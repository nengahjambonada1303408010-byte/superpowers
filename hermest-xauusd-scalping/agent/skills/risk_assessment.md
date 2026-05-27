# Skill: Risk Assessment Protocol

## Purpose
Evaluate every potential trade for risk quality before execution. Protect capital first, profit second.

## Pre-Trade Checklist (all must pass)

| Check | Condition | Action if fail |
|-------|-----------|----------------|
| Daily loss limit | Daily PnL > -3% of balance | STOP trading today |
| Max positions | Open positions < 2 | HOLD until one closes |
| Spread | Spread < 30 pts | Wait for tighter spread |
| Volatility | ATR(14) > 1.5 | HOLD — market too quiet |
| Session | During London (08-12) or NY (13-17) GMT | Reduce size outside hours |

## Signal Quality Score
Rate each potential trade 1-10:
- +2: Aligns with higher timeframe trend (H1 EMA direction)
- +2: RSI at extreme (< 30 or > 70)
- +2: Clear S/R level nearby as entry point
- +2: London or NY session open (high liquidity)
- +1: Candle pattern confirms direction
- +1: Low spread (< 15 pts)
- -3: Against H1 trend
- -2: News expected within 30 minutes

Score >= 7: HIGH quality — full lot
Score 5-6: MEDIUM — 50% lot
Score < 5: Skip trade

## Position Risk Formula
- Risk per trade: 1% of current equity (not static balance)
- SL distance: 1.5 × ATR(14) in price units
- TP distance: SL × 2.0 (minimum 1:2 risk-reward)

## Emergency Protocols
- Consecutive losses (3 in a row): Pause 30 minutes, reassess
- Equity drop 5% from session start: Close all, stop for today
- News spike causing 50+ pt move in 1 minute: Close all, wait 15 minutes
