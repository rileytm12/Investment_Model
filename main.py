import time
from src.agent.analyzer import MarketAnalyzer
from src.agent.config import (
    BETA_LOOKBACK_DAYS,
    HOLDING_LIMIT_HOURS,
    MAX_BETA,
    PROFIT_TARGET_PCT,
)
from src.agent.data_fetcher import DataFetcher
from src.agent.executor import TradeExecutor
from src.agent.scheduler import PositionMonitor
from src.agent.universe_filter import UniverseFilter


def evaluate_symbol(
    symbol: str,
    spy_returns,
    fetcher: DataFetcher,
    filter_engine: UniverseFilter,
    analyzer: MarketAnalyzer,
    executor: TradeExecutor,
    monitor: PositionMonitor,
):
    current_qty = executor.get_current_position(symbol)
    entry_price = executor.get_entry_price(symbol)
    hours_held = monitor.get_hours_held(symbol)

    df = fetcher.get_historical_data(symbol, days=max(120, BETA_LOOKBACK_DAYS + 30))
    if df.empty:
        print(f"[{symbol}] No historical data returned.")
        return

    df = fetcher.calculate_indicators(df)
    beta = fetcher.calculate_beta(df["close"], spy_returns, lookback=BETA_LOOKBACK_DAYS)

    if current_qty == 0:
        passed, reason = filter_engine.passes_screener(
            price_series=df["close"],
            beta=beta,
            max_beta=MAX_BETA,
        )
        if not passed:
            print(f"[{symbol}] Filtered out: {reason}")
            return
    else:
        if monitor.check_holding_limits(symbol):
            print(
                f"[{symbol}] Holding limit ({HOLDING_LIMIT_HOURS}h) reached. "
                "Forcing exit evaluation."
            )

    latest_data = df.iloc[-1].to_dict()
    sma_60 = latest_data.get("SMA_60")
    z_score = latest_data.get("Z_Score")

    market_state = {
        "symbol": symbol,
        "beta_vs_spy": None if beta is None else round(beta, 4),
        "max_allowed_beta": MAX_BETA,
        "current_price": float(latest_data["close"]),
        "sma_60": None if sma_60 != sma_60 else float(sma_60),
        "z_score": None if z_score != z_score else float(z_score),
        "current_shares": current_qty,
        "entry_price": entry_price,
        "hours_held": hours_held,
        "profit_target_pct": PROFIT_TARGET_PCT,
        "holding_limit_hours": HOLDING_LIMIT_HOURS,
    }

    decision = analyzer.evaluate_position(market_state)
    print(
        f"[{symbol}] (Beta: {market_state['beta_vs_spy']}, Z: {market_state['z_score']}) "
        f"Decision: {decision.action} | Confidence: {decision.confidence:.2f} | "
        f"Reason: {decision.reasoning}"
    )

    executor.execute_decision(
        symbol=symbol,
        decision=decision,
        current_qty=current_qty,
        current_price=market_state["current_price"],
        entry_price=entry_price,
    )


def main():
    fetcher = DataFetcher()
    filter_engine = UniverseFilter()
    analyzer = MarketAnalyzer()
    executor = TradeExecutor()
    monitor = PositionMonitor()

    spy_returns = fetcher.get_benchmark_returns(days=max(120, BETA_LOOKBACK_DAYS + 30))
    if spy_returns.empty:
        print("Failed to fetch SPY benchmark data. Aborting run.")
        return

    open_symbols = executor.get_open_position_symbols()
    candidates = fetcher.get_sp500_tradable_universe()

    # Always evaluate open positions first, followed by dynamic S&P 500 candidates
    scan_queue = list(dict.fromkeys(open_symbols + candidates))
    print(f"Scanning {len(scan_queue)} S&P 500 symbols (Open positions: {len(open_symbols)})...")

    for symbol in scan_queue:
        try:
            evaluate_symbol(
                symbol=symbol,
                spy_returns=spy_returns,
                fetcher=fetcher,
                filter_engine=filter_engine,
                analyzer=analyzer,
                executor=executor,
                monitor=monitor,
            )
            time.sleep(0.25)
        except Exception as exc:
            print(f"[{symbol}] Error during evaluation: {exc}")


if __name__ == "__main__":
    main()
