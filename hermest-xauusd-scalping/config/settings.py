import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    KIMI_API_KEY: str = field(default_factory=lambda: os.getenv("KIMI_API_KEY", ""))
    KIMI_BASE_URL: str = "https://api.moonshot.cn/v1"
    HERMES_MODEL: str = field(default_factory=lambda: os.getenv("HERMES_MODEL", "moonshot-v1-32k"))

    MT5_LOGIN: int = field(default_factory=lambda: int(os.getenv("MT5_LOGIN", "0")))
    MT5_PASSWORD: str = field(default_factory=lambda: os.getenv("MT5_PASSWORD", ""))
    MT5_SERVER: str = field(default_factory=lambda: os.getenv("MT5_SERVER", ""))

    RISK_PCT_PER_TRADE: float = field(default_factory=lambda: float(os.getenv("RISK_PCT_PER_TRADE", "1.0")))
    MAX_DAILY_LOSS_PCT: float = field(default_factory=lambda: float(os.getenv("MAX_DAILY_LOSS_PCT", "3.0")))
    MAX_CONCURRENT_POSITIONS: int = field(default_factory=lambda: int(os.getenv("MAX_CONCURRENT_POSITIONS", "2")))
    ATR_PERIOD: int = field(default_factory=lambda: int(os.getenv("ATR_PERIOD", "14")))
    ATR_SL_MULTIPLIER: float = field(default_factory=lambda: float(os.getenv("ATR_SL_MULTIPLIER", "1.5")))
    RR_RATIO: float = field(default_factory=lambda: float(os.getenv("RR_RATIO", "2.0")))
    COMPOUND_PROFIT: bool = field(default_factory=lambda: os.getenv("COMPOUND_PROFIT", "true").lower() == "true")

    LOOP_INTERVAL_SECONDS: int = field(default_factory=lambda: int(os.getenv("LOOP_INTERVAL_SECONDS", "10")))
    SYMBOL: str = field(default_factory=lambda: os.getenv("SYMBOL", "XAUUSD"))

    @classmethod
    def from_env(cls) -> "Settings":
        return cls()
