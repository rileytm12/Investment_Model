import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ALPACA_KEY = os.getenv("ALPACA_KEY")
ALPACA_SECRET = os.getenv("ALPACA_SECRET")

SYMBOL = "AAPL"
TRADE_QTY = 1
CONFIDENCE_THRESHOLD = 0.80
PROFIT_TARGET_PCT = 0.01
HOLDING_LIMIT_HOURS = 48
Z_SCORE_ENTRY_THRESHOLD = -1.5
Z_SCORE_EXIT_THRESHOLD = 1.0
ZERO_COMMISSION_UNIVERSE = [
    "AAPL",
    "MSFT",
    "GOOGL",
    "AMZN",
    "NVDA",
    "META",
    "BRK.B",
    "JNJ",
    "V",
    "PG",
]

