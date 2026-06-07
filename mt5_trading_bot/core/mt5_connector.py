"""
MT5 Connector - handles all MetaTrader 5 interactions.
MetaTrader5 package only works on Windows with MT5 terminal running.
"""
import time
from datetime import datetime, timezone
from typing import Optional, List, Dict

import numpy as np
import pandas as pd
from loguru import logger

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    logger.warning("MetaTrader5 package not available - running in mock mode")

TIMEFRAME_MAP = {
    "M1":  1,
    "M5":  5,
    "M15": 15,
    "M30": 30,
    "H1":  16385,
    "H4":  16388,
    "D1":  16408,
    "W1":  32769,
    "MN1": 49153,
}


class MT5Connector:
    def __init__(self, config: dict):
        self.config = config.get("mt5", {})
        self._connected = False

    def initialize(self) -> bool:
        if not MT5_AVAILABLE:
            logger.warning("MT5 not available, using mock mode")
            self._connected = False
            return False

        path = self.config.get("path", "")
        kwargs = {}
        if path:
            kwargs["path"] = path

        login = self.config.get("login")
        password = self.config.get("password", "")
        server = self.config.get("server", "")

        if login and str(login) != "12345678":
            kwargs.update({"login": int(login), "password": str(password), "server": str(server)})

        if not mt5.initialize(**kwargs):
            logger.error(f"MT5 initialize failed: {mt5.last_error()}")
            return False

        info = mt5.terminal_info()
        logger.info(f"MT5 connected: {info.name} build {info.build}")
        self._connected = True
        return True

    def shutdown(self):
        if MT5_AVAILABLE and self._connected:
            mt5.shutdown()
            self._connected = False
            logger.info("MT5 connection closed")

    def is_connected(self) -> bool:
        if not MT5_AVAILABLE or not self._connected:
            return False
        return mt5.terminal_info() is not None

    def fetch_rates(self, symbol: str, timeframe: str, n_candles: int = 65000) -> Optional[pd.DataFrame]:
        if not MT5_AVAILABLE or not self._connected:
            return self._mock_rates(symbol, n_candles)

        tf = TIMEFRAME_MAP.get(timeframe)
        if tf is None:
            raise ValueError(f"Unknown timeframe: {timeframe}")

        rates = mt5.copy_rates_from_pos(symbol, tf, 0, n_candles)
        if rates is None or len(rates) == 0:
            logger.error(f"Failed to fetch {symbol} {timeframe}: {mt5.last_error()}")
            return None

        return self._rates_to_df(rates)

    def fetch_rates_range(self, symbol: str, timeframe: str,
                          date_from: datetime, date_to: datetime) -> Optional[pd.DataFrame]:
        if not MT5_AVAILABLE or not self._connected:
            n = int((date_to - date_from).total_seconds() / 3600)
            return self._mock_rates(symbol, max(n, 100))

        tf = TIMEFRAME_MAP.get(timeframe)
        if tf is None:
            raise ValueError(f"Unknown timeframe: {timeframe}")

        rates = mt5.copy_rates_range(symbol, tf, date_from, date_to)
        if rates is None or len(rates) == 0:
            logger.error(f"Failed to fetch range {symbol}: {mt5.last_error()}")
            return None

        return self._rates_to_df(rates)

    def get_tick(self, symbol: str) -> Optional[Dict]:
        if not MT5_AVAILABLE or not self._connected:
            return {"bid": 1.1000, "ask": 1.1001, "time": datetime.now(timezone.utc)}

        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return None
        return {"bid": tick.bid, "ask": tick.ask, "time": datetime.fromtimestamp(tick.time, tz=timezone.utc)}

    def send_order(self, symbol: str, order_type: str, lot: float,
                   sl_price: float, tp_price: float, comment: str = "MT5Bot") -> Optional[Dict]:
        if not MT5_AVAILABLE or not self._connected:
            logger.warning(f"Mock order: {order_type} {symbol} {lot} lots")
            return {"retcode": 10009, "order": 999999, "comment": "mock"}

        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            logger.error(f"Cannot get tick for {symbol}")
            return None

        if order_type.upper() == "BUY":
            price = tick.ask
            mt5_type = mt5.ORDER_TYPE_BUY
        else:
            price = tick.bid
            mt5_type = mt5.ORDER_TYPE_SELL

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(lot),
            "type": mt5_type,
            "price": price,
            "sl": sl_price,
            "tp": tp_price,
            "deviation": 20,
            "magic": 202601,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"Order failed: {result.retcode} - {result.comment}")
            return None

        logger.info(f"Order sent: {order_type} {symbol} {lot} @ {price}, ticket={result.order}")
        return {"retcode": result.retcode, "order": result.order, "price": result.price, "comment": result.comment}

    def close_position(self, ticket: int) -> bool:
        if not MT5_AVAILABLE or not self._connected:
            logger.warning(f"Mock close position ticket={ticket}")
            return True

        positions = mt5.positions_get(ticket=ticket)
        if not positions:
            logger.error(f"Position {ticket} not found")
            return False

        pos = positions[0]
        tick = mt5.symbol_info_tick(pos.symbol)
        if tick is None:
            return False

        if pos.type == mt5.ORDER_TYPE_BUY:
            price = tick.bid
            close_type = mt5.ORDER_TYPE_SELL
        else:
            price = tick.ask
            close_type = mt5.ORDER_TYPE_BUY

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": pos.symbol,
            "volume": pos.volume,
            "type": close_type,
            "position": ticket,
            "price": price,
            "deviation": 20,
            "magic": 202601,
            "comment": "close",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"Close failed: {result.retcode}")
            return False

        logger.info(f"Position {ticket} closed")
        return True

    def get_account_info(self) -> Dict:
        if not MT5_AVAILABLE or not self._connected:
            return {"balance": 10000.0, "equity": 10000.0, "margin": 0.0, "free_margin": 10000.0, "profit": 0.0}

        info = mt5.account_info()
        if info is None:
            return {}
        return {
            "balance": info.balance,
            "equity": info.equity,
            "margin": info.margin,
            "free_margin": info.margin_free,
            "profit": info.profit,
            "currency": info.currency,
            "leverage": info.leverage,
        }

    def get_open_positions(self, symbol: str = None) -> List[Dict]:
        if not MT5_AVAILABLE or not self._connected:
            return []

        if symbol:
            positions = mt5.positions_get(symbol=symbol)
        else:
            positions = mt5.positions_get()

        if positions is None:
            return []

        return [
            {
                "ticket": p.ticket,
                "symbol": p.symbol,
                "type": "buy" if p.type == 0 else "sell",
                "volume": p.volume,
                "open_price": p.price_open,
                "sl": p.sl,
                "tp": p.tp,
                "profit": p.profit,
                "open_time": datetime.fromtimestamp(p.time, tz=timezone.utc),
            }
            for p in positions
        ]

    def get_symbol_info(self, symbol: str) -> Optional[Dict]:
        if not MT5_AVAILABLE or not self._connected:
            return {"point": 0.00001, "digits": 5, "trade_contract_size": 100000}

        info = mt5.symbol_info(symbol)
        if info is None:
            return None
        return {
            "point": info.point,
            "digits": info.digits,
            "trade_contract_size": info.trade_contract_size,
            "volume_min": info.volume_min,
            "volume_step": info.volume_step,
        }

    @staticmethod
    def _rates_to_df(rates) -> pd.DataFrame:
        df = pd.DataFrame(rates)
        df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
        df.set_index("time", inplace=True)
        df.rename(columns={"tick_volume": "volume"}, inplace=True)
        return df[["open", "high", "low", "close", "volume"]].astype(float)

    @staticmethod
    def _mock_rates(symbol: str, n: int) -> pd.DataFrame:
        np.random.seed(abs(hash(symbol)) % (2**31))
        close = 1.1 + np.cumsum(np.random.randn(n) * 0.0002)
        close = np.abs(close) + 0.5
        high = close + np.abs(np.random.randn(n) * 0.0003)
        low = close - np.abs(np.random.randn(n) * 0.0003)
        open_ = close + np.random.randn(n) * 0.0001
        volume = np.random.randint(100, 10000, n).astype(float)
        idx = pd.date_range(end=pd.Timestamp.now(tz="UTC"), periods=n, freq="h")
        return pd.DataFrame({
            "open": open_, "high": high, "low": low,
            "close": close, "volume": volume,
        }, index=idx)
