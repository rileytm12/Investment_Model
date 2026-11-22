import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ALPACA_KEY = os.getenv("ALPACA_KEY")
ALPACA_SECRET = os.getenv("ALPACA_SECRET")

TRADE_QTY = 1
CONFIDENCE_THRESHOLD = 0.80
PROFIT_TARGET_PCT = 0.01
HOLDING_LIMIT_HOURS = 48

# Beta & Benchmark Parameters
BENCHMARK_SYMBOL = "SPY"
MAX_BETA = 0.85
BETA_LOOKBACK_DAYS = 90

# Deterministic Z-Score Gates
Z_SCORE_ENTRY_THRESHOLD = -1.0
Z_SCORE_EXIT_THRESHOLD = 1.0

# Dynamic S&P 500 Scan Limit per Run
MAX_SCAN_CANDIDATES = 50

# Curated S&P 500 Baseline Universe (defensive, consumer, healthcare, utilities, industrials, tech)
SP500_UNIVERSE = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "BRK.B", "JNJ", "V", "PG", "UNH",
    "JPM", "XOM", "MA", "HD", "CVX", "MRK", "ABBV", "PEP", "KO", "COST",
    "WMT", "MCD", "CSCO", "ACN", "TMO", "ABT", "DHR", "LIN", "NEE", "PM",
    "VZ", "T", "CMCSA", "RTX", "HON", "UNP", "LOW", "SPGI", "INTU", "IBM",
    "GE", "CAT", "DE", "PLD", "AMT", "DUK", "SO", "CL", "GIS", "KMB",
    "SYY", "HSY", "MMC", "AON", "CB", "PGR", "TRV", "WM", "RSG", "ED",
    "EXC", "XEL", "WEC", "ES", "AWK", "MDT", "SYK", "BDX", "CI", "ELV",
    "HUM", "CVS", "GILD", "AMGN", "BMY", "ZTS", "ADP", "PAYX", "ITW", "EMR",
]
