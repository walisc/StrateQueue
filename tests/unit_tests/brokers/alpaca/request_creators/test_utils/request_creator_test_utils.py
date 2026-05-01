import pandas as pd

from StrateQueue import Position, TradingSignal, BrokerConfig, AlpacaBroker
# Dont remove, need for patching
import tests.unit_tests.brokers.alpaca.request_creators.test_utils.patch_alpaca

class MockAlpacaBroker(AlpacaBroker):
    def __init__(self, config: BrokerConfig):
        super().__init__(config)
        self._current_account_positions = {}

    def set_current_account_positions(self, value):
        self._current_account_positions = value

    def get_positions(self) -> dict[str, Position]:
        return self._current_account_positions

class RequestCreatorTestUtils:



    @staticmethod
    def make_broker():
        """Return a *connected* AlpacaBroker instance backed by fakes."""
        cfg = BrokerConfig("alpaca", credentials={"api_key": "k", "secret_key": "s"})
        broker = MockAlpacaBroker(cfg)
        assert broker.connect(), "Stub connection should always succeed"
        return broker

    @staticmethod
    def get_trading_signal(signal,
                            order_function,
                            execution_style_details,
                            price,
                            quantity=None,
                            value=None,
                            percent=None,
                            target_quantity=None,
                            target_value=None,
                            target_percent=None):
        base_props = {
            "signal": signal,
            "price": price,
            "indicators": {},
            "timestamp": pd.Timestamp.now(),
            "order_function": order_function,
            "execution_style": execution_style_details["type"],
            "quantity": quantity,
            "value": value,
            "percent": percent,
            "target_quantity": target_quantity,
            "target_value": target_value,
            "target_percent": target_percent
        }

        base_props.update(execution_style_details["details"])

        return TradingSignal(**base_props)

    @staticmethod
    def get_mock_position(symbol, qty, market_value):
        return Position(
            symbol=symbol,
            quantity=qty,
            market_value=market_value,
        )