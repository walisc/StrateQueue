import sys
import types
import uuid
from typing import Any, List
import datetime as _dt


class _FakeAPIError(Exception):
    """Replacement for alpaca.common.exceptions.APIError"""

class _FakeOrder:  # noqa: D401 – simple data holder
    def __init__(self, symbol: str, side: str, qty: float, otype: str, price: float | None = None):
        self.id: str = str(uuid.uuid4())
        self.client_order_id: str = f"cli-{self.id}"
        self.symbol: str = symbol
        self.side = types.SimpleNamespace(value=side)
        self.order_type = types.SimpleNamespace(value=otype)
        self.qty = qty
        self.notional = None  # type: ignore[assignment]
        self.filled_qty = 0
        self.status = types.SimpleNamespace(value="accepted")
        # ADD start
        # Pricing helpers – AlpacaBroker may read these directly
        self.limit_price = price  # present for LIMIT / STOP_LIMIT orders
        self.stop_price = None
        self.price = price  # fallback used by broker when limit_price absent

        # Additional attributes expected by get_order_status
        self.client_order_id = self.id  # Use same as id for simplicity
        self.order_type = types.SimpleNamespace(value=otype)
        self.filled_qty = 0.0
        # ADD end
        now = _dt.datetime.utcnow()
        self.created_at = self.updated_at = now

    # Allow ``.__dict__`` serialisation similar to real alpaca objects
    def __repr__(self) -> str:  # pragma: no cover
        return f"<_FakeOrder {self.id} {self.side.value} qty={self.qty}>"

class _FakeAlpacaClient:  # noqa: D401 – stub class
    def __init__(self, *_: Any, **__: Any) -> None:  # accept arbitrary kwargs
        self._orders: List[_FakeOrder] = []
        self._current_account_portfolio_value = "100000"
        self._current_account_positions = []

    # ---------------------------------------------------------------------
    # Credential validation helper (called by broker.validate_credentials)
    # ---------------------------------------------------------------------
    def get_account(self):
        return types.SimpleNamespace(
            id="ACCT-TEST",
            portfolio_value=self._current_account_portfolio_value,
            cash="50000",
            daytrade_count=0,
            # ADD start – extra fields accessed by AlpacaBroker
            buying_power="50000",
            pattern_day_trader=False,
            currency="USD",
            # ADD end
        )

    # ---------------------------------------------------------------------
    # Order lifecycle helpers
    # ---------------------------------------------------------------------
    def submit_order(self, order_request):  # noqa: D401 – stub
        symbol = getattr(order_request, "symbol", "AAPL")
        order = _FakeOrder(
            symbol=symbol,
            side=order_request.side.value,
            qty=getattr(order_request, "qty", 0.0),
            otype=order_request.__class__.__name__.replace("OrderRequest", "").upper(),
            price=getattr(order_request, "limit_price", None),
        )
        # Set additional order attributes from request
        order.stop_price = getattr(order_request, "stop_price", None)
        order.limit_price = getattr(order_request, "limit_price", None)
        self._orders.append(order)
        return order

    def get_orders(self, symbol: str | None = None):  # noqa: D401 – stub
        return [o for o in self._orders if symbol is None or o.symbol == symbol]

    def get_order_by_id(self, order_id: str):  # noqa: D401 – stub
        return next((o for o in self._orders if o.id == order_id), None)

    def cancel_order_by_id(self, order_id: str):  # noqa: D401 – stub
        # Mark status as canceled rather than deleting to mimic real API
        for o in self._orders:
            if o.id == order_id:
                o.status = types.SimpleNamespace(value="canceled")
                break

    def cancel_all_orders(self, *_: Any, **__: Any):  # noqa: D401 – stub
        self._orders.clear()

    # ADD start – alias used by AlpacaBroker.cancel_all_orders
    def cancel_orders(self, *_: Any, **__: Any):  # noqa: D401 – stub
        # Real SDK name; delegate to the existing helper
        self.cancel_all_orders()

    # ADD end

    def replace_order_by_id(self, order_id: str, replace_request=None, **kwargs):  # noqa: D401 – stub
        # Simplified: update known mutable fields on the target order
        order = self.get_order_by_id(order_id)
        if order is None:
            # Raise an exception like the real API would
            raise _FakeAPIError(f"Order {order_id} not found")

        # Update from replace_request if provided
        if replace_request is not None:
            # Copy over attributes the broker may set (limit_price, stop_price, qty)
            for attr in ("limit_price", "stop_price", "qty", "price"):
                if hasattr(replace_request, attr):
                    setattr(order, attr, getattr(replace_request, attr))
                    order.updated_at = _dt.datetime.utcnow()

        # Update from kwargs (direct parameter updates)
        for attr, value in kwargs.items():
            if hasattr(order, attr):
                setattr(order, attr, value)
                order.updated_at = _dt.datetime.utcnow()

        return True

    # Simplified positions helper
    def get_open_position(self, _symbol: str):  # noqa: D401 – stub
        raise Exception("no position")

    def close_all_positions(self, *_: Any, **__: Any):  # noqa: D401 – stub
        self._orders.clear()

    # ADD start – positions list helper required by broker.get_positions
    def get_all_positions(self, *_: Any, **__: Any):  # noqa: D401 – stub
        # Return empty list (no open positions) for simplicity
        return []
    # ADD end

    def set_account_portfolio_value(self, value):
        self._current_account_portfolio_value = value



for _mn, _m in list(sys.modules.items()):
    if _mn.startswith("StrateQueue.brokers.Alpaca") and hasattr(_m, "ALPACA_AVAILABLE"):
        _m.ALPACA_AVAILABLE = True  # ensure broker uses stub SDK
        setattr(_m, "TradingClient", _FakeAlpacaClient)
        setattr(_m, "APIError", _FakeAPIError)


