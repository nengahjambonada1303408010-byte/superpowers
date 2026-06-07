import sys
from pathlib import Path
from loguru import logger


def setup_logger(config: dict) -> None:
    log_cfg = config.get("logging", {})
    level = log_cfg.get("level", "INFO")
    log_file = log_cfg.get("file", "logs/trading_bot.log")
    rotation = log_cfg.get("rotation", "10 MB")
    retention = log_cfg.get("retention", "30 days")

    Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    logger.remove()
    logger.add(sys.stdout, level=level, colorize=True,
               format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>")
    logger.add(log_file, level=level, rotation=rotation, retention=retention,
               format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name} - {message}")


def get_logger(name: str):
    return logger.bind(name=name)
