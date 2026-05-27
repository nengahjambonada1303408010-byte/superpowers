import pytest
from risk.risk_manager import RiskManager


def test_lot_size_basic(settings):
    rm = RiskManager(settings)
    # SL=20 USD, tick_value=1: risk=$100, lot=100/20=5.0 (within range)
    lot = rm.calculate_lot_size(equity=10000, sl_points=20.0, tick_value=1.0)
    assert 0.01 <= lot <= 10.0
    expected = (10000 * 0.01) / (20.0 * 1.0)
    assert abs(lot - round(expected, 2)) < 0.05


def test_lot_size_minimum_clamp(settings):
    rm = RiskManager(settings)
    lot = rm.calculate_lot_size(equity=100, sl_points=100, tick_value=10.0)
    assert lot == 0.01


def test_sl_price_buy(settings):
    rm = RiskManager(settings)
    sl = rm.calculate_sl_price("BUY", entry_price=3250.0, atr=2.0)
    assert sl < 3250.0
    assert abs(sl - (3250.0 - 2.0 * 1.5)) < 0.001


def test_sl_price_sell(settings):
    rm = RiskManager(settings)
    sl = rm.calculate_sl_price("SELL", entry_price=3250.0, atr=2.0)
    assert sl > 3250.0


def test_tp_price_buy(settings):
    rm = RiskManager(settings)
    sl = rm.calculate_sl_price("BUY", 3250.0, 2.0)
    tp = rm.calculate_tp_price("BUY", 3250.0, sl)
    assert tp > 3250.0
    assert (tp - 3250.0) > (3250.0 - sl)


def test_daily_loss_exceeded(settings):
    rm = RiskManager(settings)
    assert rm.is_daily_loss_exceeded(daily_pnl=-310, balance=10000) is True
    assert rm.is_daily_loss_exceeded(daily_pnl=-100, balance=10000) is False


def test_max_positions(settings):
    rm = RiskManager(settings)
    assert rm.is_max_positions_reached([{}, {}]) is True
    assert rm.is_max_positions_reached([{}]) is False
    assert rm.is_max_positions_reached([]) is False


def test_compound_factor_increase(settings):
    rm = RiskManager(settings)
    initial = rm.compound_factor
    rm.adjust_compound_factor(daily_pnl_pct=5.0)
    assert rm.compound_factor > initial


def test_compound_factor_decrease(settings):
    rm = RiskManager(settings)
    rm.adjust_compound_factor(daily_pnl_pct=-3.0)
    assert rm.compound_factor < 1.0


def test_compound_factor_max_cap(settings):
    rm = RiskManager(settings)
    for _ in range(100):
        rm.adjust_compound_factor(daily_pnl_pct=10.0)
    assert rm.compound_factor <= 2.0
