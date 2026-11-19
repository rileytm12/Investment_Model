from src.agent.config import (
    HOLDING_LIMIT_HOURS,
    PROFIT_TARGET_PCT,
    SYMBOL,
)
from src.agent.analyzer import MarketAnalyzer
from src.agent.data_fetcher import DataFetcher
from src.agent.executor import TradeExecutor
from src.agent.scheduler import PositionMonitor
from src.agent.universe_filter import UniverseFilter


def main():
    fetcher = DataFetcher()
    filter_engine = UniverseFilter()
    analyzer = MarketAnalyzer()
    executor = TradeExecutor()
    monitor = PositionMonitor()

    df = fetcher.get_historical_data(SYMBOL)
    if df.empty:
        print(f"No historical data returned for {SYMBOL}.")
        return

    df = fetcher.calculate_indicators(df)

    if not filter_engine.is_mean_reverting(df["close"]):
        print(f"{SYMBOL} is not currently exhibiting mean-reverting behavior.")
        return

    current_qty = executor.get_current_position(SYMBOL)
    entry_price = executor.get_entry_price(SYMBOL)
    hours_held = monitor.get_hours_held(SYMBOL)

    if current_qty > 0 and monitor.check_holding_limits(SYMBOL):
        print(
            f"Holding limit ({HOLDING_LIMIT_HOURS}h) reached for {SYMBOL}. "
            "Forcing evaluation."
        )

    latest_data = df.iloc[-1].to_dict()
    market_state = {
        "symbol": SYMBOL,
        "current_price": float(latest_data["close"]),
        "sma_60": None if latest_data["SMA_60"] != latest_data["SMA_60"] else float(latest_data["SMA_60"]),
        "z_score": None if latest_data["Z_Score"] != latest_data["Z_Score"] else float(latest_data["Z_Score"]),
        "current_shares": current_qty,
        "entry_price": entry_price,
        "hours_held": hours_held,
        "profit_target_pct": PROFIT_TARGET_PCT,
        "holding_limit_hours": HOLDING_LIMIT_HOURS,
    }

    decision = analyzer.evaluate_position(market_state)
    print(
        f"Decision: {decision.action} | Confidence: {decision.confidence:.2f} | "
        f"Reason: {decision.reasoning}"
    )

    executor.execute_decision(SYMBOL, decision, current_qty, entry_price)


if __name__ == "__main__":
    main()
