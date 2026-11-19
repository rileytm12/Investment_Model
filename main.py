from src.agent.config import (
    HOLDING_LIMIT_HOURS,
    PROFIT_TARGET_PCT,
    ZERO_COMMISSION_UNIVERSE,
)
from src.agent.analyzer import MarketAnalyzer
from src.agent.data_fetcher import DataFetcher
from src.agent.executor import TradeExecutor
from src.agent.scheduler import PositionMonitor
from src.agent.universe_filter import UniverseFilter


def evaluate_symbol(
    symbol: str,
    fetcher: DataFetcher,
    filter_engine: UniverseFilter,
    analyzer: MarketAnalyzer,
    executor: TradeExecutor,
    monitor: PositionMonitor,
):
    df = fetcher.get_historical_data(symbol)
    if df.empty:
        print(f"[{symbol}] No historical data returned.")
        return

    df = fetcher.calculate_indicators(df)

    if not filter_engine.is_mean_reverting(df["close"]):
        print(f"[{symbol}] Not currently exhibiting mean-reverting behavior.")
        return

    current_qty = executor.get_current_position(symbol)
    entry_price = executor.get_entry_price(symbol)
    hours_held = monitor.get_hours_held(symbol)

    if current_qty > 0 and monitor.check_holding_limits(symbol):
        print(
            f"[{symbol}] Holding limit ({HOLDING_LIMIT_HOURS}h) reached. "
            "Forcing evaluation."
        )

    latest_data = df.iloc[-1].to_dict()
    market_state = {
        "symbol": symbol,
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
        f"[{symbol}] Decision: {decision.action} | Confidence: {decision.confidence:.2f} | "
        f"Reason: {decision.reasoning}"
    )

    executor.execute_decision(symbol, decision, current_qty, entry_price)


def main():
    fetcher = DataFetcher()
    filter_engine = UniverseFilter()
    analyzer = MarketAnalyzer()
    executor = TradeExecutor()
    monitor = PositionMonitor()

    for symbol in ZERO_COMMISSION_UNIVERSE:
        try:
            evaluate_symbol(symbol, fetcher, filter_engine, analyzer, executor, monitor)
        except Exception as exc:
            print(f"[{symbol}] Error during evaluation: {exc}")


if __name__ == "__main__":
    main()
