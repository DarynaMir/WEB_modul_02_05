import asyncio
import websockets
import json

async def send_command(command):
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        await websocket.send(json.dumps({'type': 'command', 'content': command}))
        response = await websocket.recv()
        print(f"Received response: {response}")

asyncio.run(send_command('exchange'))
