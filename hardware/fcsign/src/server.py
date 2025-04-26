import asyncio
import websockets
import json
import base64
import struct
import random
import string
import traceback

from commands import Commands, Responses

g_Firmware = b''

async def send_data(socket, data, cycles):
    await socket.send(json.dumps({
        'data' : base64.b64encode(data).decode('ascii'),
        'cycles' : cycles
    }))

def pack_data_packet(type_, status, data=b''):
    type_field = struct.pack('B', type_.value)
    status_field = struct.pack('B', status.value)
    packet = b''
    packet += b'\x33'
    packet += struct.pack('<H', len(data) + 2)
    packet += type_field
    packet += status_field
    packet += data
    return packet

def unpack_packet(data):
    if len(data) < 4 or (size := struct.unpack('<H', data[1:3])[0]) != len(data[3:]):
        print('Invalid command...')
        return {
            'type' : Commands.UNKNOWN,
            'status' : Responses.INVALID_COMMAND
        }

    # Check the first byte
    match data[3]:
        case Commands.COMM_INIT.value:
            print('Comm init...')
            return {
                'type' : Commands.COMM_INIT,
                'status' : Responses.ACK
            }
        case Commands.SET_CHIP_FREQ.value:
            print('Chip freq...')
            if len(data[4:]) != 4:
                return {
                    'type' : Commands.SET_CHIP_FREQ,
                    'status' : Responses.INVALID_COMMAND,
                }

            frequency = struct.unpack("<I", data[4:])[0]
            print(f'Frequency was {frequency} hz')
            if frequency != 16000000 and frequency != 8000000:
                return {
                    'type' : Commands.SET_CHIP_FREQ,
                    'status' : Responses.INVALID_FREQUENCY,
                }

            return {
                'type' : Commands.SET_CHIP_FREQ,
                'status' : Responses.ACK,
                'frequency' : frequency
            }

        case Commands.ID_AUTHENTICATION.value:
            print('ID auth...')
            if len(id_ := data[4:]) != 16:
                print('Invalid id len')
                return {
                    'type' : Commands.ID_AUTHENTICATION,
                    'status' : Responses.INVALID_ID_LEN,
                }
            print('Good Id len')
            return {
                'type' : Commands.ID_AUTHENTICATION,
                'status' : Responses.ACK,
                'id' : id_
            }

        case Commands.READ.value:
            print('Read...')
            if len((addr := data[4:])) != 4:
                return {
                    'type' : Commands.READ,
                    'status' : Responses.INVALID_ADDRESS,
                }
            
            address = struct.unpack("<I", addr)[0]
            if address >= 0xEDC00:
                return {
                    'type' : Commands.READ,
                    'status' : Responses.INVALID_ADDRESS,
                }        
            return {
                'type' : Commands.READ,
                'status' : Responses.ACK,
                'address' : address
            }
        case _:
            print('I dunno...')
            return {
                'type' : Commands.UNKNOWN,
                'status' : Responses.INVALID_COMMAND
            }
        
async def client_loop(websocket):
    # Give the user 5 seconds to send data.
    websocket.timeout = 5

    # Bind the chip guesses to be within binary search range, with some margin of error.
    chip_guesses_max = 26 * 16 + 15
    chip_guesses_current = 0
    cycles = 0

    try:
        # Parse message
        message = await websocket.recv()
        data = json.loads(message)

        # If message does not contain data, kick them out.
        if 'data' not in data.keys():
            return

        # If the data they pass in is not what we want, kick them out.
        if (actual_data := base64.b64decode(data['data'])) != b'\x55\x00\xC1\x00':
            print('Bad Data!')
            return

        # Known good.
        cycles += 25
        await send_data(websocket, pack_data_packet(Commands.UNKNOWN, Responses.ACK, b'\x50'), cycles)

        # Generate a random ID
        chip_id = ''.join(random.sample(string.ascii_uppercase, 16)).encode('ascii')
        print(f'Chip ID for this attempt is "{chip_id.decode("ascii")}"')

        # Spin up state machine.
        g_CommInit = False
        g_Frequency = -1
        g_Unlocked = False
        
        # Bump up time.
        websocket.timeout = 10

        # Parse all messages.
        async for message in websocket:
            data = json.loads(message)            
            if 'data' not in data.keys():
                continue
            
            if chip_guesses_current >= chip_guesses_max:
                print('Brute force detected!')
                return
            packet_data = base64.b64decode(data['data'])
            packet_data_unpacked = unpack_packet(packet_data)

            if packet_data_unpacked['status'] != Responses.ACK:
                print('Bad data. Packet shown below.')
                print(packet_data_unpacked)
                cycles += 10
                await send_data(websocket, pack_data_packet(packet_data_unpacked['type'], packet_data_unpacked['status']), cycles)
                return

            match packet_data_unpacked['type']:
                case Commands.COMM_INIT:
                    g_CommInit = True
                    cycles += 100 + random.randint(4, 6)
                    await send_data(websocket, pack_data_packet(packet_data_unpacked['type'], packet_data_unpacked['status']), cycles)
                case Commands.SET_CHIP_FREQ:
                    if not g_CommInit:
                        print('ChipFreq set before comm init')
                        cycles += 1
                        await send_data(websocket, pack_data_packet(packet_data_unpacked['type'], Responses.FLOW_ERROR), cycles)
                        return
                    g_Frequency = packet_data_unpacked['frequency']
                    cycles += 100
                    await send_data(websocket, pack_data_packet(packet_data_unpacked['type'], packet_data_unpacked['status']), cycles)
                
                case Commands.ID_AUTHENTICATION:
                    print('Auth attempt...')
                    if not g_CommInit or g_Frequency == -1:
                        cycles += 10
                        await send_data(websocket, pack_data_packet(packet_data_unpacked['type'], Responses.FLOW_ERROR), cycles)
                        return

                    chip_guesses_current += 1
                    skip_low = 250
                    skip_eq = 1000
                    skip_hi = 500 
                    all_bytes_match = True
                    for i, id_byte_sent in enumerate(packet_data_unpacked['id']):
                        print(f'Character {chip_id[i]}')
                        if id_byte_sent == chip_id[i]:
                            print('Match!')
                            cycles += skip_eq
                        elif id_byte_sent < chip_id[i]:
                            print('Low')
                            all_bytes_match = False
                            cycles += skip_low
                            await send_data(websocket, pack_data_packet(packet_data_unpacked['type'], Responses.UNAUTHORIZED), cycles)
                            break
                        else:
                            print('High')
                            all_bytes_match = False
                            cycles += skip_hi
                            await send_data(websocket, pack_data_packet(packet_data_unpacked['type'], Responses.UNAUTHORIZED), cycles)
                            break
                    
                    if all_bytes_match:
                        await send_data(websocket, pack_data_packet(packet_data_unpacked['type'], Responses.ACK), cycles) 
                        print('Auth success')
                        g_Unlocked = True   
                    else:
                        print('Auth fail')

                case Commands.READ:
                    print('Read attempt')
                    if not g_CommInit or g_Frequency == -1 or not g_Unlocked:
                        cycles += 10
                        await send_data(websocket, pack_data_packet(packet_data_unpacked['type'], Responses.FLOW_ERROR), cycles)
                        return

                    if (address := packet_data_unpacked['address']) % 0x400:
                        cycles += 10
                        await send_data(websocket, pack_data_packet(packet_data_unpacked['type'], Responses.INVALID_ADDRESS_ALIGNMENT), cycles)
                        return

                    cycles += 100000
                    await send_data(websocket, pack_data_packet(packet_data_unpacked['type'], Responses.ACK, g_Firmware[address : address + 0x400]), cycles)
                case _:
                    print('Invalid command')
                    await send_data(websocket, pack_data_packet(packet_data_unpacked['type'], Responses.INVALID_COMMAND), cycles)
                    return
    except Exception as e:
        print(e)
        return
        

async def main():
    global g_Firmware
    with open('firmware.bin', 'rb') as FIRMWARE:
        g_Firmware = FIRMWARE.read()

    async with websockets.serve(client_loop, "0.0.0.0", 8765):
        print('Rise and grind...')
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())