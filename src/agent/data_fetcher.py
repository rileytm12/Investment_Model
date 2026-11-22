from datetime import datetime, timedelta, timezone
import numpy as np
import pandas as pd
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import AssetClass, AssetStatus
from alpaca.trading.requests import GetAssetsRequest
from .config import (
    ALPACA_KEY,
    ALPACA_SECRET,
    BENCHMARK_SYMBOL,
    MAX_SCAN_CANDIDATES,
    SP500_UNIVERSE,
)


class DataFetcher:
    def __init__(self):
        self.data_client = StockHistoricalDataClient(ALPACA_KEY, ALPACA_SECRET)
        self.trading_client = TradingClient(ALPACA_KEY, ALPACA_SECRET, paper=True)

    def get_sp500_tradable_universe(self) -> list[str]:
        """Queries Alpaca active tradable equities and intersects with S&P 500 constituents."""
        request = GetAssetsRequest(
            status=AssetStatus.ACTIVE,
            asset_class=AssetClass.US_EQUITY,
        )
        assets = self.trading_client.get_all_assets(request)
        tradable_symbols = {
            asset.symbol
            for asset in assets
            if getattr(asset, "tradable", False) and getattr(asset, "fractionable", True)
        }
        filtered = [sym for sym in SP500_UNIVERSE if sym in tradable_symbols]
        return filtered[:MAX_SCAN_CANDIDATES]

    def get_historical_data(self, symbol: str, days: int = 120) -> pd.DataFrame:
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        request_params = StockBarsRequest(
            symbol_or_symbols=[symbol],
            timeframe=TimeFrame.Day,
            start=start_date,
        )
        bars = self.data_client.get_stock_bars(request_params).df
        if bars.empty:
            return pd.DataFrame()
        if isinstance(bars.index, pd.MultiIndex):
            if symbol in bars.index.get_level_values(0):
                return bars.xs(symbol, level=0).copy()
            return pd.DataFrame()
        return bars.copy()

    def get_benchmark_returns(self, days: int = 120) -> pd.Series:
        spy_df = self.get_historical_data(BENCHMARK_SYMBOL, days=days)
        if spy_df.empty or "close" not in spy_df.columns:
            return pd.Series(dtype=float)
        returns = spy_df["close"].pct_change().dropna()
        returns.index = pd.to_datetime(returns.index).normalize()
        return returns

    @staticmethod
    def calculate_beta(
        price_series: pd.Series, benchmark_returns: pd.Series, lookback: int = 90
    ) -> float | None:
        if price_series.empty or benchmark_returns.empty:
            return None

        asset_returns = price_series.pct_change().dropna()
        asset_returns.index = pd.to_datetime(asset_returns.index).normalize()

        aligned = pd.concat(
            [asset_returns.rename("asset"), benchmark_returns.rename("benchmark")],
            axis=1,
            join="inner",
        ).dropna().tail(lookback)

        if len(aligned) < 30:
            return None

        bench_var = np.var(aligned["benchmark"], ddof=1)
        if bench_var == 0:
            return None

        cov = np.cov(aligned["asset"], aligned["benchmark"], ddof=1)[0, 1]
        return float(cov / bench_var)

    @staticmethod
    def calculate_indicators(df: pd.DataFrame, window: int = 60) -> pd.DataFrame:
        df = df.copy()
        df["SMA_60"] = df["close"].rolling(window=window).mean()
        df["STD_60"] = df["close"].rolling(window=window).std()
        df["Z_Score"] = (df["close"] - df["SMA_60"]) / df["STD_60"]
        return df
