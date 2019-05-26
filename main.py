import asyncio
import traceback

import websockets
import socket


async def hello(websocket, path):
    try:
        name = await websocket.recv()
        print(f"< {name}")

        greeting = f"Hello {name}!"

        await websocket.send(greeting)
        print(f"> {greeting}")
    except:
        print(traceback.format_exc())


start_server = websockets.serve(hello, str(socket.gethostbyname(socket.gethostname())), 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
