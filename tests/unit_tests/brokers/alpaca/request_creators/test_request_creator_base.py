import pytest

from StrateQueue import SignalType, TradingSignal
from StrateQueue.brokers.Alpaca.request_creators.request_builders import AlpacaRequestBuilder
from StrateQueue.brokers.Alpaca.request_creators.request_creator_base import AlpacaRequestCreatorBase
from StrateQueue.core.signal_extractor import OrderFunction, ExecStyle
from tests.unit_tests.brokers.alpaca.request_creators.test_utils.request_creator_test_utils import \
    RequestCreatorTestUtils



def get_signal(ext_type:ExecStyle):
    return RequestCreatorTestUtils.get_trading_signal(SignalType.SELL,
                                                        OrderFunction.ORDER_TARGET_PERCENT,
                                                        {"type": ext_type, "details": {}},
                                                        10.0,
                                                        target_percent=0.1)

def test_can_get_correct_order_type_cls():
    from alpaca.trading.requests import (
        LimitOrderRequest,
        MarketOrderRequest,
        StopLimitOrderRequest,
        StopOrderRequest,
        TrailingStopOrderRequest
    )

    assert AlpacaRequestCreatorBase._get_request_cls(get_signal(ExecStyle.MARKET)) == MarketOrderRequest
    assert AlpacaRequestCreatorBase._get_request_cls(get_signal(ExecStyle.LIMIT)) == LimitOrderRequest
    assert AlpacaRequestCreatorBase._get_request_cls(get_signal(ExecStyle.STOP)) == StopOrderRequest
    assert AlpacaRequestCreatorBase._get_request_cls(get_signal(ExecStyle.STOP_LIMIT)) == StopLimitOrderRequest
    assert AlpacaRequestCreatorBase._get_request_cls(get_signal(ExecStyle.TRAILING_STOP)) == TrailingStopOrderRequest

def test_can_get_request_object():
    from alpaca.trading.enums import OrderSide
    from alpaca.trading.requests import LimitOrderRequest

    class MockBuilder(AlpacaRequestBuilder):

        def do_build(self, current_params, signal: TradingSignal, client_order_id: str):
            current_params['symbol'] = 'AAPL'
            current_params['qty'] = 55.0
            current_params['side'] = OrderSide.SELL
            current_params['limit_price'] = 55.0
            current_params['time_in_force'] = 'day'


    class MockCls(AlpacaRequestCreatorBase):
        def request_builders(self, request_cls):
            return [
                MockBuilder
            ]

    request = MockCls(RequestCreatorTestUtils.make_broker()).get_request('AAPL', get_signal(ExecStyle.LIMIT), 'aClient')

    assert isinstance(request, LimitOrderRequest)
    assert request.qty == 55.0
    assert request.symbol == 'AAPL'
    assert request.side == OrderSide.SELL
    assert request.limit_price == 55.0
    assert request.time_in_force == 'day'


def test_errors_if_require_builders_not_run():

    class MockBuilderOne(AlpacaRequestBuilder):

        def do_build(self, current_params, signal: TradingSignal, client_order_id: str):
            pass

    class MockBuilderTwo(AlpacaRequestBuilder):

        def do_build(self, current_params, signal: TradingSignal, client_order_id: str):
            pass

    class MockBuilderThree(AlpacaRequestBuilder):

        def requires(self):
            return [MockBuilderOne, MockBuilderTwo]

        def do_build(self, current_params, signal: TradingSignal, client_order_id: str):
            from alpaca.trading.enums import OrderSide

            current_params['symbol'] = 'AAPL'
            current_params['qty'] = 55.0
            current_params['side'] = OrderSide.SELL
            current_params['limit_price'] = 55.0
            current_params['time_in_force'] = 'day'


    class MockCls(AlpacaRequestCreatorBase):
        def request_builders(self, request_cls):
            return [
                MockBuilderThree,
                MockBuilderOne,
                MockBuilderTwo
            ]

    with pytest.raises(ValueError, match="The request builder 'MockBuilderThree' requires these builder to be run before 'MockBuilderOne, MockBuilderTwo'"):
        MockCls(RequestCreatorTestUtils.make_broker()).get_request('AAPL', get_signal(ExecStyle.LIMIT), 'aClient')

    class MockClsTwo(AlpacaRequestCreatorBase):
        def request_builders(self, request_cls):
            return [
                MockBuilderOne,
                MockBuilderTwo,
                MockBuilderThree
            ]

    request = MockClsTwo(RequestCreatorTestUtils.make_broker()).get_request('AAPL', get_signal(ExecStyle.LIMIT), 'aClient')

    from alpaca.trading.enums import OrderSide
    from alpaca.trading.requests import LimitOrderRequest

    assert isinstance(request, LimitOrderRequest)
    assert request.qty == 55.0
    assert request.symbol == 'AAPL'
    assert request.side == OrderSide.SELL
    assert request.limit_price == 55.0
    assert request.time_in_force == 'day'
