from abc import ABC, abstractmethod


from StrateQueue import TradingSignal, SignalType


class AlpacaRequestBuilder(ABC):

    def __init__(self, symbol, alpaca_broker, tracker):
        self.alpaca_broker = alpaca_broker
        self.symbol = symbol
        self.tracker = tracker

    def build(self, current_params, signal: TradingSignal, client_order_id: str):
        required_cls = [x.__name__ for x in self.requires()]

        run_id_list = set(required_cls).intersection(self.tracker)

        if len(run_id_list) != len(required_cls):
            raise ValueError(f"The request builder '{self.__class__.__name__}' requires these builder to be run before '{', '.join(required_cls)}'")

        self.do_build(current_params, signal, client_order_id)

    @abstractmethod
    def do_build(self, current_params, signal: TradingSignal, client_order_id: str):
        pass

    def requires(self):
        return []

class BaseDataRequestBuilder(AlpacaRequestBuilder):
    def do_build(self, current_params, signal: TradingSignal, client_order_id: str):
        current_params["symbol"] = self.symbol


class SideNotionalOrQuantityRequestBuilder(AlpacaRequestBuilder):
    def _get_order_target_percentage_as_order_target(self, _target_percent, signal_price):
        account = self.alpaca_broker.get_account_info()
        portfolio_value_pct = float(account.total_value * _target_percent)
        return self._get_order_target_value_as_order_target(portfolio_value_pct, signal_price)

    def _get_order_target_value_as_order_target(self, _target_value, signal_price):
        current_price = signal_price
        asset_amount = float(_target_value / current_price)
        return self._get_order_target_as_order_target(asset_amount, signal_price)

    def _get_order_target_as_order_target(self, _target_amount, signal_price):
        asset_amount = _target_amount
        all_positions = self.alpaca_broker.get_positions()
        if self.symbol in all_positions:
            current_position = all_positions[self.symbol].quantity
            asset_amount -= current_position

        if asset_amount > 0:
            return asset_amount, SignalType.BUY
        else:
            return asset_amount * -1, SignalType.SELL

    def do_build(self, current_params, signal: TradingSignal, client_order_id: str):

        from alpaca.trading.enums import OrderSide


        def get_alpaca_side(_signal_side):
            buy_signal_types = [
                SignalType.BUY,
                SignalType.LIMIT_BUY,
                SignalType.STOP_BUY,
                SignalType.STOP_LIMIT_BUY,
            ]


            is_buy_signal = (_signal_side in buy_signal_types or
                             (hasattr(_signal_side, 'value') and
                              _signal_side.value in [sig.value for sig in buy_signal_types]))

            return OrderSide.BUY if is_buy_signal else OrderSide.SELL

        if signal.quantity is not None:
            current_params["side"] = get_alpaca_side(signal.signal)
            current_params["qty"] = signal.quantity
        elif signal.value is not None:
            current_params["side"] = get_alpaca_side(signal.signal)
            current_params["notional"] = round(signal.value, 2)
        elif signal.percent is not None:
            account = self.alpaca_broker.get_account_info()
            current_params["side"] = get_alpaca_side(signal.signal)
            current_params["notional"] = round(float(account.total_value * signal.percent), 2)
        elif signal.target_percent is not None:
            amount, side = self._get_order_target_percentage_as_order_target(signal.target_percent, signal.price)
            current_params["side"] = get_alpaca_side(side)
            current_params["qty"] = amount
        elif signal.target_value is not None:
            amount, side = self._get_order_target_value_as_order_target(signal.target_percent, signal.price)
            current_params["side"] = get_alpaca_side(side)
            current_params["qty"] = amount
        elif signal.target_percent is not None:
            amount, side = self._get_order_target_as_order_target(signal.target_percent, signal.price)
            current_params["side"] = get_alpaca_side(side)
            current_params["qty"] = amount



class OrderClassRequestBuilder(AlpacaRequestBuilder):
    def do_build(self, current_params, signal: TradingSignal, client_order_id: str):

        if not signal.metadata:
            return

        order_class = None
        take_profit = None
        stop_loss = None


        order_class = signal.metadata.get("order_class")
        tp = signal.metadata.get("tp")
        sl = signal.metadata.get("sl")

        if order_class:
            if not ("type" in order_class and "details" in order_class):
                raise ValueError(f"order_class specified in the signal metadata, but 'type' and 'details' not specified")

            current_params["order_class"] = order_class["type"]
            current_params.update(order_class["details"])
            return

        if tp and sl:
            order_class = "bracket"
            take_profit = {"limit_price": tp}
            stop_loss = {"stop_price": sl}
        elif tp:
            order_class = "oto"
            take_profit = {"limit_price": tp}
        elif sl:
            order_class = "oto"
            stop_loss = {"stop_price": sl}
        elif signal.signal in [
            SignalType.LIMIT_SELL,
            SignalType.STOP_SELL,
            SignalType.STOP_LIMIT_SELL,
            SignalType.TRAILING_STOP_SELL,
        ] and (tp or sl):
            if tp and sl:
                order_class = "oco"
                take_profit = {"limit_price": tp}
                stop_loss = {"stop_price": sl}

        if order_class:
            current_params["order_class"] = order_class
            if take_profit:
                current_params["take_profit"] = take_profit
            if stop_loss:
                current_params["stop_loss"] = stop_loss


class ExtraMetadataRequestBuilder(AlpacaRequestBuilder):

    def requires(self):
        return [SideNotionalOrQuantityRequestBuilder]

    def do_build(self, current_params, signal: TradingSignal, client_order_id: str):
        from alpaca.trading.enums import TimeInForce

        tif_map = {
            "day": TimeInForce.DAY,
            "gtc": TimeInForce.GTC,
            "ioc": TimeInForce.IOC,
            "fok": TimeInForce.FOK,
            "opg": TimeInForce.OPG,
            "cls": TimeInForce.CLS,
        }

        is_crypto = "/" in self.symbol or self.symbol in ["BTCUSD", "ETHUSD", "DOGEUSD", "LTCUSD", "BCHUSD", "ADAUSD", "DOTUSD", "UNIUSD", "LINKUSD",
                          "SOLUSD"]

        if "qty" in current_params and current_params["qty"] % 1 != 0:
            current_params["time_in_force"] = TimeInForce.DAY
        else:
            current_params["time_in_force"] = tif_map.get(signal.time_in_force.lower(), TimeInForce.DAY)

        current_params["client_order_id"] = client_order_id
        current_params["extended_hours"] = (signal.metadata or {}).get("extended_hours", False) and not is_crypto

        if (signal.metadata or {}).get("validate_only", False):
            current_params["validate_only"] = True


class LimitPriceRequestBuilder(AlpacaRequestBuilder):

    def requires(self):
        return [OrderClassRequestBuilder]

    def do_build(self, current_params, signal: TradingSignal, client_order_id: str):
        if "order_class" not in current_params:
            current_params["limit_price"] = signal.limit_price or signal.price


class StopPriceRequestBuilder(AlpacaRequestBuilder):
    def requires(self):
        return [OrderClassRequestBuilder]

    def do_build(self, current_params, signal: TradingSignal, client_order_id: str):
        if "order_class" not in current_params:
            current_params["stop_price"] = signal.stop_price or signal.price


class TrailDateRequestBuilder(AlpacaRequestBuilder):
    def do_build(self, current_params, signal: TradingSignal, client_order_id: str):
        if signal.trail_percent:
            current_params["trail_percent"] = signal.trail_percent
        elif signal.trail_price:
            current_params["trail_amount"] = signal.trail_price
        else:
            # Default to 2% trailing stop
            current_params["trail_percent"] = 2.0
