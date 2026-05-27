from __future__ import annotations

import math

from config.trading_params import MAX_SPREAD_POINTS, MIN_ATR
from utils.logger import logger


class RiskManager:
    def __init__(self, settings):
        self._settings = settings
        self._compound_factor: float = 1.0

    # ── Position sizing ───────────────────────────────────────────────────────

    def calculate_lot_size(self, equity: float, sl_points: float, tick_value: float = 1.0) -> float:
        if sl_points <= 0 or tick_value <= 0:
            return 0.01

        risk_pct = self._settings.RISK_PCT_PER_TRADE * self._compound_factor
        risk_amount = equity * (risk_pct / 100.0)
        raw_lot = risk_amount / (sl_points * tick_value)
        return self._clamp_lot(raw_lot)

    def _clamp_lot(self, lot: float) -> float:
        step = 0.01
        clamped = max(0.01, min(lot, 10.0))
        return round(math.floor(clamped / step) * step, 2)

    # ── SL / TP ───────────────────────────────────────────────────────────────

    def calculate_sl_price(self, side: str, entry_price: float, atr: float) -> float:
        distance = atr * self._settings.ATR_SL_MULTIPLIER
        return entry_price - distance if side.upper() == "BUY" else entry_price + distance

    def calculate_tp_price(self, side: str, entry_price: float, sl_price: float) -> float:
        sl_distance = abs(entry_price - sl_price)
        tp_distance = sl_distance * self._settings.RR_RATIO
        return entry_price + tp_distance if side.upper() == "BUY" else entry_price - tp_distance

    # ── Guards ────────────────────────────────────────────────────────────────

    def is_daily_loss_exceeded(self, daily_pnl: float, balance: float) -> bool:
        if balance <= 0:
            return True
        loss_pct = (-daily_pnl / balance) * 100
        return loss_pct >= self._settings.MAX_DAILY_LOSS_PCT

    def is_max_positions_reached(self, open_positions: list) -> bool:
        return len(open_positions) >= self._settings.MAX_CONCURRENT_POSITIONS

    def validate_trade(self, market_data) -> tuple[bool, str]:
        if self.is_daily_loss_exceeded(market_data.daily_pnl, market_data.account_balance):
            return False, f"Daily loss limit reached ({self._settings.MAX_DAILY_LOSS_PCT}%)"

        if self.is_max_positions_reached(market_data.open_positions):
            return False, f"Max positions reached ({self._settings.MAX_CONCURRENT_POSITIONS})"

        spread_pts = market_data.spread / 0.01
        if spread_pts > MAX_SPREAD_POINTS:
            return False, f"Spread too wide ({spread_pts:.0f} pts > {MAX_SPREAD_POINTS})"

        if market_data.atr_14 < MIN_ATR:
            return False, f"ATR too low ({market_data.atr_14:.2f} < {MIN_ATR}) — market too quiet"

        return True, "OK"

    # ── Profit compounding ────────────────────────────────────────────────────

    def adjust_compound_factor(self, daily_pnl_pct: float) -> None:
        if not self._settings.COMPOUND_PROFIT:
            return
        if daily_pnl_pct >= 3.0:
            self._compound_factor = min(self._compound_factor * 1.1, 2.0)
            logger.info("Compound factor increased to %.2f", self._compound_factor)
        elif daily_pnl_pct <= -2.0:
            self._compound_factor = max(self._compound_factor * 0.8, 0.5)
            logger.info("Compound factor decreased to %.2f", self._compound_factor)

    @property
    def compound_factor(self) -> float:
        return self._compound_factor
