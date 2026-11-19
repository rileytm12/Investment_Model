from datetime import datetime, timedelta, timezone
import pandas as pd
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from .config import ALPACA_KEY, ALPACA_SECRET


class DataFetcher:
    def __init__(self):
        self.data_client = StockHistoricalDataClient(ALPACA_KEY, ALPACA_SECRET)

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

    def calculate_indicators(self, df: pd.DataFrame, window: int = 60) -> pd.DataFrame:
        df = df.copy()
        df["SMA_60"] = df["close"].rolling(window=window).mean()
        df["STD_60"] = df["close"].rolling(window=window).std()
        df["Z_Score"] = (df["close"] - df["SMA_60"]) / df["STD_60"]
        return df
