SCHEMAS = {
    "mt5_get_tick": {
        "name": "mt5_get_tick",
        "description": "Get current XAUUSD real-time bid/ask price and spread",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    "mt5_get_ohlcv": {
        "name": "mt5_get_ohlcv",
        "description": "Get XAUUSD OHLCV candlestick data",
        "parameters": {
            "type": "object",
            "properties": {
                "timeframe": {"type": "string", "enum": ["M1", "M5", "M15", "H1"], "default": "M5"},
                "bars": {"type": "integer", "default": 20, "maximum": 200},
            },
            "required": [],
        },
    },
    "mt5_get_account": {
        "name": "mt5_get_account",
        "description": "Get current account balance, equity, margin, and floating profit",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    "mt5_get_positions": {
        "name": "mt5_get_positions",
        "description": "Get all open XAUUSD positions with ticket, side, lot, SL, TP, and current profit",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    "mt5_get_history": {
        "name": "mt5_get_history",
        "description": "Get today's closed trade history for XAUUSD",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    "mt5_get_symbol_info": {
        "name": "mt5_get_symbol_info",
        "description": "Get XAUUSD contract specifications: tick size, tick value, lot limits",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    "mt5_place_buy": {
        "name": "mt5_place_buy",
        "description": "Open a market BUY position on XAUUSD. Lot size is auto-calculated from risk settings.",
        "parameters": {
            "type": "object",
            "properties": {
                "sl_price": {"type": "number", "description": "Stop-loss price in USD"},
                "tp_price": {"type": "number", "description": "Take-profit price in USD (auto-calculated if omitted)"},
                "comment": {"type": "string", "default": "GoldHouseAI-BUY"},
            },
            "required": ["sl_price"],
        },
    },
    "mt5_place_sell": {
        "name": "mt5_place_sell",
        "description": "Open a market SELL position on XAUUSD. Lot size is auto-calculated from risk settings.",
        "parameters": {
            "type": "object",
            "properties": {
                "sl_price": {"type": "number", "description": "Stop-loss price in USD"},
                "tp_price": {"type": "number", "description": "Take-profit price in USD (auto-calculated if omitted)"},
                "comment": {"type": "string", "default": "GoldHouseAI-SELL"},
            },
            "required": ["sl_price"],
        },
    },
    "mt5_place_buy_limit": {
        "name": "mt5_place_buy_limit",
        "description": "Place a pending BUY LIMIT order at a specific price",
        "parameters": {
            "type": "object",
            "properties": {
                "price": {"type": "number", "description": "Entry price for the limit order"},
                "sl_price": {"type": "number"},
                "tp_price": {"type": "number"},
                "lot": {"type": "number", "default": 0.01},
            },
            "required": ["price", "sl_price"],
        },
    },
    "mt5_place_sell_limit": {
        "name": "mt5_place_sell_limit",
        "description": "Place a pending SELL LIMIT order at a specific price",
        "parameters": {
            "type": "object",
            "properties": {
                "price": {"type": "number"},
                "sl_price": {"type": "number"},
                "tp_price": {"type": "number"},
                "lot": {"type": "number", "default": 0.01},
            },
            "required": ["price", "sl_price"],
        },
    },
    "mt5_modify_position": {
        "name": "mt5_modify_position",
        "description": "Update SL and/or TP of an open position",
        "parameters": {
            "type": "object",
            "properties": {
                "ticket": {"type": "integer"},
                "sl_price": {"type": "number"},
                "tp_price": {"type": "number"},
            },
            "required": ["ticket", "sl_price", "tp_price"],
        },
    },
    "mt5_close_position": {
        "name": "mt5_close_position",
        "description": "Close a specific open position by its ticket number",
        "parameters": {
            "type": "object",
            "properties": {"ticket": {"type": "integer"}},
            "required": ["ticket"],
        },
    },
    "mt5_close_all": {
        "name": "mt5_close_all",
        "description": "Close ALL open XAUUSD positions immediately",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    "mt5_cancel_pending": {
        "name": "mt5_cancel_pending",
        "description": "Cancel a pending order by ticket number",
        "parameters": {
            "type": "object",
            "properties": {"ticket": {"type": "integer"}},
            "required": ["ticket"],
        },
    },
    "mt5_trailing_stop": {
        "name": "mt5_trailing_stop",
        "description": "Apply trailing stop to an open position",
        "parameters": {
            "type": "object",
            "properties": {
                "ticket": {"type": "integer"},
                "trail_points": {"type": "number", "description": "Trail distance in price points (e.g. 2.0 for $2)"},
            },
            "required": ["ticket", "trail_points"],
        },
    },
    "mt5_create_skill": {
        "name": "mt5_create_skill",
        "description": "Save a new trading skill or strategy insight as a .md file to the skills directory for future sessions",
        "parameters": {
            "type": "object",
            "properties": {
                "skill_name": {"type": "string", "description": "Filename (no spaces, no .md extension)"},
                "content": {"type": "string", "description": "Full markdown content of the skill"},
            },
            "required": ["skill_name", "content"],
        },
    },
}
