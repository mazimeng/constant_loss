import datetime

import HuobiClient
HuobiClient.HTTP_PROXY = ('127.0.0.1', 1080)
HuobiClient.LOCAL_TIMEZONE = datetime.timezone(offset=datetime.timedelta(hours=0))


def test_bar_data_replay():
    bar_data_replay = HuobiClient.BarDataReplay('eosusdt', datetime.date(2019, 1, 1), datetime.date(2019, 1, 2))
    bar_data_replay.request_data()
    csv_path = bar_data_replay.to_csv()
    bar_data_replay.from_csv(csv_path)


test_bar_data_replay()
