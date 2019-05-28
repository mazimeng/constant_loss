import datetime
import re
import sys
import uuid
import warnings
from enum import Enum
from typing import Optional


class OrderType(Enum):
    Manual = -2  # type: Enum
    CancelOrder = -1  # type: Enum
    LimitOrder = 1  # type: Enum
    FOK = 2  # type: Enum
    FAK = 3  # type: Enum


class TradeSide(Enum):
    ShortOpen = -2  # type: Enum
    LongClose = -1  # type: Enum
    Cancel = 0  # type: Enum
    LongOpen = 1  # type: Enum
    ShortClose = 2  # type: Enum


class OrderState(Enum):
    Invalid = -1  # type: Enum
    Pending = 0  # type: Enum
    Placed = 1  # type: Enum
    PartFilled = 2  # type: Enum
    Filled = 3  # type: Enum
    Canceling = 4  # type: Enum
    Canceled = 5  # type: Enum


# noinspection SpellCheckingInspection
class PythonTerminalStyle(Enum):
    CEND = '\33[0m'  # type: Enum
    CBOLD = '\33[1m'  # type: Enum
    CITALIC = '\33[3m'  # type: Enum
    CURL = '\33[4m'  # type: Enum
    CBLINK = '\33[5m'  # type: Enum
    CBLINK2 = '\33[6m'  # type: Enum
    CSELECTED = '\33[7m'  # type: Enum

    CBLACK = '\33[30m'  # type: Enum
    CRED = '\33[31m'  # type: Enum
    CGREEN = '\33[32m'  # type: Enum
    CYELLOW = '\33[33m'  # type: Enum
    CBLUE = '\33[34m'  # type: Enum
    CVIOLET = '\33[35m'  # type: Enum
    CBEIGE = '\33[36m'  # type: Enum
    CWHITE = '\33[37m'  # type: Enum

    CBLACKBG = '\33[40m'  # type: Enum
    CREDBG = '\33[41m'  # type: Enum
    CGREENBG = '\33[42m'  # type: Enum
    CYELLOWBG = '\33[43m'  # type: Enum
    CBLUEBG = '\33[44m'  # type: Enum
    CVIOLETBG = '\33[45m'  # type: Enum
    CBEIGEBG = '\33[46m'  # type: Enum
    CWHITEBG = '\33[47m'  # type: Enum

    CGREY = '\33[90m'  # type: Enum
    CRED2 = '\33[91m'  # type: Enum
    CGREEN2 = '\33[92m'  # type: Enum
    CYELLOW2 = '\33[93m'  # type: Enum
    CBLUE2 = '\33[94m'  # type: Enum
    CVIOLET2 = '\33[95m'  # type: Enum
    CBEIGE2 = '\33[96m'  # type: Enum
    CWHITE2 = '\33[97m'  # type: Enum

    CGREYBG = '\33[100m'  # type: Enum
    CREDBG2 = '\33[101m'  # type: Enum
    CGREENBG2 = '\33[102m'  # type: Enum
    CYELLOWBG2 = '\33[103m'  # type: Enum
    CBLUEBG2 = '\33[104m'  # type: Enum
    CVIOLETBG2 = '\33[105m'  # type: Enum
    CBEIGEBG2 = '\33[106m'  # type: Enum
    CWHITEBG2 = '\33[107m'  # type: Enum


class TradeData:
    def __init__(
            self,
            ticker,
            trade_time,
            trade_price,
            trade_volume,
    ):
        self.ticker = ticker
        self.trade_time = trade_time
        self.price = trade_price
        self.volume = trade_volume
        self.side = None


class BarData:
    def __init__(
            self,
            ticker,  # type: str
            high_price,  # type: float
            low_price,  # type: float
            open_price,  # type: float
            close_price,  # type: float
            bar_start_time,  # type: datetime.datetime
            bar_span,  # type: datetime.timedelta
            volume,  # type: float
            notional  # type: float
    ):
        self.ticker = ticker
        self.high_price = high_price
        self.low_price = low_price
        self.open_price = open_price
        self.close_price = close_price
        self.bar_start_time = bar_start_time  # type: datetime.datetime
        self.bar_span = bar_span
        self.volume = volume
        self.notional = notional


class TickData:
    def __init__(
            self,
            ticker,  # type: str
            last_price,  # type: float
            bid_price,  # type: float
            ask_price,  # type: float
            bid_amount,  # type: int
            ask_amount,  # type: int
            total_volume,  # type: float
            total_notional,  # type: float
            time  # type: datetime.datetime

    ):
        """
        store tick data
        :param ticker: name of the underlying
        :param last_price: float
        :param bid_price: float
        :param ask_price: float
        :param bid_amount: int
        :param ask_amount: int
        :param total_volume: int
        :param time: datetime.datetime
        :param total_notional: float, equals total turnover
        """
        self.ticker = ticker
        self.last_price = last_price
        self.bid_price = bid_price
        self.ask_price = ask_price
        self.bid_amount = bid_amount
        self.ask_amount = ask_amount
        self.total_volume = total_volume
        self.total_notional = total_notional
        self.time = time


class Instruction:

    def __init__(
            self,
            ticker,  # type: str
            side,  # type: TradeSide
            order_type,  # type: OrderType
            amount=0,  # type: int
            limit_price=0.0,  # type: float
            order_id=None,  # type: Optional[str]
            note=''  # type: str
    ):
        if type(amount) is not int:
            warnings.warn('Amount is not integer.')

        if amount <= 0:
            warnings.warn('Invalid trade amount!')

        if type(side) is not TradeSide:
            warnings.warn('Invalid trade side!')

        self.__ticker = ticker
        self.__side = side
        self.__type = order_type
        self.__amount = int(amount)
        self.__limit_price = limit_price
        self.__order_id = order_id if order_id is not None else str(uuid.uuid1())
        self.__note = note

        self.__state = OrderState.Pending  # type: OrderState
        self.__filled_amount = 0  # type: int
        self.__filled_notional = 0.0  # type: float
        self.__stop_datetime = None  # type: Optional[datetime.datetime]
        self.__start_datetime = datetime.datetime.now()  # type: Optional[datetime.datetime]
        self.__estimated_margin_cost = 0.0  # type: float
        self.__average_price = 0.0  # type: float

    def filled(
            self,
            amount,  # type: int
            notional,  # type: float
            filled_datetime  # type: datetime.datetime
    ):
        if amount != 0:
            self.__filled_amount += abs(amount)
            self.__filled_notional += abs(notional)

        if self.__filled_amount == self.__amount:
            self.__state = OrderState.Filled  # type: OrderState
            self.__stop_datetime = filled_datetime
        elif self.__filled_amount > 0:
            self.__state = OrderState.PartFilled  # type: OrderState

        if self.__filled_amount != 0:
            self.__average_price = self.__filled_notional / self.__filled_amount
        else:
            self.__average_price = float('NaN')

    def canceling(self, canceling_date_time):
        self.__state = OrderState.Canceling

        cancel_instruction = Instruction(
            ticker=self.__ticker,
            side=TradeSide.Cancel,
            order_type=OrderType.CancelOrder,
            order_id=self.__order_id,
            note=self.__note
        )

        return cancel_instruction

    def canceled(self, canceled_datetime):
        # type: (datetime.datetime) -> None
        self.__state = OrderState.Canceled  # type: OrderState
        self.__stop_datetime = canceled_datetime

    def set_estimated_margin(self, margin):
        self.__estimated_margin_cost = margin

    # noinspection PyPep8Naming
    @property
    def OrderID(self):
        # type: () -> str
        return self.__order_id

    # noinspection PyPep8Naming
    @property
    def Ticker(self):
        # type: () -> str
        return self.__ticker

    # noinspection PyPep8Naming
    @property
    def Side(self):
        # type: () -> TradeSide
        return self.__side

    # noinspection PyPep8Naming
    @property
    def Type(self):
        # type: () -> OrderType
        return self.__type

    # noinspection PyPep8Naming
    @property
    def Amount(self):
        # type: () -> int
        return self.__amount

    # noinspection PyPep8Naming
    @property
    def LimitPrice(self):
        # type: () -> float
        return self.__limit_price

    # noinspection PyPep8Naming
    @property
    def StartTime(self):
        # type: () -> datetime.datetime
        return self.__start_datetime

    # noinspection PyPep8Naming
    @property
    def Note(self):
        # type: () -> str
        return self.__note

    # noinspection PyPep8Naming
    @property
    def State(self):
        # type: () -> OrderState
        return self.__state

    # noinspection PyPep8Naming
    @property
    def FilledAmount(self):
        # type: () -> int
        return self.__filled_amount

    # noinspection PyPep8Naming
    @property
    def FilledNotional(self):
        # type: () -> float
        return self.__filled_notional

    # noinspection PyPep8Naming
    @property
    def AveragePrice(self):
        # type: () -> float
        return self.__average_price

    # noinspection PyPep8Naming
    @property
    def StopTime(self):
        # type: () -> datetime
        return self.__stop_datetime

    # noinspection PyPep8Naming
    @property
    def Margin(self):
        # type: () -> float
        return self.__estimated_margin_cost


class Report:

    def __init__(
            self,
            ticker,  # type: str
            side,  # type: TradeSide
            amount,  # type: int
            notional,  # type: float
            trade_time,  # type: datetime.datetime
            order_id,  # type: str
            note  # type: str
    ):

        self.__ticker = ticker
        self.__side = side
        self.__amount = amount
        self.__notional = notional
        self.__trade_time = trade_time
        self.__order_id = order_id
        self.__note = note

        self.__margin = None

    def set_margin(self, margin):
        # type: (float) -> None
        self.__margin = margin

    # noinspection PyPep8Naming
    @property
    def Ticker(self):
        # type: () -> str
        return self.__ticker

    # noinspection PyPep8Naming
    @property
    def Side(self):
        # type: () -> TradeSide
        return self.__side

    # noinspection PyPep8Naming
    @property
    def Amount(self):
        # type: () -> int
        return self.__amount

    # noinspection PyPep8Naming
    @property
    def Notional(self):
        # type: () -> float
        return self.__notional

    # noinspection PyPep8Naming
    @property
    def TradeTime(self):
        # type: () -> datetime.datetime
        return self.__trade_time

    # noinspection PyPep8Naming
    @property
    def OrderID(self):
        # type: () -> str
        return self.__order_id

    # noinspection PyPep8Naming
    @property
    def Note(self):
        # type: () -> str
        return self.__note

    # noinspection PyPep8Naming
    @property
    def Margin(self):
        # type: () -> float
        return self.__margin


class ProgressBar(object):

    DEFAULT = 'Progress: %(bar)s %(percent)3d%%'
    FULL = '%(bar)s %(current)d/%(total)d (%(percent)3d%%) %(remaining)d to go'

    def __init__(self, total, width=40, fmt=DEFAULT, symbol='=',
                 output=sys.stderr):
        assert len(symbol) == 1

        self.total = total
        self.width = width
        self.symbol = symbol
        self.output = output
        self.fmt = re.sub(r'(?P<name>%\(.+?\))d', r'\g<name>%dd' % len(str(total)), fmt)

        self.current = 0

    def __call__(self):
        percent = self.current / float(self.total)
        size = int(self.width * percent)
        remaining = self.total - self.current
        bar = '[' + self.symbol * size + ' ' * (self.width - size) + ']'

        args = {
            'total': self.total,
            'bar': bar,
            'current': self.current,
            'percent': percent * 100,
            'remaining': remaining
        }
        print('\r' + self.fmt % args)

    def done(self):
        self.current = self.total
        self()
        print('')
