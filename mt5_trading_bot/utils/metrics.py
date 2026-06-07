import numpy as np
from typing import List, Dict


def compute_winrate(trades: List[Dict]) -> float:
    if not trades:
        return 0.0
    wins = sum(1 for t in trades if t.get("result") == "win")
    return wins / len(trades)


def compute_profit_factor(trades: List[Dict]) -> float:
    gross_profit = sum(t["pnl_r"] for t in trades if t["pnl_r"] > 0)
    gross_loss = abs(sum(t["pnl_r"] for t in trades if t["pnl_r"] < 0))
    if gross_loss == 0:
        return float("inf") if gross_profit > 0 else 0.0
    return gross_profit / gross_loss


def compute_max_drawdown(equity_curve: np.ndarray) -> float:
    if len(equity_curve) == 0:
        return 0.0
    peak = np.maximum.accumulate(equity_curve)
    drawdown = (peak - equity_curve) / np.where(peak == 0, 1, peak)
    return float(np.max(drawdown))


def compute_sharpe_ratio(returns: np.ndarray, risk_free: float = 0.0) -> float:
    if len(returns) < 2:
        return 0.0
    excess = returns - risk_free
    std = np.std(excess, ddof=1)
    if std == 0:
        return 0.0
    return float(np.mean(excess) / std * np.sqrt(252))


def compute_equity_curve(trades: List[Dict], initial_balance: float = 10000.0) -> np.ndarray:
    equity = [initial_balance]
    for t in trades:
        equity.append(equity[-1] + t.get("pnl_r", 0) * initial_balance * 0.01)
    return np.array(equity)


def compute_all_metrics(trades: List[Dict]) -> Dict:
    if not trades:
        return {
            "winrate": 0.0,
            "profit_factor": 0.0,
            "total_trades": 0,
            "max_drawdown": 0.0,
            "sharpe_ratio": 0.0,
            "avg_trade_duration": 0.0,
            "is_valid": False,
        }

    equity = compute_equity_curve(trades)
    returns = np.diff(equity) / equity[:-1]
    pnl_arr = np.array([t["pnl_r"] for t in trades])

    winrate = compute_winrate(trades)
    profit_factor = compute_profit_factor(trades)
    max_dd = compute_max_drawdown(equity)
    sharpe = compute_sharpe_ratio(returns)
    durations = [t.get("duration_bars", 0) for t in trades]
    avg_dur = float(np.mean(durations)) if durations else 0.0

    return {
        "winrate": winrate,
        "profit_factor": profit_factor,
        "total_trades": len(trades),
        "max_drawdown": max_dd,
        "sharpe_ratio": sharpe,
        "avg_trade_duration": avg_dur,
        "net_pnl_r": float(np.sum(pnl_arr)),
        "is_valid": winrate >= 0.75 and len(trades) >= 100 and profit_factor >= 2.0,
    }


def expected_value(winrate: float, rr: float = 2.0) -> float:
    return winrate * rr - (1 - winrate) * 1.0
