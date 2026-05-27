import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class BotState:
    is_running: bool = False
    session_start_balance: float = 0.0
    daily_pnl: float = 0.0
    session_trade_count: int = 0
    consecutive_losses: int = 0
    last_action: str = "HOLD"
    last_decision_time: Optional[datetime] = None
    compound_factor: float = 1.0


class StateManager:
    def __init__(self):
        self._lock = threading.Lock()
        self._state = BotState()

    def get(self) -> BotState:
        with self._lock:
            return BotState(**self._state.__dict__)

    def update(self, **kwargs) -> None:
        with self._lock:
            for k, v in kwargs.items():
                if hasattr(self._state, k):
                    setattr(self._state, k, v)

    def increment_trade_count(self) -> None:
        with self._lock:
            self._state.session_trade_count += 1

    def record_loss(self) -> None:
        with self._lock:
            self._state.consecutive_losses += 1

    def reset_consecutive_losses(self) -> None:
        with self._lock:
            self._state.consecutive_losses = 0
