from __future__ import annotations

from pathlib import Path

from .handlers import (
    make_cancel_pending_handler,
    make_close_all_handler,
    make_close_position_handler,
    make_create_skill_handler,
    make_get_account_handler,
    make_get_history_handler,
    make_get_ohlcv_handler,
    make_get_positions_handler,
    make_get_symbol_info_handler,
    make_get_tick_handler,
    make_modify_position_handler,
    make_pending_handler,
    make_place_buy_handler,
    make_place_sell_handler,
    make_trailing_stop_handler,
)

from .schemas import SCHEMAS

_connector = None
_risk_manager = None
_skills_dir: Path = Path(__file__).parent.parent / "skills"


def set_dependencies(connector, risk_manager, skills_dir: Path = None):
    global _connector, _risk_manager, _skills_dir
    _connector = connector
    _risk_manager = risk_manager
    if skills_dir:
        _skills_dir = skills_dir


def register(ctx):
    assert _connector is not None, "Call set_dependencies() before loading plugin"

    tool_map = {
        "mt5_get_tick": make_get_tick_handler(_connector),
        "mt5_get_ohlcv": make_get_ohlcv_handler(_connector),
        "mt5_get_account": make_get_account_handler(_connector),
        "mt5_get_positions": make_get_positions_handler(_connector),
        "mt5_get_history": make_get_history_handler(_connector),
        "mt5_get_symbol_info": make_get_symbol_info_handler(_connector),
        "mt5_place_buy": make_place_buy_handler(_connector, _risk_manager),
        "mt5_place_sell": make_place_sell_handler(_connector, _risk_manager),
        "mt5_place_buy_limit": make_pending_handler(_connector, _risk_manager, "BUY_LIMIT"),
        "mt5_place_sell_limit": make_pending_handler(_connector, _risk_manager, "SELL_LIMIT"),
        "mt5_modify_position": make_modify_position_handler(_connector),
        "mt5_close_position": make_close_position_handler(_connector),
        "mt5_close_all": make_close_all_handler(_connector),
        "mt5_cancel_pending": make_cancel_pending_handler(_connector),
        "mt5_trailing_stop": make_trailing_stop_handler(_connector),
        "mt5_create_skill": make_create_skill_handler(_skills_dir),
    }

    for name, handler in tool_map.items():
        ctx.register_tool(
            name=name,
            toolset="mt5_trading",
            schema=SCHEMAS[name],
            handler=handler,
        )
