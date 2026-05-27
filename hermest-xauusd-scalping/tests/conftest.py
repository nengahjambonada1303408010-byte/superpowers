import pandas as pd
import numpy as np
import pytest
from unittest.mock import MagicMock

from config.settings import Settings


@pytest.fixture
def settings():
    s = Settings()
    s.RISK_PCT_PER_TRADE = 1.0
    s.MAX_DAILY_LOSS_PCT = 3.0
    s.MAX_CONCURRENT_POSITIONS = 2
    s.ATR_PERIOD = 14
    s.ATR_SL_MULTIPLIER = 1.5
    s.RR_RATIO = 2.0
    s.COMPOUND_PROFIT = True
    s.LOOP_INTERVAL_SECONDS = 10
    return s


@pytest.fixture
def mock_ohlcv():
    n = 100
    close = 3250.0 + np.cumsum(np.random.randn(n) * 0.5)
    return pd.DataFrame({
        "time": pd.date_range("2024-01-01", periods=n, freq="5min"),
        "open": close - np.random.randn(n) * 0.2,
        "high": close + abs(np.random.randn(n) * 0.3),
        "low": close - abs(np.random.randn(n) * 0.3),
        "close": close,
        "volume": np.random.randint(100, 1000, n),
    })


@pytest.fixture
def mock_connector(mock_ohlcv):
    connector = MagicMock()
    connector.get_tick.return_value = {"bid": 3250.0, "ask": 3250.5, "spread": 0.5,
                                       "time": pd.Timestamp.utcnow()}
    connector.get_rates.return_value = mock_ohlcv
    connector.get_account_info.return_value = {"balance": 10000.0, "equity": 10000.0,
                                                "margin": 0.0, "free_margin": 10000.0, "profit": 0.0}
    connector.get_open_positions.return_value = []
    connector.place_market_order.return_value = MagicMock(success=True, ticket=123456, message="OK")
    connector.close_position.return_value = True
    return connector
