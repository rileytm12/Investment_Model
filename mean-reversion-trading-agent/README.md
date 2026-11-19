# Autonomous Mean Reversion Trading Agent

## Overview
An automated paper-trading workflow implementing a 60-day mean reversion strategy for zero-commission equities, using Gemini for structured trade evaluation and Alpaca for execution.

## Setup Instructions

### 1. Account & API Keys
- **Alpaca:** Create an Alpaca account and generate **Paper Trading** API keys (Key ID and Secret).
- **Gemini:** Create a Gemini API key in Google AI Studio.

### 2. Repository & Secrets Setup
1. Upload these files to a GitHub repository keeping the exact folder layout.
2. In GitHub, go to **Settings > Secrets and variables > Actions** and add:
   - `GEMINI_API_KEY`
   - `ALPACA_KEY`
   - `ALPACA_SECRET`
3. For local testing, copy `.env.example` to `.env` and fill in your keys (`.env` is ignored by Git).

### 3. Schedule (GitHub Actions)
`.github/workflows/trading_agent.yml` runs `main.py` every 30 minutes (`*/30 * * * *`) and can also be triggered manually from the **Actions** tab.

## Strategy Parameters (`src/agent/config.py`)
- **Profit Target:** `1.5%` (`PROFIT_TARGET_PCT = 0.015`)
- **Holding Limit:** `48` hours (`HOLDING_LIMIT_HOURS = 48`)
- **Zero-Commission Universe:** Enforced via `ZERO_COMMISSION_UNIVERSE` in `executor.py`
