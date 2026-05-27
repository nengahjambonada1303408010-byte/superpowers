import pytest
from connectors.mt5_connector import MT5Connector


def test_mock_mode_connect():
    connector = MT5Connector()
    assert connector.connect(0, "demo", "Mock") is True
    assert connector.is_connected() is True


def test_mock_tick():
    connector = MT5Connector()
    connector.connect(0, "demo", "Mock")
    tick = connector.get_tick()
    assert "bid" in tick
    assert "ask" in tick
    assert tick["ask"] > tick["bid"]


def test_mock_ohlcv():
    connector = MT5Connector()
    connector.connect(0, "demo", "Mock")
    df = connector.get_rates(count=50)
    assert len(df) == 50
    assert set(["open", "high", "low", "close", "volume"]).issubset(df.columns)


def test_mock_account():
    connector = MT5Connector()
    connector.connect(0, "demo", "Mock")
    account = connector.get_account_info()
    assert account["balance"] > 0
    assert account["equity"] > 0


def test_mock_place_order():
    connector = MT5Connector()
    connector.connect(0, "demo", "Mock")
    result = connector.place_market_order("XAUUSD", "BUY", 0.01, 3240.0, 3270.0)
    assert result.success is True
    assert result.ticket > 0


def test_mock_close_position():
    connector = MT5Connector()
    connector.connect(0, "demo", "Mock")
    assert connector.close_position(123456) is True
