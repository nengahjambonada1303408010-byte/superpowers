"""
Risk Manager - calculates lot sizes and enforces drawdown limits.
"""
import numpy as np
from loguru import logger

from core.mt5_connector import MT5Connector


class RiskManager:
    def __init__(self, config: dict, connector: MT5Connector):
        risk_cfg = config.get("risk", {})
        self.mode = risk_cfg.get("mode", "percent_balance")
        self.fixed_lot = risk_cfg.get("fixed_lot", 0.01)
        self.risk_percent = risk_cfg.get("risk_percent", 1.0) / 100.0
        self.max_daily_loss_pct = risk_cfg.get("max_daily_loss_percent", 5.0) / 100.0
        self.max_positions = risk_cfg.get("max_open_positions", 3)
        self.rr_ratio = risk_cfg.get("rr_ratio", 2.0)
        self.connector = connector
        self._daily_loss = 0.0
        self._daily_start_balance = None

    def calculate_lot(self, symbol: str, sl_distance_price: float) -> float:
        """
        Calculate position size based on risk management mode.
        sl_distance_price: absolute price distance to stop loss.
        """
        if self.mode == "fixed_lot":
            return self.fixed_lot

        account = self.connector.get_account_info()
        balance = account.get("balance", 10000.0)

        if self._daily_start_balance is None:
            self._daily_start_balance = balance

        if sl_distance_price <= 0:
            return self.fixed_lot

        symbol_info = self.connector.get_symbol_info(symbol)
        if symbol_info is None:
            return self.fixed_lot

        point = symbol_info.get("point", 0.00001)
        contract_size = symbol_info.get("trade_contract_size", 100000)
        volume_min = symbol_info.get("volume_min", 0.01)
        volume_step = symbol_info.get("volume_step", 0.01)

        # Risk amount in account currency
        risk_amount = balance * self.risk_percent

        # SL in points
        sl_points = sl_distance_price / point

        # Value per point per lot
        value_per_point = point * contract_size

        if value_per_point == 0 or sl_points == 0:
            return volume_min

        lot = risk_amount / (sl_points * value_per_point)

        # Round to valid lot step
        lot = max(volume_min, round(lot / volume_step) * volume_step)
        lot = min(lot, 100.0)  # hard cap

        return round(lot, 2)

    def can_open_trade(self, symbol: str) -> bool:
        """Check if we're allowed to open another trade."""
        open_positions = self.connector.get_open_positions()

        if len(open_positions) >= self.max_positions:
            logger.warning(f"Max positions ({self.max_positions}) reached")
            return False

        if self._is_daily_loss_limit_hit():
            logger.warning("Daily loss limit reached - no new trades")
            return False

        return True

    def update_daily_pnl(self, pnl: float):
        """Update running daily P&L."""
        self._daily_loss += min(0, pnl)

    def reset_daily(self):
        """Reset daily counters (call at start of new trading day)."""
        self._daily_loss = 0.0
        account = self.connector.get_account_info()
        self._daily_start_balance = account.get("balance", 10000.0)

    def _is_daily_loss_limit_hit(self) -> bool:
        if self._daily_start_balance is None or self._daily_start_balance == 0:
            return False
        daily_loss_pct = abs(self._daily_loss) / self._daily_start_balance
        return daily_loss_pct >= self.max_daily_loss_pct
