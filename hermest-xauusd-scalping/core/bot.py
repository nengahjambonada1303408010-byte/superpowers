from __future__ import annotations

import time
from datetime import datetime, timezone

from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot

from core.signal_dedup import SignalDeduplicator
from core.state_manager import StateManager
from data.market_data import build_market_data
from utils.logger import logger


class ScalpingBot(QObject):
    price_updated = pyqtSignal(float, float, float)        # bid, ask, spread
    candles_updated = pyqtSignal(object)                   # pd.DataFrame
    agent_decision = pyqtSignal(str, str, float)           # action, reasoning, confidence
    positions_updated = pyqtSignal(list)
    account_updated = pyqtSignal(float, float, float)      # balance, equity, daily_pnl
    error_occurred = pyqtSignal(str)
    status_changed = pyqtSignal(str)

    def __init__(self, settings, connector, agent, risk_manager):
        super().__init__()
        self._settings = settings
        self._connector = connector
        self._agent = agent
        self._risk_manager = risk_manager
        self._dedup = SignalDeduplicator(cooldown_seconds=30)
        self._state = StateManager()
        self._running = False
        self._session_start_balance = 0.0

    @pyqtSlot()
    def run(self):
        self._running = True
        self._state.update(is_running=True)

        try:
            account = self._connector.get_account_info()
            self._session_start_balance = account["balance"]
            self._state.update(session_start_balance=self._session_start_balance)
            logger.info("Bot started. Session balance: %.2f", self._session_start_balance)
        except Exception as e:
            self.error_occurred.emit(f"Failed to connect: {e}")
            return

        self.status_changed.emit("Running")

        while self._running:
            try:
                self._tick()
            except Exception as e:
                logger.exception("Bot tick error")
                self.error_occurred.emit(str(e))
            time.sleep(self._settings.LOOP_INTERVAL_SECONDS)

        self.status_changed.emit("Stopped")
        self._state.update(is_running=False)

    def _tick(self):
        md = build_market_data(self._connector, self._settings, self._session_start_balance)

        self.price_updated.emit(md.bid, md.ask, md.spread)
        self.candles_updated.emit(md.m5_ohlcv)
        self.account_updated.emit(md.account_balance, md.account_equity, md.daily_pnl)
        self.positions_updated.emit(md.open_positions)

        daily_pnl_pct = (md.daily_pnl / md.account_balance * 100) if md.account_balance > 0 else 0
        self._risk_manager.adjust_compound_factor(daily_pnl_pct)

        ok, reason = self._risk_manager.validate_trade(md)
        if not ok:
            self.status_changed.emit(f"Blocked: {reason}")
            return

        self.status_changed.emit("Consulting Hermes Agent...")
        decision = self._agent.analyze_and_act(md)

        if decision.action in ("BUY", "SELL") and self._dedup.is_duplicate(decision.action):
            self.status_changed.emit(f"Dedup: skipping repeated {decision.action}")
            return

        self._dedup.record(decision.action)
        self._state.update(last_action=decision.action,
                           last_decision_time=datetime.now(tz=timezone.utc))

        if decision.action == "CLOSE_ALL":
            count = self._connector.close_all_positions()
            logger.info("Hermes ordered CLOSE_ALL: %d positions closed", count)

        self.agent_decision.emit(decision.action, decision.reasoning, decision.confidence)
        self.status_changed.emit(f"Last: {decision.action} (conf={decision.confidence:.2f})")
        logger.info("Decision: %s | %s", decision.action, decision.reasoning[:100])

    @pyqtSlot()
    def stop(self):
        self._running = False
        logger.info("Bot stop requested")
