import pandas as pd
from statsmodels.tsa.stattools import adfuller


class UniverseFilter:
    @staticmethod
    def is_mean_reverting(
        price_series: pd.Series, p_value_threshold: float = 0.05
    ) -> bool:
        dropna_series = price_series.dropna()
        if len(dropna_series) < 60:
            return False
        result = adfuller(dropna_series, result_object=False)
        p_value = result[1]
        return bool(p_value < p_value_threshold)
