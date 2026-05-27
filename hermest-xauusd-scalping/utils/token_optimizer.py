import pandas as pd
from datetime import datetime


def format_ohlcv_compact(df: pd.DataFrame) -> str:
    rows = []
    for _, row in df.iterrows():
        t = pd.Timestamp(row.get("time", row.name)).strftime("%H:%M")
        rows.append(f"{t},{row['open']:.2f},{row['high']:.2f},{row['low']:.2f},{row['close']:.2f}")
    return "\n".join(rows)


def build_compact_market_context(md, settings) -> str:
    pos_summary = ""
    if md.open_positions:
        pos_lines = []
        for p in md.open_positions:
            side = "B" if p.get("type") == 0 else "S"
            pos_lines.append(
                f"  #{p['ticket']} {side} {p['volume']}lot @{p['price_open']:.2f} "
                f"SL:{p['sl']:.2f} TP:{p['tp']:.2f} P&L:{p['profit']:.1f}"
            )
        pos_summary = "OpenPos:\n" + "\n".join(pos_lines)
    else:
        pos_summary = "OpenPos: none"

    compact_ohlcv = format_ohlcv_compact(md.m5_ohlcv.tail(20))

    lines = [
        f"XAUUSD {md.timestamp.strftime('%H:%M')} GMT Bid:{md.bid:.2f} Ask:{md.ask:.2f} Spread:{md.spread:.1f}pts",
        f"ATR14:{md.atr_14:.2f} EMA20:{md.ema_20:.2f} RSI14:{md.rsi_14:.1f}",
        f"Bal:{md.account_balance:.0f} Eq:{md.account_equity:.0f} DayPnL:{md.daily_pnl:.1f}",
        f"MaxPos:{settings.MAX_CONCURRENT_POSITIONS} RiskPct:{settings.RISK_PCT_PER_TRADE}%",
        pos_summary,
        "M5_OHLCV(T,O,H,L,C last20):",
        compact_ohlcv,
        "",
        "You are Gold House AI chief scalping strategist. Analyze XAUUSD and decide:",
        "ACTION: BUY | SELL | HOLD | CLOSE_ALL",
        "Use available MT5 tools if needed. Reply with ACTION on last line.",
    ]
    return "\n".join(lines)
