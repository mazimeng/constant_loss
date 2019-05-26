import asyncio
import gzip
import json
import time

import websockets
import socket


async def hello():
    async with websockets.connect("wss://api.huobi.pro/ws") as websocket:
        await websocket.send(json.dumps({"ping": time.time()}))

        response = await websocket.recv()
        result = gzip.decompress(response).decode('utf-8')
        print("{}".format(result))

asyncio.get_event_loop().run_until_complete(hello())
