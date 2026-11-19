from datetime import datetime, timezone
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, QueryOrderStatus
from alpaca.trading.requests import GetOrdersRequest
from .config import ALPACA_KEY, ALPACA_SECRET, HOLDING_LIMIT_HOURS


class PositionMonitor:
    def __init__(self):
        self.trading_client = TradingClient(ALPACA_KEY, ALPACA_SECRET, paper=True)

    def get_hours_held(self, symbol: str) -> float | None:
        request = GetOrdersRequest(
            status=QueryOrderStatus.CLOSED,
            side=OrderSide.BUY,
            limit=50,
        )
        orders = self.trading_client.get_orders(request)
        for order in orders:
            if getattr(order, "symbol", None) == symbol and getattr(order, "filled_at", None) is not None:
                filled_time = order.filled_at
                if filled_time.tzinfo is None:
                    filled_time = filled_time.replace(tzinfo=timezone.utc)
                elapsed = datetime.now(timezone.utc) - filled_time
                return round(elapsed.total_seconds() / 3600.0, 2)
        return None

    def check_holding_limits(self, symbol: str) -> bool:
        hours_held = self.get_hours_held(symbol)
        if hours_held is not None and hours_held >= HOLDING_LIMIT_HOURS:
            return True
        return False
