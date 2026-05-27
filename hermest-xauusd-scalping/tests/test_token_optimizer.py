import pandas as pd
import numpy as np
import pytest
from datetime import datetime
from unittest.mock import MagicMock

from utils.token_optimizer import build_compact_market_context, format_ohlcv_compact
from data.market_data import MarketData


def make_mock_md():
    n = 30
    close = 3250.0 + np.cumsum(np.random.randn(n) * 0.5)
    df = pd.DataFrame({
        "time": pd.date_range("2024-01-01", periods=n, freq="5min"),
        "open": close - 0.1,
        "high": close + 0.2,
        "low": close - 0.2,
        "close": close,
        "volume": np.ones(n) * 100,
    })
    return MarketData(
        symbol="XAUUSD",
        timestamp=datetime.utcnow(),
        bid=3250.0,
        ask=3250.5,
        spread=0.5,
        m1_ohlcv=df,
        m5_ohlcv=df,
        atr_14=2.5,
        ema_20=3248.0,
        rsi_14=55.0,
        open_positions=[],
        account_balance=10000.0,
        account_equity=10050.0,
        daily_pnl=50.0,
    )


def make_settings():
    s = MagicMock()
    s.RISK_PCT_PER_TRADE = 1.0
    s.MAX_CONCURRENT_POSITIONS = 2
    return s


def test_compact_context_contains_key_fields():
    md = make_mock_md()
    settings = make_settings()
    text = build_compact_market_context(md, settings)
    assert "XAUUSD" in text
    assert "Bid:" in text
    assert "ATR" in text
    assert "RSI" in text
    assert "ACTION" in text


def test_compact_context_token_efficiency():
    md = make_mock_md()
    settings = make_settings()
    text = build_compact_market_context(md, settings)
    word_count = len(text.split())
    assert word_count < 800, f"Context too verbose: {word_count} words"


def test_format_ohlcv_compact_rows():
    n = 20
    close = 3250.0 + np.zeros(n)
    df = pd.DataFrame({
        "time": pd.date_range("2024-01-01", periods=n, freq="5min"),
        "open": close,
        "high": close + 0.1,
        "low": close - 0.1,
        "close": close,
        "volume": np.ones(n),
    })
    result = format_ohlcv_compact(df)
    lines = result.strip().splitlines()
    assert len(lines) == n
    assert "," in lines[0]
