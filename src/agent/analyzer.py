import json
import time
from typing import Literal
from google import genai
from google.genai import types
from google.genai.errors import APIError
from pydantic import BaseModel, Field
from .config import (
    CONFIDENCE_THRESHOLD,
    GEMINI_API_KEY,
    HOLDING_LIMIT_HOURS,
    PROFIT_TARGET_PCT,
)


class TradeDecision(BaseModel):
    action: Literal["BUY", "SELL", "HOLD"]
    confidence: float = Field(description="Confidence score between 0.0 and 1.0")
    reasoning: str = Field(description="Concise justification based on the data")


class MarketAnalyzer:
    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY)

    def evaluate_position(self, market_state: dict, max_retries: int = 3) -> TradeDecision:
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
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=TradeDecision,
                        temperature=0.1,
                    ),
                )
                return TradeDecision.model_validate_json(response.text)
            except APIError as exc:
                if exc.code == 503 and attempt < max_retries - 1:
                    wait_seconds = 2 ** (attempt + 1)
                    print(f"Model busy (503). Retrying in {wait_seconds}s...")
                    time.sleep(wait_seconds)
                else:
                    raise
