# Skill: Technical Analysis — XAUUSD Scalping

## Purpose
Analyze XAUUSD (Gold/USD) price action using technical indicators to identify high-probability scalping entries.

## Primary Indicators
- **EMA 20** (M5): Trend direction filter. Price above EMA = bullish bias; below = bearish bias.
- **RSI 14** (M5): Momentum. Below 35 = oversold (BUY zone). Above 65 = overbought (SELL zone).
- **ATR 14** (M5): Volatility filter. Trade only when ATR > 2.0. Higher ATR = larger SL/TP.

## Entry Criteria

### BUY Signal
1. Price pulls back to EMA 20 from above (retest)
2. RSI crosses up from below 40
3. Previous candle is a bullish engulfing or hammer on M5
4. Spread < 30 pts

### SELL Signal
1. Price rejects EMA 20 from below
2. RSI crosses down from above 60
3. Previous candle is a bearish engulfing or shooting star on M5
4. Spread < 30 pts

## Confidence Score (1-10)
- Score 7+: Execute trade
- Score 4-6: Wait for confirmation
- Score 1-3: HOLD

## Market Structure Notes
- XAUUSD respects round numbers (3200, 3250, 3300) as S/R
- Asian session forms the range; London breaks it
- Avoid entries 5 minutes before/after major economic news
