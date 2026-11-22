# Autonomous Low-Beta S&P 500 Mean Reversion Agent

## Architecture
1. **Dynamic Universe Discovery (`data_fetcher.py`):** Queries Alpaca for active, tradable US equities within the S&P 500 pool and fetches `SPY` benchmark returns.
2. **Deterministic Quantitative Screener (`universe_filter.py` & `analyzer.py`):**
   - Computes 90-day equity beta against `SPY` and discards tickers with `beta >= 0.85`.
   - Runs Augmented Dickey-Fuller (`adfuller`) stationarity check (`p < 0.05`).
   - Applies deterministic Z-score gates (`Z <= -1.0` for entries, `Z >= +1.0` or target/time limits for exits) locally before invoking Gemini.
3. **AI Qualitative Risk Manager (`analyzer.py`):** Evaluates only setups that pass all quantitative filters and returns a structured `BUY` / `SELL` / `HOLD` decision.
4. **Limit Order Execution (`executor.py`):** Submits paper limit orders (`LimitOrderRequest`) via `alpaca-py` with a 0.1% execution buffer when confidence meets `CONFIDENCE_THRESHOLD`.

## GitHub Secrets Required
Configure under **Settings > Secrets and variables > Actions > Secrets**:
- `GEMINI_API_KEY`
- `ALPACA_KEY`
- `ALPACA_SECRET`
