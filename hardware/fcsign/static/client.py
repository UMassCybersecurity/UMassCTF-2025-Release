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
c
async def receive_data(socket):
    response = await socket.recv()
    message = json.loads(response)
    return base64.b64decode(message['data']), message['cycles']

async def main():
    # Example test code...
    socket = await connect('ws://ctf.umasscybersec.org:10004')

    # Here is an example on how to interact with the target.
    await send_data(socket, b'\x12\x34\x56\x78')

    # This is for receiving the data and the cycle count...
    data, cycles = await receive_data(socket)

    return 0

if __name__ == "__main__":
    asyncio.run(main())