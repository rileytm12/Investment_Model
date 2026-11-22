from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import LimitOrderRequest
from .config import (
    ALPACA_KEY,
    ALPACA_SECRET,
    CONFIDENCE_THRESHOLD,
    TRADE_QTY,
)

LIMIT_BUFFER_PCT = 0.001  # 0.1% execution buffer


class TradeExecutor:
    def __init__(self):
        self.trading_client = TradingClient(ALPACA_KEY, ALPACA_SECRET, paper=True)

    def get_open_position_symbols(self) -> list[str]:
        positions = self.trading_client.get_all_positions()
        return [p.symbol for p in positions if float(p.qty) > 0]

    def get_current_position(self, symbol: str) -> float:
        positions = self.trading_client.get_all_positions()
        for p in positions:
            if p.symbol == symbol:
                return float(p.qty)
        return 0.0

    def get_entry_price(self, symbol: str) -> float | None:
        positions = self.trading_client.get_all_positions()
        for p in positions:
            if p.symbol == symbol and p.avg_entry_price is not None:
                return float(p.avg_entry_price)
        return None

    def is_tradable_asset(self, symbol: str) -> bool:
        try:
            asset = self.trading_client.get_asset(symbol)
            return bool(getattr(asset, "tradable", False))
        except Exception:
            return False

    def execute_decision(
        self,
        symbol: str,
        decision,
        current_qty: float,
        current_price: float,
        entry_price: float | None = None,
        buffer_pct: float = LIMIT_BUFFER_PCT,
    ):
        if not self.is_tradable_asset(symbol):
            print(f"[{symbol}] Aborted: Asset is not tradable on Alpaca.")
            return

        if decision.confidence < CONFIDENCE_THRESHOLD:
            print(
                f"[{symbol}] Aborted: Confidence {decision.confidence:.2f} is below "
                f"threshold {CONFIDENCE_THRESHOLD:.2f}."
            )
            return

        if current_price is None or current_price <= 0:
            print(f"[{symbol}] Aborted: Invalid current_price ({current_price}) for limit order.")
            return

        if decision.action == "BUY" and current_qty == 0:
            limit_price = round(current_price * (1 + buffer_pct), 2)
            order_data = LimitOrderRequest(
                symbol=symbol,
                qty=TRADE_QTY,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.DAY,
                limit_price=limit_price,
            )
            self.trading_client.submit_order(order_data)
            print(
                f"[{symbol}] Submitted BUY limit order for {TRADE_QTY} share(s) "
                f"at limit ${limit_price:.2f} (ref: ${current_price:.2f})."
            )
        elif decision.action == "SELL" and current_qty > 0:
            limit_price = round(current_price * (1 - buffer_pct), 2)
            order_data = LimitOrderRequest(
                symbol=symbol,
                qty=current_qty,
                side=OrderSide.SELL,
                time_in_force=TimeInForce.DAY,
                limit_price=limit_price,
            )
            self.trading_client.submit_order(order_data)
            entry_info = f" (entry: ${entry_price:.2f})" if entry_price else ""
            print(
                f"[{symbol}] Submitted SELL limit order for {current_qty} share(s) "
                f"at limit ${limit_price:.2f} (ref: ${current_price:.2f}){entry_info}."
            )
        else:
            print(f"[{symbol}] No order submitted for action {decision.action} with qty {current_qty}.")
