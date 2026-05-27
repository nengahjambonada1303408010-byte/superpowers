from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

import pandas as pd

from config.trading_params import (
    DEVIATION_POINTS,
    LOT_STEP,
    MAGIC_NUMBER,
    MAX_LOT,
    MIN_LOT,
    SYMBOL,
    TIMEFRAMES,
)
from utils.logger import logger

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    mt5 = None


class MT5ConnectionError(Exception):
    pass


@dataclass
class OrderResult:
    success: bool
    ticket: int = 0
    message: str = ""


class MT5Connector:
    def __init__(self):
        self._connected = False

    def connect(self, login: int, password: str, server: str) -> bool:
        if not MT5_AVAILABLE:
            logger.warning("MetaTrader5 not installed — running in mock mode")
            self._connected = True
            return True
        if not mt5.initialize(login=login, password=password, server=server):
            err = mt5.last_error()
            raise MT5ConnectionError(f"MT5 init failed: {err}")
        self._connected = True
        info = mt5.account_info()
        logger.info("MT5 connected: account=%s server=%s", info.login if info else login, server)
        return True

    def disconnect(self) -> None:
        if MT5_AVAILABLE and self._connected:
            mt5.shutdown()
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    # ── Market data ──────────────────────────────────────────────────────────

    def get_tick(self, symbol: str = SYMBOL) -> dict:
        if not MT5_AVAILABLE:
            return {"bid": 3250.0, "ask": 3250.5, "spread": 0.5, "time": pd.Timestamp.utcnow()}
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            raise MT5ConnectionError(f"Cannot get tick for {symbol}: {mt5.last_error()}")
        return {
            "bid": tick.bid,
            "ask": tick.ask,
            "spread": round(tick.ask - tick.bid, 5),
            "time": pd.Timestamp(tick.time, unit="s", tz="UTC"),
        }

    def get_rates(self, symbol: str = SYMBOL, timeframe_key: str = "M5", count: int = 200) -> pd.DataFrame:
        if not MT5_AVAILABLE:
            return self._mock_ohlcv(count)
        tf = TIMEFRAMES.get(timeframe_key, 5)
        rates = mt5.copy_rates_from_pos(symbol, tf, 0, count)
        if rates is None or len(rates) == 0:
            raise MT5ConnectionError(f"Cannot get rates {symbol}/{timeframe_key}: {mt5.last_error()}")
        df = pd.DataFrame(rates)
        df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
        df.rename(columns={"tick_volume": "volume"}, inplace=True)
        return df[["time", "open", "high", "low", "close", "volume"]].copy()

    def get_account_info(self) -> dict:
        if not MT5_AVAILABLE:
            return {"balance": 10000.0, "equity": 10000.0, "margin": 0.0, "free_margin": 10000.0, "profit": 0.0}
        info = mt5.account_info()
        if info is None:
            raise MT5ConnectionError(f"Cannot get account info: {mt5.last_error()}")
        return {
            "balance": info.balance,
            "equity": info.equity,
            "margin": info.margin,
            "free_margin": info.margin_free,
            "profit": info.profit,
        }

    def get_open_positions(self, symbol: str = SYMBOL) -> list[dict]:
        if not MT5_AVAILABLE:
            return []
        positions = mt5.positions_get(symbol=symbol)
        if positions is None:
            return []
        return [
            {
                "ticket": p.ticket,
                "type": p.type,
                "volume": p.volume,
                "price_open": p.price_open,
                "price_current": p.price_current,
                "sl": p.sl,
                "tp": p.tp,
                "profit": p.profit,
                "comment": p.comment,
                "time": pd.Timestamp(p.time, unit="s", tz="UTC"),
            }
            for p in positions
        ]

    def get_trade_history_today(self, symbol: str = SYMBOL) -> list[dict]:
        if not MT5_AVAILABLE:
            return []
        import datetime
        today = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0)
        deals = mt5.history_deals_get(today, datetime.datetime.utcnow(), group=f"*{symbol}*")
        if deals is None:
            return []
        return [
            {"ticket": d.ticket, "type": d.type, "volume": d.volume,
             "price": d.price, "profit": d.profit, "time": pd.Timestamp(d.time, unit="s", tz="UTC")}
            for d in deals
        ]

    def get_symbol_info(self, symbol: str = SYMBOL) -> dict:
        if not MT5_AVAILABLE:
            return {"point": 0.01, "trade_tick_size": 0.01, "trade_tick_value": 1.0,
                    "volume_min": 0.01, "volume_max": 10.0, "volume_step": 0.01}
        info = mt5.symbol_info(symbol)
        if info is None:
            raise MT5ConnectionError(f"Cannot get symbol info {symbol}: {mt5.last_error()}")
        return {
            "point": info.point,
            "trade_tick_size": info.trade_tick_size,
            "trade_tick_value": info.trade_tick_value,
            "volume_min": info.volume_min,
            "volume_max": info.volume_max,
            "volume_step": info.volume_step,
        }

    def get_pending_orders(self, symbol: str = SYMBOL) -> list[dict]:
        if not MT5_AVAILABLE:
            return []
        orders = mt5.orders_get(symbol=symbol)
        if orders is None:
            return []
        return [
            {"ticket": o.ticket, "type": o.type, "volume": o.volume_initial,
             "price": o.price_open, "sl": o.sl, "tp": o.tp}
            for o in orders
        ]

    # ── Order management ─────────────────────────────────────────────────────

    def place_market_order(self, symbol: str, order_type: str, volume: float,
                           sl: float, tp: float, comment: str = "GoldHouseAI") -> OrderResult:
        if not MT5_AVAILABLE:
            fake_ticket = 100000 + int(volume * 100)
            logger.info("MOCK %s %.2flot SL=%.2f TP=%.2f", order_type, volume, sl, tp)
            return OrderResult(success=True, ticket=fake_ticket, message="mock order")

        if not MT5_AVAILABLE or mt5 is None:
            return OrderResult(success=False, message="MT5 not available")

        ot = mt5.ORDER_TYPE_BUY if order_type.upper() == "BUY" else mt5.ORDER_TYPE_SELL
        tick = mt5.symbol_info_tick(symbol)
        price = tick.ask if ot == mt5.ORDER_TYPE_BUY else tick.bid

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": round(volume, 2),
            "type": ot,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": DEVIATION_POINTS,
            "magic": MAGIC_NUMBER,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        result = mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            return OrderResult(success=True, ticket=result.order, message="OK")
        return OrderResult(success=False, message=f"retcode={result.retcode} {result.comment}")

    def close_position(self, ticket: int) -> bool:
        if not MT5_AVAILABLE:
            logger.info("MOCK close ticket=%d", ticket)
            return True
        pos = mt5.positions_get(ticket=ticket)
        if not pos:
            return False
        p = pos[0]
        close_type = mt5.ORDER_TYPE_SELL if p.type == 0 else mt5.ORDER_TYPE_BUY
        tick = mt5.symbol_info_tick(p.symbol)
        price = tick.bid if close_type == mt5.ORDER_TYPE_SELL else tick.ask
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": p.symbol,
            "volume": p.volume,
            "type": close_type,
            "position": ticket,
            "price": price,
            "deviation": DEVIATION_POINTS,
            "magic": MAGIC_NUMBER,
            "comment": "GoldHouseAI-close",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        result = mt5.order_send(request)
        return result.retcode == mt5.TRADE_RETCODE_DONE

    def close_all_positions(self, symbol: str = SYMBOL) -> int:
        positions = self.get_open_positions(symbol)
        closed = 0
        for p in positions:
            if self.close_position(p["ticket"]):
                closed += 1
        return closed

    def modify_position(self, ticket: int, sl: float, tp: float) -> bool:
        if not MT5_AVAILABLE:
            return True
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": ticket,
            "sl": sl,
            "tp": tp,
        }
        result = mt5.order_send(request)
        return result.retcode == mt5.TRADE_RETCODE_DONE

    def place_pending_order(self, symbol: str, order_type: str, volume: float,
                            price: float, sl: float, tp: float) -> OrderResult:
        if not MT5_AVAILABLE:
            return OrderResult(success=True, ticket=200000, message="mock pending")
        type_map = {
            "BUY_LIMIT": mt5.ORDER_TYPE_BUY_LIMIT,
            "SELL_LIMIT": mt5.ORDER_TYPE_SELL_LIMIT,
            "BUY_STOP": mt5.ORDER_TYPE_BUY_STOP,
            "SELL_STOP": mt5.ORDER_TYPE_SELL_STOP,
        }
        ot = type_map.get(order_type.upper().replace(" ", "_"), mt5.ORDER_TYPE_BUY_LIMIT)
        request = {
            "action": mt5.TRADE_ACTION_PENDING,
            "symbol": symbol,
            "volume": round(volume, 2),
            "type": ot,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": DEVIATION_POINTS,
            "magic": MAGIC_NUMBER,
            "comment": "GoldHouseAI-pending",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_RETURN,
        }
        result = mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            return OrderResult(success=True, ticket=result.order, message="OK")
        return OrderResult(success=False, message=f"retcode={result.retcode}")

    def cancel_pending_order(self, ticket: int) -> bool:
        if not MT5_AVAILABLE:
            return True
        request = {"action": mt5.TRADE_ACTION_REMOVE, "order": ticket}
        result = mt5.order_send(request)
        return result.retcode == mt5.TRADE_RETCODE_DONE

    def set_trailing_stop(self, ticket: int, trail_points: float) -> bool:
        if not MT5_AVAILABLE:
            return True
        pos = mt5.positions_get(ticket=ticket)
        if not pos:
            return False
        p = pos[0]
        tick = mt5.symbol_info_tick(p.symbol)
        if p.type == 0:  # BUY
            new_sl = tick.bid - trail_points
            if new_sl > p.sl:
                return self.modify_position(ticket, sl=new_sl, tp=p.tp)
        else:  # SELL
            new_sl = tick.ask + trail_points
            if new_sl < p.sl or p.sl == 0:
                return self.modify_position(ticket, sl=new_sl, tp=p.tp)
        return False

    # ── Mock helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _mock_ohlcv(count: int) -> pd.DataFrame:
        import numpy as np
        times = pd.date_range(end=pd.Timestamp.utcnow(), periods=count, freq="5min", tz="UTC")
        close = 3250.0 + np.cumsum(np.random.randn(count) * 0.5)
        high = close + abs(np.random.randn(count) * 0.3)
        low = close - abs(np.random.randn(count) * 0.3)
        open_ = close - np.random.randn(count) * 0.2
        return pd.DataFrame({"time": times, "open": open_, "high": high, "low": low,
                              "close": close, "volume": np.random.randint(100, 1000, count)})
