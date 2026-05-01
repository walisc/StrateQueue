import abc
from abc import abstractmethod

from StrateQueue import TradingSignal, SignalType
from StrateQueue.core.signal_extractor import ExecStyle


class AlpacaRequestCreatorBase(abc.ABC):
    def __init__(self, broker):
        self.broker = broker

    def get_request(self, symbol: str, signal: TradingSignal, client_order_id: str):
        request_cls = self._get_request_cls(signal)
        request_cls_params = {}
        request_cls_tracker = []

        for request_builder in self.request_builders(request_cls):
            request_builder(symbol, self.broker, request_cls_tracker).build(request_cls_params, signal, client_order_id)
            request_cls_tracker.append(request_builder.__name__)

        return request_cls(**request_cls_params)

    @staticmethod
    def _get_request_cls(signal: TradingSignal):


        from alpaca.trading.requests import (
            LimitOrderRequest,
            MarketOrderRequest,
            StopLimitOrderRequest,
            StopOrderRequest,
            TrailingStopOrderRequest
        )

        if signal.execution_style == ExecStyle.TRAILING_STOP:
           return TrailingStopOrderRequest
        elif signal.execution_style == ExecStyle.LIMIT:
           return LimitOrderRequest
        elif signal.execution_style == ExecStyle.STOP:
            return StopOrderRequest
        elif signal.execution_style == ExecStyle.STOP_LIMIT:
            return StopLimitOrderRequest
        else:
            return MarketOrderRequest

    @abstractmethod
    def request_builders(self, request_cls):
        pass