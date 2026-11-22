import pandas as pd
from statsmodels.tsa.stattools import adfuller
from .config import MAX_BETA


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

    @classmethod
    def passes_screener(
        cls,
        price_series: pd.Series,
        beta: float | None,
        max_beta: float = MAX_BETA,
        p_value_threshold: float = 0.05,
    ) -> tuple[bool, str]:
        if beta is None:
            return False, "Insufficient data to compute beta."
        if beta >= max_beta:
            return False, f"Beta {beta:.2f} >= max threshold {max_beta:.2f}."
        if not cls.is_mean_reverting(price_series, p_value_threshold=p_value_threshold):
            return False, f"Beta {beta:.2f} OK, but failed ADF mean-reversion test."
        return True, f"Passed screener (Beta {beta:.2f} < {max_beta:.2f}, stationary)."
