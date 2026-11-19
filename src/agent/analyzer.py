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
    Z_SCORE_ENTRY_THRESHOLD,
    Z_SCORE_EXIT_THRESHOLD,
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

    def _passes_deterministic_gate(self, market_state: dict) -> tuple[bool, str]:
        z_score = market_state.get("z_score")
        current_shares = market_state.get("current_shares", 0)
        current_price = market_state.get("current_price")
        entry_price = market_state.get("entry_price")
        hours_held = market_state.get("hours_held")
        profit_target_pct = market_state.get("profit_target_pct", PROFIT_TARGET_PCT)
        holding_limit_hours = market_state.get("holding_limit_hours", HOLDING_LIMIT_HOURS)

        if z_score is None:
            return False, "Insufficient data for Z-score calculation; holding locally."

        if current_shares == 0:
            if z_score <= Z_SCORE_ENTRY_THRESHOLD:
                return True, f"Z-score ({z_score:.2f}) <= entry threshold ({Z_SCORE_ENTRY_THRESHOLD})."
            return (
                False,
                f"Flat position with Z-score ({z_score:.2f}) > entry threshold ({Z_SCORE_ENTRY_THRESHOLD}); holding locally.",
            )

        profit_target_hit = (
            entry_price is not None
            and current_price is not None
            and current_price >= entry_price * (1 + profit_target_pct)
        )
        holding_limit_hit = hours_held is not None and hours_held >= holding_limit_hours
        z_exit_hit = z_score >= Z_SCORE_EXIT_THRESHOLD

        if z_exit_hit or profit_target_hit or holding_limit_hit:
            return True, "Exit or risk condition triggered; escalating to LLM for confirmation."

        return (
            False,
            f"Open position within limits (Z-score {z_score:.2f} < {Z_SCORE_EXIT_THRESHOLD}, target/time limits not met); holding locally.",
        )

    def evaluate_position(self, market_state: dict, max_retries: int = 4) -> TradeDecision:
        should_call_llm, gate_reason = self._passes_deterministic_gate(market_state)
        if not should_call_llm:
            return TradeDecision(
                action="HOLD",
                confidence=1.0,
                reasoning=gate_reason,
            )

        prompt = f"""
        You are evaluating a short-term mean-reversion position on a low-beta equity.
        Rules:
        - Target profit per trade: {PROFIT_TARGET_PCT * 100:.1f}%
        - Maximum holding window: {HOLDING_LIMIT_HOURS} hours
        - Minimum required confidence to act: {CONFIDENCE_THRESHOLD:.2f}
        - Entry Z-score threshold: {Z_SCORE_ENTRY_THRESHOLD}
        - Exit Z-score threshold: {Z_SCORE_EXIT_THRESHOLD}
        - If holding a position and (current_price >= entry_price * (1 + profit_target_pct) or z_score >= {Z_SCORE_EXIT_THRESHOLD}),
          strongly consider SELL to capture the target gain or mean reversion.
        - If hours_held >= holding_limit_hours, prioritize exiting or reviewing per risk rules.
        - Confirm BUY entries when flat only if Z-score <= {Z_SCORE_ENTRY_THRESHOLD} represents a valid mean-reversion dip.

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
