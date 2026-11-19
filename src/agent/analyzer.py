import json
import time
from typing import Literal
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from .config import (
    CONFIDENCE_THRESHOLD,
    GEMINI_API_KEY,
    HOLDING_LIMIT_HOURS,
    PROFIT_TARGET_PCT,
)

PRIMARY_MODEL = "gemini-3.8-flash"
FALLBACK_MODEL = "gemini-2.5-flash"


class TradeDecision(BaseModel):
    action: Literal["BUY", "SELL", "HOLD"]
    confidence: float = Field(description="Confidence score between 0.0 and 1.0")
    reasoning: str = Field(description="Concise justification based on the data")


class MarketAnalyzer:
    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY)

    def evaluate_position(self, market_state: dict, max_retries: int = 4) -> TradeDecision:
        prompt = f"""
        You are evaluating a short-term mean-reversion position on a low-beta equity.
        Rules:
        - Target profit per trade: {PROFIT_TARGET_PCT * 100:.1f}%
        - Maximum holding window: {HOLDING_LIMIT_HOURS} hours
        - Minimum required confidence to act: {CONFIDENCE_THRESHOLD:.2f}
        - If holding a position and current_price >= entry_price * (1 + profit_target_pct),
          strongly consider SELL to capture the target gain.
        - If hours_held >= holding_limit_hours, prioritize exiting or reviewing per risk rules.
        - Look for local dips relative to SMA_60 / negative Z_Score for BUY entries when flat.

        Market State:
        {json.dumps(market_state, indent=2)}
        """
        last_error = None
        for attempt in range(max_retries):
            model_to_use = PRIMARY_MODEL if attempt < max_retries - 1 else FALLBACK_MODEL
            try:
                response = self.client.models.generate_content(
                    model=model_to_use,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=TradeDecision,
                        temperature=0.1,
                    ),
                )
                return TradeDecision.model_validate_json(response.text)
            except Exception as exc:
                last_error = exc
                if attempt < max_retries - 1:
                    wait_seconds = min(3 * (2 ** attempt), 15)
                    print(
                        f"Transient error on {model_to_use} ({exc}). "
                        f"Retrying in {wait_seconds}s..."
                    )
                    time.sleep(wait_seconds)
                else:
                    raise last_error
