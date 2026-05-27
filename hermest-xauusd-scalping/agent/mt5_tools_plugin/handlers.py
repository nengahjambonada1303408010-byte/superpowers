from __future__ import annotations

import json
import os
from pathlib import Path

from utils.logger import logger


def make_get_tick_handler(connector):
    def handler(**_kwargs):
        try:
            tick = connector.get_tick()
            return json.dumps({"bid": tick["bid"], "ask": tick["ask"], "spread": tick["spread"],
                               "time": str(tick["time"])})
        except Exception as e:
            return json.dumps({"error": str(e)})
    return handler


def make_get_ohlcv_handler(connector):
    def handler(timeframe: str = "M5", bars: int = 20, **_):
        try:
            df = connector.get_rates(timeframe_key=timeframe, count=int(bars))
            rows = []
            for _, row in df.tail(bars).iterrows():
                rows.append({"time": str(row["time"]), "open": row["open"], "high": row["high"],
                             "low": row["low"], "close": row["close"], "volume": int(row["volume"])})
            return json.dumps(rows)
        except Exception as e:
            return json.dumps({"error": str(e)})
    return handler


def make_get_account_handler(connector):
    def handler(**_):
        try:
            return json.dumps(connector.get_account_info())
        except Exception as e:
            return json.dumps({"error": str(e)})
    return handler


def make_get_positions_handler(connector):
    def handler(**_):
        try:
            positions = connector.get_open_positions()
            serializable = []
            for p in positions:
                p2 = dict(p)
                p2["time"] = str(p2.get("time", ""))
                serializable.append(p2)
            return json.dumps(serializable)
        except Exception as e:
            return json.dumps({"error": str(e)})
    return handler


def make_get_history_handler(connector):
    def handler(**_):
        try:
            history = connector.get_trade_history_today()
            for h in history:
                h["time"] = str(h.get("time", ""))
            return json.dumps(history)
        except Exception as e:
            return json.dumps({"error": str(e)})
    return handler


def make_get_symbol_info_handler(connector):
    def handler(**_):
        try:
            return json.dumps(connector.get_symbol_info())
        except Exception as e:
            return json.dumps({"error": str(e)})
    return handler


def make_place_buy_handler(connector, risk_manager):
    def handler(sl_price: float, tp_price: float = None, comment: str = "GoldHouseAI-BUY", **_):
        try:
            account = connector.get_account_info()
            tick = connector.get_tick()
            entry = tick["ask"]
            sl = float(sl_price)
            sl_distance = abs(entry - sl)
            lot = risk_manager.calculate_lot_size(account["equity"], sl_distance)
            if tp_price is None:
                tp = risk_manager.calculate_tp_price("BUY", entry, sl)
            else:
                tp = float(tp_price)
            result = connector.place_market_order(connector._settings_symbol if hasattr(connector, "_settings_symbol") else "XAUUSD",
                                                   "BUY", lot, sl, tp, comment)
            return json.dumps({"success": result.success, "ticket": result.ticket, "lot": lot,
                               "entry": entry, "sl": sl, "tp": tp, "message": result.message})
        except Exception as e:
            return json.dumps({"error": str(e)})
    return handler


def make_place_sell_handler(connector, risk_manager):
    def handler(sl_price: float, tp_price: float = None, comment: str = "GoldHouseAI-SELL", **_):
        try:
            account = connector.get_account_info()
            tick = connector.get_tick()
            entry = tick["bid"]
            sl = float(sl_price)
            sl_distance = abs(entry - sl)
            lot = risk_manager.calculate_lot_size(account["equity"], sl_distance)
            if tp_price is None:
                tp = risk_manager.calculate_tp_price("SELL", entry, sl)
            else:
                tp = float(tp_price)
            result = connector.place_market_order("XAUUSD", "SELL", lot, sl, tp, comment)
            return json.dumps({"success": result.success, "ticket": result.ticket, "lot": lot,
                               "entry": entry, "sl": sl, "tp": tp, "message": result.message})
        except Exception as e:
            return json.dumps({"error": str(e)})
    return handler


def make_pending_handler(connector, risk_manager, order_type: str):
    def handler(price: float, sl_price: float, tp_price: float = None, lot: float = 0.01, **_):
        try:
            tp = float(tp_price) if tp_price else 0.0
            result = connector.place_pending_order("XAUUSD", order_type, float(lot), float(price), float(sl_price), tp)
            return json.dumps({"success": result.success, "ticket": result.ticket, "message": result.message})
        except Exception as e:
            return json.dumps({"error": str(e)})
    return handler


def make_modify_position_handler(connector):
    def handler(ticket: int, sl_price: float, tp_price: float, **_):
        try:
            ok = connector.modify_position(int(ticket), float(sl_price), float(tp_price))
            return json.dumps({"success": ok})
        except Exception as e:
            return json.dumps({"error": str(e)})
    return handler


def make_close_position_handler(connector):
    def handler(ticket: int, **_):
        try:
            ok = connector.close_position(int(ticket))
            return json.dumps({"success": ok, "ticket": ticket})
        except Exception as e:
            return json.dumps({"error": str(e)})
    return handler


def make_close_all_handler(connector):
    def handler(**_):
        try:
            count = connector.close_all_positions()
            return json.dumps({"success": True, "closed_count": count})
        except Exception as e:
            return json.dumps({"error": str(e)})
    return handler


def make_cancel_pending_handler(connector):
    def handler(ticket: int, **_):
        try:
            ok = connector.cancel_pending_order(int(ticket))
            return json.dumps({"success": ok})
        except Exception as e:
            return json.dumps({"error": str(e)})
    return handler


def make_trailing_stop_handler(connector):
    def handler(ticket: int, trail_points: float, **_):
        try:
            ok = connector.set_trailing_stop(int(ticket), float(trail_points))
            return json.dumps({"success": ok})
        except Exception as e:
            return json.dumps({"error": str(e)})
    return handler


def make_create_skill_handler(skills_dir: Path):
    def handler(skill_name: str, content: str, **_):
        try:
            safe_name = "".join(c for c in skill_name if c.isalnum() or c in "-_")
            if not safe_name:
                return json.dumps({"error": "Invalid skill name"})
            path = skills_dir / f"{safe_name}.md"
            path.write_text(content, encoding="utf-8")
            logger.info("Hermes created new skill: %s", path)
            return json.dumps({"success": True, "path": str(path), "skill_name": safe_name})
        except Exception as e:
            return json.dumps({"error": str(e)})
    return handler
