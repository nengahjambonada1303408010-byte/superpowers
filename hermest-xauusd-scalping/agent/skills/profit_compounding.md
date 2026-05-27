# Skill: Profit Compounding Strategy

## Purpose
Systematically grow account balance by increasing position size as equity grows, while protecting gains during drawdowns.

## Compounding Philosophy
"Let winners run the account. Let losers teach, not destroy."

## Compound Factor System

| Daily PnL | Compound Factor Change | Next Day Lot Multiplier |
|-----------|------------------------|-------------------------|
| >= +5% | +15% factor | Up to 2.0× base lot |
| >= +3% | +10% factor | Moderate increase |
| +1% to +3% | No change | Maintain current |
| -1% to +1% | No change | Maintain current |
| -2% to -1% | -10% factor | Slight reduction |
| <= -3% | -20% factor | Significant reduction |

## Lot Calculation (Compound Mode)
```
risk_amount = current_equity × (risk_pct × compound_factor / 100)
lot_size = risk_amount / (sl_distance_in_price × contract_size)
```

## Weekly Review Protocol
Every Monday:
1. Calculate week's net PnL %
2. If >= +10%: Celebrate, maintain compound factor
3. If >= +20%: Consider withdrawing 30% profits, reset compound
4. If <= -5%: Reset compound factor to 0.8, review strategy

## Monthly Targets
- Conservative: 8-12% ROI
- Moderate: 12-18% ROI
- Aggressive: 18-25% ROI (higher drawdown risk)

## Compounding Schedule Example (starting $1,000)
| Month | Balance | Lot Size | Target Return |
|-------|---------|----------|---------------|
| 1 | $1,000 | 0.01 | +15% → $1,150 |
| 2 | $1,150 | 0.012 | +15% → $1,322 |
| 3 | $1,322 | 0.014 | +15% → $1,520 |
| 6 | $2,313 | 0.023 | +15% → $2,660 |
| 12 | $4,652 | 0.047 | +15% → $5,350 |

## Capital Protection Rules
- Never risk more than 2% per trade regardless of compound factor
- If compound factor reaches 2.0×, cap it there
- If 5 consecutive losses: reset compound factor to 0.5 for 1 day
- Monthly max drawdown: 10% of month-start balance → stop for month
