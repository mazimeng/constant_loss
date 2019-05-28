import datetime
import gzip
import uuid
import threading
import functools
import json
import os
from typing import Dict

import websocket

from DataStructure import BarData, ProgressBar

HTTP_PROXY = (None, None)  # ('127.0.0.1', 1080) or (None, None)
LOCAL_TIMEZONE = None


def main():
    pass


class BarDataReplay(object):
    def __init__(self, ticker, start_date, end_date):
        # type: (str, datetime.date, datetime.date) -> None

        self.ticker = ticker
        self.start_date = start_date
        self.end_date = end_date

        self.connected = False
        self._requests_status = {}
        self.bar_data_storage = {}  # type: Dict[datetime.datetime, BarData]
        # websocket.enableTrace(True)
        self.socket = websocket.WebSocketApp(
            url="wss://api.huobi.pro/ws",
            on_open=functools.partial(self._on_open, self),
            on_message=functools.partial(self._on_message, self),
            on_error=self._on_error,
            on_close=functools.partial(self._on_close, self)
        )

        self.socket_thread = threading.Thread(target=self._socket_thread, args=[HTTP_PROXY])

    def _socket_thread(self, proxy):

        if proxy != (None, None):
            print('Using proxy ' + proxy[0] + ': ' + str(proxy[1]))

        self.socket.run_forever(
            http_proxy_host=proxy[0],
            http_proxy_port=proxy[1]
        )

    @staticmethod
    def _on_open(self, socket):
        self.connected = socket.sock.connected

    @staticmethod
    def _on_close(self, socket):
        print(socket.connected)
        self.connected = socket.sock.connected

    @staticmethod
    def _on_message(self, socket, message):
        result = gzip.decompress(message).decode('utf-8')
        if "ping" in result:
            socket.send(json.dumps({"pong": datetime.datetime.now().timestamp()}))
        else:
            self._log_bar_data(result)

    @staticmethod
    def _on_error(socket, error):
        print(error)
        socket.close()

    def _log_bar_data(self, message):
        result = json.loads(message)

        assert result['status'] == 'ok', 'bad message'

        for tick_dict in result['data']:
            bar_data = BarData(
                ticker=self.ticker,
                high_price=tick_dict['high'],
                low_price=tick_dict['low'],
                open_price=tick_dict['open'],
                close_price=tick_dict['close'],
                bar_start_time=datetime.datetime.utcfromtimestamp(tick_dict['id']),
                bar_span=datetime.timedelta(minutes=1),
                volume=tick_dict['amount'],
                notional=tick_dict['vol']
            )

            self.bar_data_storage[bar_data.bar_start_time] = bar_data

        self._requests_status[result['id']] = 'Processed'

    def request_data(self, request_size=300, queue_size=5):
        # type: (int, int) -> None

        print('Requesting data from ' + self.socket.url)
        self.socket_thread.start()

        pgb = ProgressBar(total=((self.end_date - self.start_date) + datetime.timedelta(days=1)).total_seconds() / 60)

        def update_pgb():
            while True:
                progress = len(self.bar_data_storage)
                if pgb.current != progress:
                    pgb.current = progress
                    pgb()

                if pgb.current == pgb.total:
                    break

        while True:
            if self.connected:
                break

        # 300 rows max that's 5 hours of bars for 1-min interval
        start_datetime = datetime.datetime.combine(self.start_date, time=datetime.time(), tzinfo=LOCAL_TIMEZONE)
        end_datetime = start_datetime + datetime.timedelta(minutes=request_size)
        pgb_thread = threading.Thread(target=update_pgb)
        pgb_thread.start()
        while True:
            req = {
                "req": "market.{}.kline.{}".format(self.ticker, "1min"),
                "id": str(uuid.uuid1()),
                "from": int(start_datetime.timestamp()),
                "to": int(end_datetime.timestamp())
            }

            self.socket.send(json.dumps(req))
            self._requests_status[req['id']] = 'Sent'

            while True:
                pending_count = sum([1 if status == 'Sent' else 0 for status in self._requests_status.values()])
                if queue_size > pending_count:
                    break

            start_datetime = end_datetime
            end_datetime = start_datetime + datetime.timedelta(minutes=request_size)

            if start_datetime >= datetime.datetime.combine(self.end_date + datetime.timedelta(days=1), datetime.time(), tzinfo=LOCAL_TIMEZONE):
                break
            elif end_datetime > datetime.datetime.combine(self.end_date + datetime.timedelta(days=1), datetime.time(), tzinfo=LOCAL_TIMEZONE):
                end_datetime = datetime.datetime.combine(self.end_date + datetime.timedelta(days=1), datetime.time(), tzinfo=LOCAL_TIMEZONE)

        while True:
            processed_count = sum([1 if status == 'Processed' else 0 for status in self._requests_status.values()])
            if processed_count == len(self._requests_status):
                break

        pgb.done()

        self.socket.close()
        print(str(len(self.bar_data_storage)) + ' bar data received and processed, completed!')

    def to_csv(self, file_path=None):

        if file_path is None:
            file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.ticker + '_' + self.start_date.strftime('%Y%m%d') + '_' + self.end_date.strftime('%Y%m%d') + '.csv')

        if self.bar_data_storage:
            print('Dumping data to csv file at ' + file_path)
            import pandas as pd

            bar_data_df = pd.DataFrame()
            i = 0
            pgb = ProgressBar(total=len(self.bar_data_storage))
            key_list = sorted(self.bar_data_storage.keys())

            while i < len(key_list):
                trade_datetime = key_list[i]
                bar_data_df.at[trade_datetime, 'Ticker'] = self.bar_data_storage[trade_datetime].ticker
                bar_data_df.at[trade_datetime, 'High'] = self.bar_data_storage[trade_datetime].high_price
                bar_data_df.at[trade_datetime, 'Low'] = self.bar_data_storage[trade_datetime].low_price
                bar_data_df.at[trade_datetime, 'Open'] = self.bar_data_storage[trade_datetime].open_price
                bar_data_df.at[trade_datetime, 'Close'] = self.bar_data_storage[trade_datetime].close_price
                bar_data_df.at[trade_datetime, 'Volume'] = self.bar_data_storage[trade_datetime].volume
                bar_data_df.at[trade_datetime, 'Notional'] = self.bar_data_storage[trade_datetime].notional
                pgb.current = i
                pgb()
                i += 1

            pgb.done()
            bar_data_df.sort_index(inplace=True)
            bar_data_df.to_csv(file_path, index_label='Time', index=True)

        return file_path

    def from_csv(self, file_path):
        if file_path is None:
            file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.ticker + '_' + self.start_date.strftime('%Y%m%d') + '_' + self.end_date.strftime('%Y%m%d') + '.csv')

        print('Loading data from csv file at ' + file_path)

        import pandas as pd
        bar_data_df = pd.read_csv(file_path, index_col=0)
        bar_data_df.index = pd.to_datetime(bar_data_df.index)
        pgb = ProgressBar(total=len(bar_data_df))

        i = 0
        while i < len(bar_data_df):
            trade_datetime = bar_data_df.index[i].to_pydatetime()

            bar_data = BarData(
                ticker=bar_data_df.at[trade_datetime, 'Ticker'],
                high_price=bar_data_df.at[trade_datetime, 'High'],
                low_price=bar_data_df.at[trade_datetime, 'Low'],
                open_price=bar_data_df.at[trade_datetime, 'Open'],
                close_price=bar_data_df.at[trade_datetime, 'Close'],
                bar_start_time=trade_datetime,
                bar_span=datetime.timedelta(minutes=1),
                volume=bar_data_df.at[trade_datetime, 'Volume'],
                notional=bar_data_df.at[trade_datetime, 'Notional']
            )

            self.bar_data_storage[bar_data.bar_start_time] = bar_data

            pgb.current = i
            pgb()
            i += 1

        pgb.done()


if __name__ == "__main__":
    main()
