# Gold House AI — XAUUSD Scalping Bot

**AI-powered XAUUSD scalping application using Hermes Agent + Kimi AI**

## Architecture

```
Hermes Agent (NousResearch/hermes-agent)
  ├── Kimi AI (moonshot-v1-32k) — token-efficient LLM backend
  ├── MT5 Plugin (16 tools) — full MetaTrader 5 access
  └── 5 Built-in Skills — Gold House AI trading DNA
        ├── technical_analysis
        ├── risk_assessment
        ├── trade_execution
        ├── profit_compounding
        └── market_session
```

## Prerequisites

- **Windows 10/11** PC (MT5 Python library requires Windows)
- **MetaTrader 5** terminal installed and running
- **Python 3.11+**
- **Kimi AI API key** — register at [platform.moonshot.cn](https://platform.moonshot.cn)
- A **demo/live account** at an MT5 broker supporting XAUUSD (ICMarkets, Pepperstone, etc.)

## Installation

```bash
# 1. Clone or navigate to the project
cd hermest-xauusd-scalping

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # Linux/Mac

# 3. Install dependencies
pip install --upgrade pip
pip install MetaTrader5 PyQt5 pyqtgraph pandas numpy python-dotenv pyyaml openai
pip install git+https://github.com/NousResearch/hermes-agent.git

# 4. Configure
cp .env.example .env
# Edit .env with your credentials
```

## Configuration

Edit `.env`:

```env
KIMI_API_KEY=sk-your-kimi-api-key
HERMES_MODEL=moonshot-v1-32k

MT5_LOGIN=12345678
MT5_PASSWORD=your_password
MT5_SERVER=ICMarkets-Demo

RISK_PCT_PER_TRADE=1.0
MAX_DAILY_LOSS_PCT=3.0
```

## Running

```bash
# Normal mode (requires MT5 running)
python main.py

# Dry run (mock data, no MT5 required — for testing)
python main.py --dry-run
```

## Running Tests

```bash
pip install pytest
pytest tests/ -v
```

## How Hermes Agent Works Here

1. Every **10 seconds**, the bot collects:
   - XAUUSD real-time tick (bid/ask)
   - 200 M5 bars + 60 M1 bars
   - Technical indicators (ATR, EMA20, RSI14)
   - Open positions and account info

2. Data is **compressed to ~800 tokens** (hemat token Kimi AI) and sent to Hermes Agent

3. Hermes Agent reads its **5 skill files** and applies:
   - `technical_analysis`: Identify entry signals
   - `risk_assessment`: Score trade quality (1-10)
   - `market_session`: Check if it's London/NY prime time
   - `profit_compounding`: Size position based on equity compound

4. Hermes Agent can **call MT5 tools directly**:
   - `mt5_place_buy` / `mt5_place_sell` — open trades
   - `mt5_modify_position` — move SL to breakeven
   - `mt5_trailing_stop` — trail profits
   - `mt5_create_skill` — save new strategies it discovers

5. **GUI updates in real-time**: chart, positions, agent log, P&L

## Skill Manager

Hermes Agent can create new skills autonomously when it discovers profitable patterns.
View and manage skills in the **Skill Manager panel** on the right side of the GUI.

Manually created skills are marked with `*` in the list.

## Risk Management

| Parameter | Default | Description |
|-----------|---------|-------------|
| Risk/trade | 1% | % of current equity per trade |
| Max daily loss | 3% | Bot stops trading for the day |
| Max positions | 2 | Maximum concurrent open trades |
| SL distance | 1.5×ATR | Stop loss based on volatility |
| RR Ratio | 2.0 | Minimum risk:reward ratio |
| Compounding | ON | Lot size grows with equity |

## Disclaimer

> **This is an educational project. Trading XAUUSD carries significant financial risk.
> Always start with a DEMO account. Past performance does not guarantee future results.
> Never risk money you cannot afford to lose.**
