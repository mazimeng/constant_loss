import asyncio
import gzip
import json
import time
import uuid

import websockets
import socket


# def req(ws):
#     await ws.send(json.dumps({
#         "req": "market.{}.kline.{}".format("btcusdt", "1min"),
#         "id": str(uuid.uuid4())}))
#
#     response = await ws.recv()
#     result = gzip.decompress(response).decode('utf-8')
#     print("{}".format(result))


async def hello():
    async with websockets.connect("wss://api.huobi.pro/ws") as ws:
        await ws.send(json.dumps({
            "req": "market.{}.kline.{}".format("btcusdt", "1min"),
            "id": str(uuid.uuid4())}))

        response = await ws.recv()
        result = gzip.decompress(response).decode('utf-8')
        print("{}".format(result))


asyncio.get_event_loop().run_until_complete(hello())
