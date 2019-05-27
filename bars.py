import datetime
import gzip
import json
import uuid

import websocket

import time


def on_message(ws, message):
    result = gzip.decompress(message).decode('utf-8')
    if "ping" in result:
        ws.send(json.dumps({"pong": time.time()}))
    else:
        # todo: save data
        print(result)


def on_error(ws, error):
    print(error)


def on_close(ws):
    print("### closed ###")


def on_open(ws):
    datetime_from = datetime.datetime(2018, 1, 1, 0, 0,
                                      tzinfo=datetime.timezone(datetime.timedelta(hours=8)))
    datetime_to = datetime.datetime(2018, 1, 1, 0, 1,
                                    tzinfo=datetime.timezone(datetime.timedelta(hours=8)))

    # 300 rows max that's 5 hours of bars for 1-min interval
    req = {"req": "market.{}.kline.{}".format("eosusdt", "1min"),
           "id": str(uuid.uuid4()),
           "from": int(datetime_from.timestamp()),
           "to": int(datetime_to.timestamp())}

    ws.send(json.dumps(req))


if __name__ == "__main__":
    ws = websocket.WebSocketApp("wss://api.huobi.pro/ws",
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.on_open = on_open

    http_proxy_host = None
    http_proxy_port = None
    ws.run_forever(http_proxy_host=http_proxy_host,
                   http_proxy_port=http_proxy_port)
