"""
Trade Logger - records all trades to CSV and SQLite for analysis.
"""
import csv
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger


class TradeLogger:
    def __init__(self, log_dir: str = "data"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.csv_path = self.log_dir / "trades.csv"
        self.db_path = self.log_dir / "trades.db"
        self._init_db()
        self._init_csv()

    def log_trade(self, trade: Dict):
        """Log a completed trade."""
        trade["logged_at"] = datetime.now(timezone.utc).isoformat()
        self._write_csv(trade)
        self._write_db(trade)

    def log_signal(self, signal: Dict):
        """Log a generated signal (even if not executed)."""
        signal["type"] = "signal"
        signal["logged_at"] = datetime.now(timezone.utc).isoformat()
        self._write_db_signal(signal)

    def get_recent_trades(self, n: int = 50, symbol: str = None) -> List[Dict]:
        """Retrieve recent trades from database."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            if symbol:
                rows = conn.execute(
                    "SELECT * FROM trades WHERE symbol=? ORDER BY entry_time DESC LIMIT ?",
                    (symbol, n)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM trades ORDER BY entry_time DESC LIMIT ?",
                    (n,)
                ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_statistics(self, symbol: str = None) -> Dict:
        """Compute summary statistics from trade history."""
        conn = sqlite3.connect(self.db_path)
        try:
            if symbol:
                rows = conn.execute(
                    "SELECT result, pnl_r FROM trades WHERE symbol=?", (symbol,)
                ).fetchall()
            else:
                rows = conn.execute("SELECT result, pnl_r FROM trades").fetchall()

            if not rows:
                return {"total": 0, "wins": 0, "losses": 0, "winrate": 0.0, "net_r": 0.0}

            total = len(rows)
            wins = sum(1 for r in rows if r[0] == "win")
            losses = sum(1 for r in rows if r[0] == "loss")
            net_r = sum(r[1] for r in rows)

            return {
                "total": total,
                "wins": wins,
                "losses": losses,
                "winrate": wins / total if total > 0 else 0.0,
                "net_r": net_r,
            }
        finally:
            conn.close()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                direction TEXT,
                entry_time TEXT,
                exit_time TEXT,
                entry_price REAL,
                exit_price REAL,
                sl_price REAL,
                tp_price REAL,
                lot REAL,
                result TEXT,
                pnl_r REAL,
                pnl_currency REAL,
                formula_id TEXT,
                ticket INTEGER,
                logged_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                direction TEXT,
                entry_price REAL,
                sl_price REAL,
                tp_price REAL,
                formula_id TEXT,
                executed INTEGER DEFAULT 0,
                logged_at TEXT
            )
        """)
        conn.commit()
        conn.close()

    def _init_csv(self):
        if not self.csv_path.exists():
            with open(self.csv_path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "symbol", "direction", "entry_time", "exit_time",
                    "entry_price", "exit_price", "sl_price", "tp_price",
                    "lot", "result", "pnl_r", "pnl_currency", "formula_id", "ticket"
                ])
                writer.writeheader()

    def _write_csv(self, trade: Dict):
        try:
            with open(self.csv_path, "a", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "symbol", "direction", "entry_time", "exit_time",
                    "entry_price", "exit_price", "sl_price", "tp_price",
                    "lot", "result", "pnl_r", "pnl_currency", "formula_id", "ticket"
                ], extrasaction="ignore")
                writer.writerow(trade)
        except Exception as e:
            logger.warning(f"CSV write failed: {e}")

    def _write_db(self, trade: Dict):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("""
                INSERT INTO trades (symbol, direction, entry_time, exit_time,
                    entry_price, exit_price, sl_price, tp_price, lot, result,
                    pnl_r, pnl_currency, formula_id, ticket, logged_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trade.get("symbol"), trade.get("direction"),
                str(trade.get("entry_time")), str(trade.get("exit_time")),
                trade.get("entry_price"), trade.get("exit_price"),
                trade.get("sl_price"), trade.get("tp_price"),
                trade.get("lot"), trade.get("result"),
                trade.get("pnl_r"), trade.get("pnl_currency"),
                trade.get("formula_id"), trade.get("ticket"),
                trade.get("logged_at"),
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"DB write failed: {e}")

    def _write_db_signal(self, signal: Dict):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("""
                INSERT INTO signals (symbol, direction, entry_price, sl_price, tp_price,
                    formula_id, executed, logged_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                signal.get("symbol"), signal.get("direction"),
                signal.get("entry_price"), signal.get("sl_price"),
                signal.get("tp_price"), signal.get("formula_id"),
                1 if signal.get("executed") else 0,
                signal.get("logged_at"),
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"Signal log failed: {e}")
