# Skill: Trade Execution SOP

## Purpose
Standard Operating Procedure for opening, managing, and closing XAUUSD scalping trades.

## Entry Process
1. Risk assessment score >= 7 (or >= 5 for smaller size)
2. Confirm on M1 that price is moving in intended direction
3. Calculate lot size via RiskManager (equity-based, ATR SL)
4. Set SL FIRST, then TP — never enter without SL
5. Execute market order via `mt5_place_buy` or `mt5_place_sell`
6. Log: entry price, SL, TP, lot, reason, confidence score

## Position Management

### Trailing Stop
- After price moves 1× SL distance in profit direction:
  → Activate trailing stop at breakeven + 5 pts
- After price moves 2× SL distance:
  → Trail at 50% of distance gained

### Partial Close
- At TP1 (1× risk distance): Close 50% of position
- Let remaining 50% run with trailing stop to TP2 (2× risk)

### Stop Management
- Never move SL further away (against you) — capital protection is absolute
- May move SL to breakeven after reaching 1× profit

## Exit Conditions
| Condition | Action |
|-----------|--------|
| Price hits TP | Close remaining — profit booked |
| Price hits SL | Accept loss — SOP followed |
| RSI reverses sharply opposite | Consider early close at 50% |
| News spike | Close all immediately |
| End of NY session (17:00 GMT) | Close all open scalps |
| Daily loss limit approached | Close all, protect capital |

## After Trade
- Record: result (win/loss/breakeven), pips gained/lost, execution quality
- If winning pattern: note conditions for skill creation
- If 3 consecutive losses: trigger risk_assessment review
