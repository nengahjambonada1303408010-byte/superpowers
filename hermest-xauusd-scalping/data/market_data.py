from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

import pandas as pd

from utils.indicators import latest_atr, latest_ema, latest_rsi


@dataclass
class MarketData:
    symbol: str
    timestamp: datetime
    bid: float
    ask: float
    spread: float
    m1_ohlcv: pd.DataFrame
    m5_ohlcv: pd.DataFrame
    atr_14: float
    ema_20: float
    rsi_14: float
    open_positions: list[dict] = field(default_factory=list)
    account_balance: float = 0.0
    account_equity: float = 0.0
    daily_pnl: float = 0.0


def build_market_data(connector, settings, session_start_balance: float = 0.0) -> MarketData:
    tick = connector.get_tick(settings.SYMBOL)
    m5 = connector.get_rates(settings.SYMBOL, "M5", 200)
    m1 = connector.get_rates(settings.SYMBOL, "M1", 60)
    account = connector.get_account_info()
    positions = connector.get_open_positions(settings.SYMBOL)

    atr_val = latest_atr(m5, settings.ATR_PERIOD)
    ema_val = latest_ema(m5, 20)
    rsi_val = latest_rsi(m5, 14)

    balance = account["balance"]
    equity = account["equity"]
    daily_pnl = equity - (session_start_balance if session_start_balance > 0 else balance)

    return MarketData(
        symbol=settings.SYMBOL,
        timestamp=tick["time"].to_pydatetime() if hasattr(tick["time"], "to_pydatetime") else tick["time"],
        bid=tick["bid"],
        ask=tick["ask"],
        spread=tick["spread"],
        m1_ohlcv=m1,
        m5_ohlcv=m5,
        atr_14=atr_val,
        ema_20=ema_val,
        rsi_14=rsi_val,
        open_positions=positions,
        account_balance=balance,
        account_equity=equity,
        daily_pnl=daily_pnl,
    )
