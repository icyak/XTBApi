# -*- coding utf-8 -*-

"""
XTBApi.api
~~~~~~~

Main module
"""

import enum
import json
import logging
import time
from datetime import datetime
from websocket import create_connection
from websocket._exceptions import WebSocketConnectionClosedException

import XTBApi.exceptions


logger = logging.getLogger()
LOGIN_TIMEOUT = 120
MAX_TIME_INTERVAL = 0.200


class STATUS(enum.Enum):
    LOGGED = enum.auto()
    NOT_LOGGED = enum.auto()


class MODES(enum.Enum):
    BUY = 0
    SELL = 1
    BUY_LIMIT = 2
    SELL_LIMIT = 3
    BUY_STOP = 4
    SELL_STOP = 5
    BALANCE = 6
    CREDIT = 7


class TRANS_TYPES(enum.Enum):
    OPEN = 0
    PENDING = 1
    CLOSE = 2
    MODIFY = 3
    DELETE = 4


class PERIOD(enum.Enum):
    ONE_MINUTE = 1
    FIVE_MINUTES = 5
    FIFTEEN_MINUTES = 15
    THIRTY_MINUTES = 30
    ONE_HOUR = 60
    FOUR_HOURS = 240
    ONE_DAY = 1440
    ONE_WEEK = 10080
    ONE_MONTH = 43200


def _get_data(command, **parameters):
    data = {
        "command": command,
    }
    if parameters:
        data['arguments'] = {}
        for (key, value) in parameters.items():
            data['arguments'][key] = value
    return data


def _check_mode(mode):
    """check if mode acceptable"""
    modes = [x.value for x in MODES]
    if mode not in modes:
        raise ValueError("mode must be in: ",mode)


def _check_period(period):
    """check if period is acceptable"""
    if period not in [x.value for x in PERIOD]:
        raise ValueError("Period:", period, "not acceptable")


def _check_volume(volume):
    """normalize volume"""
    if not isinstance(volume, float):
        try:
            return float(volume)
        except Exception as exc:
            raise ValueError('vol must be float') from exc
    else:
        return volume


class BaseClient(object):
    """main client class"""

    def __init__(self):
        self.ws = None
        self._login_data = None
        self._time_last_request = time.time() - MAX_TIME_INTERVAL
        self.status = STATUS.NOT_LOGGED
        logger.debug("BaseClient inited")
        self.logger = logging.getLogger('XTBApi.api.BaseClient')

    def _login_decorator(self, func, *args, **kwargs):
        if self.status == STATUS.NOT_LOGGED:
            raise XTBApi.exceptions.NotLogged()
        try:
            return func(*args, **kwargs)
        except XTBApi.exceptions.SocketError:
            logger.info("re-logging in due to LOGIN_TIMEOUT gone")
            self.login(self._login_data[0], self._login_data[1])
            return func(*args, **kwargs)
        except Exception as exc:
            logger.warning(exc)
            self.login(self._login_data[0], self._login_data[1])
            return func(*args, **kwargs)

    def _send_command(self, dict_data):
        """send command to api"""
        time_interval = time.time() - self._time_last_request
        self.logger.debug("took %s s.", time_interval)
        if time_interval < MAX_TIME_INTERVAL:
            time.sleep(MAX_TIME_INTERVAL - time_interval)
        try:
            self.ws.send(json.dumps(dict_data))
            response = self.ws.recv()
        except WebSocketConnectionClosedException as exc:
            raise XTBApi.exceptions.SocketError() from exc

        self._time_last_request = time.time()
        res = json.loads(response)
        if res['status'] is False:
            raise XTBApi.exceptions.CommandFailed(res)
        if 'returnData' in res.keys():
            self.logger.info("CMD: done")
            self.logger.debug(res['returnData'])
            return res['returnData']

    def _send_command_with_check(self, dict_data):
        """with check login"""
        return self._login_decorator(self._send_command, dict_data)

    def login(self, user_id, password, mode='demo'):
        """login command"""
        data = _get_data("login", userId=user_id, password=password)
        self.ws = create_connection(f"wss://ws.xtb.com/{mode}")
        response = self._send_command(data)
        self._login_data = (user_id, password)
        self.status = STATUS.LOGGED
        self.logger.info("CMD: login...")
        return response

    def logout(self):
        """logout command"""
        data = _get_data("logout")
        response = self._send_command(data)
        self.status = STATUS.LOGGED
        self.logger.info("CMD: logout...")
        return response

    def get_all_symbols(self):
        """getAllSymbols command"""
        data = _get_data("getAllSymbols")
        self.logger.info("CMD: get all symbols...")
        return self._send_command_with_check(data)

    def get_calendar(self):
        """getCalendar command"""
        data = _get_data("getCalendar")
        self.logger.info("CMD: get calendar...")
        return self._send_command_with_check(data)

    def get_chart_last_request(self, symbol, period, start):
        """getChartLastRequest command"""
        _check_period(period)
        args = {
            "period": period,
            "start": start * 1000,
            "symbol": symbol
        }
        data = _get_data("getChartLastRequest", info=args)
        self.logger.info("CMD: get chart last request for %s of period %s from %s ...",
                         symbol, period, start)
        return self._send_command_with_check(data)

    def get_chart_range_request(self, symbol, period, start, end, ticks):
        """getChartRangeRequest command"""
        if not isinstance(ticks, int):
            raise ValueError(f"ticks value {ticks} must be int")
        args = {
            "end": end * 1000,
            "period": period,
            "start": start * 1000,
            "symbol": symbol,
            "ticks": ticks
        }
        data = _get_data("getChartRangeRequest", info=args)
        self.logger.info("CMD: get chart range request for %s of %s from %s to %s with ticks of %s",
                         symbol, period, start, end, ticks)
        return self._send_command_with_check(data)

    def get_commission(self, symbol, volume):
        """getCommissionDef command"""
        volume = _check_volume(volume)
        data = _get_data("getCommissionDef", symbol=symbol, volume=volume)
        self.logger.info("CMD: get commission for %s of %i...", symbol, volume)
        return self._send_command_with_check(data)

    def get_margin_level(self):
        """getMarginLevel command
        get margin information"""
        data = _get_data("getMarginLevel")
        self.logger.info("CMD: get margin level...")
        return self._send_command_with_check(data)

    def get_margin_trade(self, symbol, volume):
        """getMarginTrade command
        get expected margin for volumes used symbol"""
        volume = _check_volume(volume)
        data = _get_data("getMarginTrade", symbol=symbol, volume=volume)
        self.logger.info("CMD: get margin trade for %s of %i...", symbol, volume)
        return self._send_command_with_check(data)

    def get_profit_calculation(self, symbol, mode, volume, op_price, cl_price):
        """getProfitCalculation command
        get profit calculation for symbol with vol, mode and op, cl prices"""
        _check_mode(mode)
        volume = _check_volume(volume)
        data = _get_data("getProfitCalculation", closePrice=cl_price,
                         cmd=mode, openPrice=op_price, symbol=symbol,
                         volume=volume)
        self.logger.info("CMD: get profit calculation for %s of %i from %f to %f in mode  %s...",
                         symbol, volume, op_price, cl_price, mode)
        return self._send_command_with_check(data)

    def get_server_time(self):
        """getServerTime command"""
        data = _get_data("getServerTime")
        self.logger.info("CMD: get server time...")
        return self._send_command_with_check(data)

    def get_symbol(self, symbol):
        """getSymbol command"""
        data = _get_data("getSymbol", symbol=symbol)
        self.logger.info("CMD: get symbol %s...", symbol)
        return self._send_command_with_check(data)

    def get_tick_prices(self, symbols, start, level=0):
        """getTickPrices command"""
        data = _get_data("getTickPrices", level=level, symbols=symbols,
                         timestamp=start)
        self.logger.info("CMD: get tick prices of %s from %s with level %s...",
                         symbols, start, level )
        return self._send_command_with_check(data)

    def get_trade_records(self, trade_position_list):
        """getTradeRecords command
        takes a list of position id"""
        data = _get_data("getTradeRecords", orders=trade_position_list)
        self.logger.info("CMD: get trade records of length: %i", len(trade_position_list))
        return self._send_command_with_check(data)

    def get_trades(self, opened_only=True):
        """getTrades command"""
        data = _get_data("getTrades", openedOnly=opened_only)
        self.logger.info("CMD: get trades...")
        return self._send_command_with_check(data)

    def get_trades_history(self, start, end):
        """getTradesHistory command
        can take 0 as actual time"""
        data = _get_data("getTradesHistory", end=end, start=start)
        self.logger.info("CMD: get trades history from %s to %s...", start, end)
        return self._send_command_with_check(data)

    def get_trading_hours(self, trade_position_list):
        """getTradingHours command"""
        data = _get_data("getTradingHours", symbols=trade_position_list)
        self.logger.info("CMD: get trading hours of lenght: %i", len(trade_position_list))
        response = self._send_command_with_check(data)
        for symbol in response:
            for day in symbol['trading']:
                day['fromT'] = int(day['fromT'] / 1000)
                day['toT'] = int(day['toT'] / 1000)
            for day in symbol['quotes']:
                day['fromT'] = int(day['fromT'] / 1000)
                day['toT'] = int(day['toT'] / 1000)
        return response

    def get_version(self):
        """getVersion command"""
        data = _get_data("getVersion")
        self.logger.info("CMD: get version...")
        return self._send_command_with_check(data)

    def ping(self):
        """ping command"""
        data = _get_data("ping")
        self.logger.info("CMD: get ping...")
        self._send_command_with_check(data)

    def trade_transaction(self, symbol, mode, trans_type, volume, **kwargs):
        """tradeTransaction command"""
        # check type
        if trans_type not in [x.value for x in TRANS_TYPES]:
            raise ValueError(f"Type must be in {[x for x in trans_type]}")
        # check kwargs
        accepted_values = ['order', 'price', 'expiration', 'customComment',
                           'offset', 'sl', 'tp']
        assert all([val in accepted_values for val in kwargs.keys()])
        _check_mode(mode)  # check if mode is acceptable
        volume = _check_volume(volume)  # check if volume is valid
        info = {
            'cmd': mode,
            'symbol': symbol,
            'type': trans_type,
            'volume': volume
        }
        info.update(kwargs)  # update with kwargs parameters
        data = _get_data("tradeTransaction", tradeTransInfo=info)
        name_of_mode = [x.name for x in MODES if x.value == mode][0]
        name_of_type = [x.name for x in TRANS_TYPES if x.value ==
                        trans_type][0]
        self.logger.info("CMD: trade transaction of %s of mode %s with type %s of %i",
                         symbol, name_of_mode, name_of_type, volume)
        return self._send_command_with_check(data)

    def trade_transaction_status(self, order_id):
        """tradeTransactionStatus command"""
        data = _get_data("tradeTransactionStatus", order=order_id)
        self.logger.info("CMD: trade transaction status for %s", order_id)
        return self._send_command_with_check(data)

    def get_user_data(self):
        """getCurrentUserData command"""
        data = _get_data("getCurrentUserData")
        self.logger.info("CMD: get user data...")
        return self._send_command_with_check(data)


class Transaction(object):
    """class for transaction"""
    def __init__(self, trans_dict):
        self._trans_dict = trans_dict
        self.mode = {0: 'buy', 1: 'sell', 2: 'buy_limit', 3: 'sell_limit'}[trans_dict['cmd']]
        self.order_id = trans_dict['order']
        self.symbol = trans_dict['symbol']
        self.volume = trans_dict['volume']
        self.price = trans_dict['close_price']
        self.actual_profit = trans_dict['profit']
        self.timestamp = trans_dict['open_time'] / 1000
        logger.debug("Transaction %s inited", self.order_id)


class Client(BaseClient):
    """advanced class of client"""
    def __init__(self):
        super().__init__()
        self.trade_rec = {}
        self.logger = logging.getLogger('XTBApi.api.Client')
        self.logger.info("Client inited")

    def check_if_market_open(self, list_of_symbols):
        """check if market is open for symbol in symbols"""
        _td = datetime.today()
        actual_tmsp = _td.hour * 3600 + _td.minute * 60 + _td.second
        response = self.get_trading_hours(list_of_symbols)
        market_values = {}
        for symbol in response:
            today_values = [day for day in symbol['trading'] if day['day'] ==
                _td.isoweekday()][0]
            if today_values['fromT'] <= actual_tmsp <= today_values['toT']:
                market_values[symbol['symbol']] = True
            else:
                market_values[symbol['symbol']] = False
        return market_values

    def get_lastn_candle_history(self, symbol, timeframe_in_seconds, number):
        """get last n candles of timeframe"""
        acc_tmf = [60, 300, 900, 1800, 3600, 14400, 86400, 604800, 2592000]
        if timeframe_in_seconds not in acc_tmf:
            raise ValueError(f"timeframe not accepted, not in "
                             f"{', '.join([str(x) for x in acc_tmf])}")
        sec_prior = timeframe_in_seconds * number
        logger.debug("sym: %s, tmf: %s,%f",symbol, timeframe_in_seconds, time.time() - sec_prior)
        res = {'rateInfos': []}
        while len(res['rateInfos']) < number:
            res = self.get_chart_last_request(symbol,
                timeframe_in_seconds // 60, time.time() - sec_prior)
            logger.debug(res)
            res['rateInfos'] = res['rateInfos'][-number:]
            sec_prior *= 3
        candle_history = []
        for candle in res['rateInfos']:
            _pr = candle['open']
            op_pr = _pr / 10 ** res['digits']
            cl_pr = (_pr + candle['close']) / 10 ** res['digits']
            hg_pr = (_pr + candle['high']) / 10 ** res['digits']
            lw_pr = (_pr + candle['low']) / 10 ** res['digits']
            new_candle_entry = {'timestamp': candle['ctm'] / 1000, 'open':
                op_pr, 'close': cl_pr, 'high': hg_pr, 'low': lw_pr,
                                'volume': candle['vol']}
            candle_history.append(new_candle_entry)
        logger.debug(candle_history)
        return candle_history

    def update_trades(self):
        """update trade list"""
        trades = self.get_trades()
        self.trade_rec.clear()
        for trade in trades:
            obj_trans = Transaction(trade)
            self.trade_rec[obj_trans.order_id] = obj_trans
        #values_to_del = [key for key, trad_not_listed in
        #                 self.trade_rec.items() if trad_not_listed.order_id
        #                 not in [x['order'] for x in trades]]
        #for key in values_to_del:
        #    del self.trade_rec[key]
        self.logger.info("updated %i trades", len(self.trade_rec))
        return self.trade_rec

    def get_trade_profit(self, trans_id):
        """get profit of trade"""
        self.update_trades()
        profit = self.trade_rec[trans_id].actual_profit
        self.logger.info("got trade profit of %s", profit)
        return profit

    def open_trade(self, mode, symbol, volume =0, dollars=0, custom_message ="",
                   tp_per = 0.00, sl_per= 0.00, type_of_instrument ="", order_margin_per = 0, expiration_stamp = 0):
        """open trade transaction"""
        self.logger.debug("dollars = %s", dollars)
        if mode in [MODES.BUY.value, MODES.SELL.value]:
            mode = [x for x in MODES if x.value == mode][0]
        elif mode in ['buy', 'sell']:
            modes = {'buy': MODES.BUY, 'sell': MODES.SELL}
            mode = modes[mode]
        else:
            raise ValueError("mode can be buy or sell")
        if type_of_instrument == "stc":
            symbol = symbol + "_9"
        elif type_of_instrument == "cfd":
            symbol = symbol + "_4"
        price, price_2 = self.get_prices_operate(mode, symbol)
        if order_margin_per != 0:
            # https://www.xtb.com/int/education/xstation-5-pending-orders
            mode, mode_name = self.change_to_order_type_mode(mode.name)
        else:
            mode_name = mode.name
            mode = mode.value
        self.logger.debug("opening trade of %s of Dollars: %i with %s Expiration: %s",
                          symbol, dollars, mode_name, datetime.fromtimestamp(expiration_stamp/1000))
        price = round(price * (1 + order_margin_per) , 2)
        if dollars != 0:
            round_value = 0
            if len(str(int(price))) >= 4:
                round_value = 2
            volume = round((dollars / price) , round_value)
        lot_step = self.get_symbol(symbol)['lotStep']
        if lot_step == 0.01:
            volume = round(volume, 2)
        elif lot_step == 0.1:
            volume = round(volume, 1)
        elif lot_step == 1.0:
            volume = round(volume, 0)
        elif lot_step == 10.0:
            volume = round(volume, -1)
        elif lot_step == 100.0:
            volume = round(volume, -2)
        sl, tp = self.get_tp_sl(mode, price, sl_per, tp_per)
        if tp_per == 0 and sl_per == 0:
            response = self.trade_transaction(symbol, mode, trans_type = 0,volume = volume,
                                              price=price, customComment=custom_message, expiration = expiration_stamp) #open trade without SL/TP
            status, status_messg = self.manage_response(expiration_stamp, response)
        else:
            response = self.trade_transaction(symbol, mode, trans_type = 0,volume = volume,
                                              price=price, customComment=custom_message, tp=tp, sl=sl,expiration = expiration_stamp) #open trade with SL/TP
            status, status_messg = self.manage_response(expiration_stamp, response)
        if status_messg == 'Invalid prices(limit)':
            self.logger.debug("FAIL. opening trade of %s Message: %s Stock: %s", symbol, status_messg, symbol)
            response = self.trade_transaction(symbol, mode, trans_type=0, volume=volume,
                                              price=price_2,customComment=custom_message, expiration=expiration_stamp)
            status, status_messg = self.manage_response(expiration_stamp, response)
            price = price_2
        if status_messg == 'Invalid s/l or t/p price':
            sl, tp = self.get_tp_sl(mode, price, sl_per+ 0.012, tp_per+ 0.012)
            self.logger.debug("FAIL. opening trade of %s Message: %s Stock: %s", symbol, status_messg, symbol)
            response = self.trade_transaction(symbol, mode, trans_type=0, volume=volume,
                                              price=price,customComment=custom_message, expiration=expiration_stamp)
            status, status_messg = self.manage_response(expiration_stamp, response)
        if status_messg == 'SL/TP order not supported' or status_messg == 'Short selling not available':
            self.logger.debug("FAIL. opening trade of %s Message: %s Stock: %s", symbol, status_messg, symbol)
            return response
        if status_messg == 'Invalid nominal': #if you want to trade something that needs multiple different than 0.01, 0.1, 1.0 or 10.0
            self.logger.debug("FAIL. opening trade of %s Message: %s Stock: %s", symbol, status_messg, symbol)
            response = self.trade_transaction(symbol, mode, trans_type=0, volume=volume,
                                              price=price,customComment=custom_message, expiration=expiration_stamp)
            status, status_messg = self.manage_response(expiration_stamp, response)
        if status_messg == 'Market closed':
            self.logger.debug("FAIL. opening trade of %s Message: %s Stock: %s", symbol, status_messg, symbol)
            response = self.trade_transaction(symbol, mode, trans_type=0, volume=volume,
                                              price=price,customComment=custom_message, expiration=expiration_stamp)
            status, status_messg = self.manage_response(expiration_stamp, response)
        if status != 3:
            self.logger.debug("FAIL. opening trade of %s Message: %s Stock: %s of Dollars %i with volume %i with Expiration: %s",
                              symbol, status_messg, symbol, dollars, volume, datetime.fromtimestamp(expiration_stamp / 1000))
        else:
            self.logger.debug("Successfully. opening trade of %s of Dollars: %i with Expiration: %s",
                              symbol, dollars, datetime.fromtimestamp(expiration_stamp/1000))
        return response

    def get_tp_sl(self, mode, price, sl_per, tp_per):
        self: self@Client
        if mode == MODES.BUY.value or mode == MODES.BUY_LIMIT.value:
            tp = round(price * (1 + tp_per), 2)
            sl = round(price * (1 - sl_per), 2)
        elif mode == MODES.SELL.value or mode == MODES.SELL_LIMIT.value:
            sl = round(price * (1 + sl_per), 2)
            tp = round(price * (1 - tp_per), 2)
        return sl, tp

    def get_prices_operate(self, mode, symbol):
        conversion_mode = {MODES.BUY.value: 'ask', MODES.SELL.value: 'bid'}
        symbol_info = self.get_symbol(symbol)
        price = symbol_info[conversion_mode[mode.value]]
        conversion_mode_2 = {MODES.BUY.value: 'low', MODES.SELL.value: 'high'}
        price_2 = symbol_info[conversion_mode_2[mode.value]]
        factor_price_2 = 0.008
        if mode in (MODES.BUY,MODES.BUY_LIMIT):
            price_2 = round(price_2 * (1 - factor_price_2), 2)
        elif mode in(MODES.SELL,MODES.SELL_LIMIT):
            price_2 = round(price_2 * (1 + factor_price_2), 2)

        return price, price_2

    def manage_response(self, expiration_stamp, response):
        self.update_trades()
        status_rep = self.trade_transaction_status(response['order'])
        status = status_rep['requestStatus']
        status_messg = status_rep['message']
        self.logger.debug("open_trade completed with status of %s Message: %s Expiration: %s",
                          status, status_messg, datetime.fromtimestamp(expiration_stamp/1000))
        return status, status_messg

    def change_to_order_type_mode(self, mode_name):
        if mode_name == MODES.BUY.name:
            mode_name = MODES.BUY_LIMIT.name
            mode = MODES.BUY_LIMIT.value
        elif mode_name == MODES.SELL.name:
            mode_name = MODES.SELL_LIMIT.name
            mode = MODES.SELL_LIMIT.value
        return mode, mode_name

    def _close_trade_only(self, order_id):
        """faster but less secure"""
        trade = self.trade_rec[order_id]
        self.logger.debug("Closing trade %s", order_id)
        try:
            response = self.trade_transaction(
                trade.symbol, 0, 2, trade.volume, order=trade.order_id,
                price=trade.price)
        except XTBApi.exceptions.CommandFailed as e:
            if e.err_code == 'BE51':  # order already closed
                self.logger.debug("BE51 error code noticed")
                return 'BE51'
            else:
                raise
        status = self.trade_transaction_status(
            response['order'])['requestStatus']
        self.logger.debug("Close_trade completed with status of %s", status)
        if status != 3:
            raise XTBApi.exceptions.TransactionRejected(status)
        return response

    def close_trade(self, trans):
        """close trade transaction"""
        if isinstance(trans, Transaction):
            order_id = trans.order_id
        else:
            order_id = trans
        self.update_trades()
        return self._close_trade_only(order_id)

    def close_all_trades(self):
        """close all trades"""
        self.update_trades()
        self.logger.debug("closing %i trades", len(self.trade_rec))
        trade_ids = self.trade_rec.keys()
        for trade_id in trade_ids:
            self._close_trade_only(trade_id)
