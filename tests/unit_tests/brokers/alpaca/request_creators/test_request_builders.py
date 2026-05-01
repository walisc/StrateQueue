

from StrateQueue.brokers.Alpaca.request_creators.request_builders import SideNotionalOrQuantityRequestBuilder
from StrateQueue.core.signal_extractor import SignalType,  OrderFunction, ExecStyle
from tests.unit_tests.brokers.alpaca.request_creators.test_utils.request_creator_test_utils import \
    RequestCreatorTestUtils


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_side_notional_quantity_target_percent():

    broker = RequestCreatorTestUtils.make_broker()
    broker.trading_client.set_account_portfolio_value(100.00)
    request_builder = SideNotionalOrQuantityRequestBuilder(broker, "AAPL")

    signal = RequestCreatorTestUtils.get_trading_signal(SignalType.SELL,
                                                         OrderFunction.ORDER_TARGET_PERCENT,
                                                         {"type":ExecStyle.MARKET, "details": {} },
                                                         10.0,
                                                         target_percent=0.1)


    current_params = {}


    request_builder.build(current_params, "AAPL", signal, "a_client_id")
    print(current_params)

    broker.set_current_account_positions({
        'AAPL': RequestCreatorTestUtils.get_mock_position('AAPL', 40, 10.0) #
    })

    request_builder.build(current_params, "AAPL", signal, "a_client_id")
    print(current_params)
    # -39




