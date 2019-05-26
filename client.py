import asyncio
import json
import time

import websockets
import socket


async def hello():
    async with websockets.connect("wss://api.huobi.pro/ws") as websocket:
        await websocket.send(json.dumps({"ping": time.time()}))

        response = await websocket.recv()
        print("{}".format(response.decode()))

asyncio.get_event_loop().run_until_complete(hello())
