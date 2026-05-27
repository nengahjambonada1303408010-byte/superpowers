from datetime import datetime, timezone


class SignalDeduplicator:
    def __init__(self, cooldown_seconds: int = 30):
        self._last_action: str = "HOLD"
        self._last_time: datetime | None = None
        self._cooldown = cooldown_seconds

    def is_duplicate(self, action: str) -> bool:
        if action == "HOLD":
            return False
        if self._last_action != action:
            return False
        if self._last_time is None:
            return False
        elapsed = (datetime.now(tz=timezone.utc) - self._last_time).total_seconds()
        return elapsed < self._cooldown

    def record(self, action: str) -> None:
        self._last_action = action
        self._last_time = datetime.now(tz=timezone.utc)
