import asyncio
import websockets
import socket


async def hello():
    async with websockets.connect("wss://api.huobi.pro/ws") as websocket:
            # "ws://{}:8765".format(socket.gethostbyname(socket.gethostname()))) as websocket:
        print("ok")

asyncio.get_event_loop().run_until_complete(hello())
