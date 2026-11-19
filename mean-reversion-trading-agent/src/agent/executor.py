from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import MarketOrderRequest
from .config import (
    ALPACA_KEY,
    ALPACA_SECRET,
    CONFIDENCE_THRESHOLD,
    TRADE_QTY,
    ZERO_COMMISSION_UNIVERSE,
)


class TradeExecutor:
    def __init__(self):
        self.trading_client = TradingClient(ALPACA_KEY, ALPACA_SECRET, paper=True)

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

    def execute_decision(
        self,
        symbol: str,
        decision,
        current_qty: float,
        entry_price: float | None = None,
    ):
        if symbol not in ZERO_COMMISSION_UNIVERSE:
            print(f"Aborted: {symbol} is not in ZERO_COMMISSION_UNIVERSE.")
            return

        if decision.confidence < CONFIDENCE_THRESHOLD:
            print(
                f"Aborted: Confidence {decision.confidence:.2f} is below "
                f"threshold {CONFIDENCE_THRESHOLD:.2f}."
            )
            return

        if decision.action == "BUY" and current_qty == 0:
            order_data = MarketOrderRequest(
                symbol=symbol,
                qty=TRADE_QTY,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.DAY,
            )
            self.trading_client.submit_order(order_data)
            print(f"Submitted BUY order for {TRADE_QTY} share(s) of {symbol}.")
        elif decision.action == "SELL" and current_qty > 0:
            order_data = MarketOrderRequest(
                symbol=symbol,
                qty=current_qty,
                side=OrderSide.SELL,
                time_in_force=TimeInForce.DAY,
            )
            self.trading_client.submit_order(order_data)
            entry_info = f" (entry: ${entry_price:.2f})" if entry_price else ""
            print(f"Submitted SELL order for {current_qty} share(s) of {symbol}{entry_info}.")
        else:
            print(f"No order submitted for action {decision.action} with qty {current_qty}.")
