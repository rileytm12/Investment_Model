from datetime import datetime, timezone
from alpaca.trading.client import TradingClient
from .config import ALPACA_KEY, ALPACA_SECRET, HOLDING_LIMIT_HOURS


class PositionMonitor:
    def __init__(self):
        self.trading_client = TradingClient(ALPACA_KEY, ALPACA_SECRET, paper=True)

    def get_hours_held(self, symbol: str) -> float | None:
        activities = self.trading_client.get_account_activities(activity_types=["FILL"])
        for activity in activities:
            if getattr(activity, "symbol", None) == symbol and getattr(activity, "side", None) == "buy":
                tx_time = getattr(activity, "transaction_time", None)
                if tx_time is not None:
                    if tx_time.tzinfo is None:
                        tx_time = tx_time.replace(tzinfo=timezone.utc)
                    elapsed = datetime.now(timezone.utc) - tx_time
                    return round(elapsed.total_seconds() / 3600.0, 2)
                break
        return None

    def check_holding_limits(self, symbol: str) -> bool:
        hours_held = self.get_hours_held(symbol)
        if hours_held is not None and hours_held >= HOLDING_LIMIT_HOURS:
            return True
        return False
