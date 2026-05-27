import logging
import os
from logging.handlers import RotatingFileHandler

os.makedirs("logs", exist_ok=True)


def setup_logger() -> logging.Logger:
    logger = logging.getLogger("gold_house_ai")
    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", "%Y-%m-%d %H:%M:%S")

    fh = RotatingFileHandler("logs/gold_house_ai.log", maxBytes=5 * 1024 * 1024, backupCount=3)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


logger = logging.getLogger("gold_house_ai")
