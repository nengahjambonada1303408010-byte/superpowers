"""
Live Trader - executes trades in real-time using trained formulas.
Supports Auto mode (execute immediately) and Manual mode (wait for user confirmation).
"""
import time
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional, Callable

import pandas as pd
import numpy as np
from loguru import logger

from core.mt5_connector import MT5Connector
from core.data_manager import DataManager
from core.formula_engine import FormulaEngine
from core.backtest_engine import BacktestEngine
from core.training_manager import TrainingManager
from core.indicators import atr
from trading.risk_manager import RiskManager
from trading.trade_logger import TradeLogger


class TradeSignal:
    def __init__(self, symbol: str, direction: str, entry: float,
                 sl: float, tp: float, formula_id: str, winrate: float):
        self.symbol = symbol
        self.direction = direction
        self.entry = entry
        self.sl = sl
        self.tp = tp
        self.formula_id = formula_id
        self.winrate = winrate
        self.sl_distance = abs(entry - sl)
        self.tp_distance = abs(tp - entry)
        self.rr = self.tp_distance / self.sl_distance if self.sl_distance > 0 else 0
        self.time = datetime.now(timezone.utc)


class LiveTrader:
    def __init__(self, config: dict, connector: MT5Connector):
        self.config = config
        self.connector = connector
        live_cfg = config.get("live_trading", {})
        self.mode = live_cfg.get("default_mode", "manual")
        self.check_interval = live_cfg.get("check_interval_seconds", 5)
        self.min_formula_winrate = live_cfg.get("min_formula_winrate", 0.75)

        self.data_manager = DataManager(connector)
        self.formula_engine = FormulaEngine(config)
        self.backtest_engine = BacktestEngine(rr_ratio=config.get("risk", {}).get("rr_ratio", 2.0))
        self.risk_manager = RiskManager(config, connector)
        self.trade_logger = TradeLogger()
        self.training_manager = TrainingManager(config, connector)

        self._active_formulas: Dict[str, Dict] = {}
        self._formula_winrates: Dict[str, float] = {}
        self._running = False
        self._stop_flag = threading.Event()
        self._pending_signals: List[TradeSignal] = []
        self._lock = threading.Lock()

        # GUI callbacks
        self.on_signal: Optional[Callable] = None        # called when signal detected
        self.on_trade_opened: Optional[Callable] = None  # called when trade opens
        self.on_trade_closed: Optional[Callable] = None  # called when trade closes
        self.on_error: Optional[Callable] = None         # called on error

    def set_mode(self, mode: str):
        """Switch between 'auto' and 'manual' mode."""
        assert mode in ("auto", "manual")
        self.mode = mode
        logger.info(f"Trading mode set to: {mode}")

    def load_formulas(self, symbols: List[str]) -> int:
        """Load best trained formula for each symbol. Returns count loaded."""
        loaded = 0
        for symbol in symbols:
            formula = self.training_manager.load_best_formula(symbol)
            if formula:
                self._active_formulas[symbol] = formula
                # Estimate winrate from last backtest
                tf_entry = self.config.get("training", {}).get("timeframe_entry", "M15")
                tf_htf = self.config.get("training", {}).get("timeframe_htf", "H1")
                df = self.data_manager.fetch_and_cache(symbol, tf_entry, 1)
                df_htf = self.data_manager.fetch_and_cache(symbol, tf_htf, 1)
                if df is not None:
                    result = self.backtest_engine.run(df, df_htf, formula, self.formula_engine)
                    self._formula_winrates[symbol] = result.winrate
                else:
                    self._formula_winrates[symbol] = 0.0
                loaded += 1
                logger.info(f"Loaded formula for {symbol}: "
                            f"wr={self._formula_winrates[symbol]:.1%}")
            else:
                logger.warning(f"No formula found for {symbol} - skipping")
        return loaded

    def start(self, symbols: List[str] = None):
        """Start live trading loop in a background thread."""
        if self._running:
            logger.warning("Live trader already running")
            return

        if symbols:
            self.load_formulas(symbols)

        if not self._active_formulas:
            logger.error("No formulas loaded. Train the bot first.")
            return

        self._stop_flag.clear()
        self._running = True
        thread = threading.Thread(target=self._trading_loop, daemon=True)
        thread.start()
        logger.info(f"Live trading started (mode={self.mode}): {list(self._active_formulas.keys())}")

    def stop(self):
        """Stop the trading loop."""
        self._stop_flag.set()
        self._running = False
        logger.info("Live trading stopped")

    def confirm_signal(self, signal: TradeSignal):
        """Manually confirm and execute a pending signal (manual mode)."""
        with self._lock:
            if signal in self._pending_signals:
                self._pending_signals.remove(signal)
        self._execute_trade(signal)

    def reject_signal(self, signal: TradeSignal):
        """Reject a pending signal (manual mode)."""
        with self._lock:
            if signal in self._pending_signals:
                self._pending_signals.remove(signal)
        logger.info(f"Signal rejected by user: {signal.direction} {signal.symbol}")
        self.trade_logger.log_signal({
            "symbol": signal.symbol,
            "direction": signal.direction,
            "entry_price": signal.entry,
            "sl_price": signal.sl,
            "tp_price": signal.tp,
            "formula_id": signal.formula_id,
            "executed": False,
        })

    def is_running(self) -> bool:
        return self._running

    def get_pending_signals(self) -> List[TradeSignal]:
        with self._lock:
            return list(self._pending_signals)

    def _trading_loop(self):
        """Main loop: check signals every candle close."""
        tf_entry = self.config.get("training", {}).get("timeframe_entry", "M15")
        tf_htf = self.config.get("training", {}).get("timeframe_htf", "H1")
        last_candle_time: Dict[str, pd.Timestamp] = {}

        while not self._stop_flag.is_set():
            try:
                for symbol, formula in list(self._active_formulas.items()):
                    if self._stop_flag.is_set():
                        break

                    # Check if formula still meets minimum winrate
                    wr = self._formula_winrates.get(symbol, 0.0)
                    if wr < self.min_formula_winrate:
                        logger.warning(f"{symbol}: formula winrate {wr:.1%} below threshold, skipping")
                        continue

                    # Fetch latest candles
                    df = self.data_manager.connector.fetch_rates(symbol, tf_entry, 300)
                    df_htf = self.data_manager.connector.fetch_rates(symbol, tf_htf, 100)

                    if df is None or len(df) < 50:
                        continue

                    # Check if a new candle closed
                    latest_candle = df.index[-2]  # use -2 (last CLOSED candle)
                    prev_latest = last_candle_time.get(symbol)

                    if prev_latest is not None and latest_candle <= prev_latest:
                        continue  # no new closed candle

                    last_candle_time[symbol] = latest_candle

                    # Get signal on last closed bar
                    signals = self.formula_engine.compute_signals(df, df_htf, formula)
                    last_signal = signals[-2]  # last closed bar

                    if last_signal == 0:
                        continue

                    # Calculate SL/TP
                    h = df["high"].values
                    l = df["low"].values
                    c = df["close"].values
                    atr_arr = atr(h, l, c, formula["params"]["atr_period"])
                    sl_mult = formula["params"]["sl_atr_mult"]
                    rr = self.config.get("risk", {}).get("rr_ratio", 2.0)

                    if np.isnan(atr_arr[-2]) or atr_arr[-2] <= 0:
                        continue

                    entry_price = c[-1]  # current bar open (approximate)
                    sl_dist = atr_arr[-2] * sl_mult

                    if last_signal == 1:
                        direction = "buy"
                        sl_price = entry_price - sl_dist
                        tp_price = entry_price + sl_dist * rr
                    else:
                        direction = "sell"
                        sl_price = entry_price + sl_dist
                        tp_price = entry_price - sl_dist * rr

                    signal = TradeSignal(
                        symbol=symbol,
                        direction=direction,
                        entry=entry_price,
                        sl=sl_price,
                        tp=tp_price,
                        formula_id=formula.get("id", "?"),
                        winrate=wr,
                    )

                    logger.info(f"Signal: {direction.upper()} {symbol} @ {entry_price:.5f} "
                                f"SL={sl_price:.5f} TP={tp_price:.5f} WR={wr:.1%}")

                    if not self.risk_manager.can_open_trade(symbol):
                        continue

                    if self.mode == "auto":
                        self._execute_trade(signal)
                    else:
                        with self._lock:
                            self._pending_signals.append(signal)
                        if self.on_signal:
                            self.on_signal(signal)

            except Exception as e:
                logger.error(f"Trading loop error: {e}")
                if self.on_error:
                    self.on_error(str(e))

            self._stop_flag.wait(self.check_interval)

    def _execute_trade(self, signal: TradeSignal):
        """Execute a trade signal via MT5."""
        lot = self.risk_manager.calculate_lot(signal.symbol, signal.sl_distance)

        result = self.connector.send_order(
            symbol=signal.symbol,
            order_type=signal.direction,
            lot=lot,
            sl_price=signal.sl,
            tp_price=signal.tp,
        )

        if result:
            trade_info = {
                "symbol": signal.symbol,
                "direction": signal.direction,
                "entry_time": signal.time.isoformat(),
                "entry_price": signal.entry,
                "sl_price": signal.sl,
                "tp_price": signal.tp,
                "lot": lot,
                "result": "open",
                "formula_id": signal.formula_id,
                "ticket": result.get("order"),
            }
            self.trade_logger.log_signal({
                **trade_info,
                "executed": True,
            })
            if self.on_trade_opened:
                self.on_trade_opened(trade_info)
            logger.info(f"Trade opened: ticket={result.get('order')} {signal.direction} {signal.symbol}")
        else:
            logger.error(f"Failed to open trade: {signal.symbol}")
