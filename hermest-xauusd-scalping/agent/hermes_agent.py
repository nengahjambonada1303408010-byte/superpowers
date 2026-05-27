from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

from utils.logger import logger
from utils.token_optimizer import build_compact_market_context

PLUGIN_DIR = Path(__file__).parent / "mt5_tools_plugin"
SKILLS_DIR = Path(__file__).parent / "skills"

SYSTEM_PROMPT = """You are Gold House AI — the chief strategist of a professional XAUUSD scalping operation.

Your mission is to generate consistent, compounding profits by scalping Gold (XAUUSD) on MetaTrader 5.

You have full access to MT5 via tools (mt5_get_tick, mt5_place_buy, mt5_place_sell, mt5_close_position, etc.)
and 5 specialized skills that define your trading DNA:
- technical_analysis: How to read XAUUSD charts
- risk_assessment: How to evaluate and score trade quality
- trade_execution: SOP for entering, managing, and exiting trades
- profit_compounding: How to grow the account systematically
- market_session: Optimal trading windows (London/NY sessions)

After analyzing market data:
1. Score the signal quality (1-10) using risk_assessment skill
2. If score >= 7: Execute the trade (use MT5 tools if you decide to trade)
3. If you identify a new profitable pattern: use mt5_create_skill to save it

Always end your response with exactly one of:
ACTION: BUY
ACTION: SELL
ACTION: HOLD
ACTION: CLOSE_ALL"""


@dataclass
class AgentDecision:
    action: str
    reasoning: str
    confidence: float = 0.0
    raw_response: str = ""


class HermesTrader:
    def __init__(self, settings, connector, risk_manager):
        self._settings = settings
        self._connector = connector
        self._risk_manager = risk_manager
        self._agent = None
        self._fallback_mode = False
        self._init_agent()

    def _init_agent(self):
        try:
            from agent.mt5_tools_plugin import set_dependencies
            set_dependencies(self._connector, self._risk_manager, SKILLS_DIR)

            from run_agent import AIAgent
            self._agent = AIAgent(
                model=self._settings.HERMES_MODEL,
                openai_api_key=self._settings.KIMI_API_KEY,
                openai_base_url=self._settings.KIMI_BASE_URL,
                quiet_mode=True,
                skip_memory=False,
                plugin_dirs=[str(PLUGIN_DIR)],
                skills_dir=str(SKILLS_DIR),
                system_prompt=SYSTEM_PROMPT,
            )
            logger.info("Hermes Agent initialized with Kimi AI (%s)", self._settings.HERMES_MODEL)
        except ImportError:
            logger.warning("hermes-agent not installed — using fallback Kimi AI direct mode")
            self._fallback_mode = True
            self._init_fallback_client()

    def _init_fallback_client(self):
        try:
            from openai import OpenAI
            self._fallback_client = OpenAI(
                api_key=self._settings.KIMI_API_KEY,
                base_url=self._settings.KIMI_BASE_URL,
            )
            self._load_skills_text()
        except ImportError:
            logger.error("Neither hermes-agent nor openai package found")
            self._fallback_client = None

    def _load_skills_text(self) -> str:
        texts = []
        for skill_file in sorted(SKILLS_DIR.glob("*.md")):
            texts.append(f"## {skill_file.stem}\n{skill_file.read_text(encoding='utf-8')}")
        return "\n\n".join(texts)

    def analyze_and_act(self, market_data) -> AgentDecision:
        prompt = build_compact_market_context(market_data, self._settings)

        if self._fallback_mode:
            return self._fallback_analyze(prompt, market_data)

        try:
            response = self._agent.chat(prompt)
            return self._parse_decision(response)
        except Exception as e:
            logger.error("Hermes Agent error: %s", e)
            return AgentDecision(action="HOLD", reasoning=f"Agent error: {e}", raw_response=str(e))

    def _fallback_analyze(self, prompt: str, market_data) -> AgentDecision:
        if not self._fallback_client:
            return AgentDecision(action="HOLD", reasoning="No AI client available")
        try:
            skills_text = self._load_skills_text()
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT + "\n\n# Your Skills\n" + skills_text},
                {"role": "user", "content": prompt},
            ]
            resp = self._fallback_client.chat.completions.create(
                model=self._settings.HERMES_MODEL,
                messages=messages,
                max_tokens=500,
                temperature=0.3,
            )
            text = resp.choices[0].message.content
            decision = self._parse_decision(text)
            if decision.action in ("BUY", "SELL"):
                self._execute_from_decision(decision.action, market_data)
            return decision
        except Exception as e:
            logger.error("Fallback Kimi AI error: %s", e)
            return AgentDecision(action="HOLD", reasoning=f"Kimi error: {e}")

    def _execute_from_decision(self, action: str, market_data) -> None:
        try:
            tick = self._connector.get_tick()
            entry = tick["ask"] if action == "BUY" else tick["bid"]
            sl = self._risk_manager.calculate_sl_price(action, entry, market_data.atr_14)
            tp = self._risk_manager.calculate_tp_price(action, entry, sl)
            lot = self._risk_manager.calculate_lot_size(market_data.account_equity,
                                                        abs(entry - sl))
            result = self._connector.place_market_order("XAUUSD", action, lot, sl, tp)
            logger.info("Executed %s: lot=%.2f entry=%.2f sl=%.2f tp=%.2f ticket=%d",
                        action, lot, entry, sl, tp, result.ticket)
        except Exception as e:
            logger.error("Trade execution error: %s", e)

    def _parse_decision(self, response: str) -> AgentDecision:
        action = "HOLD"
        for line in reversed(response.strip().splitlines()):
            line = line.strip()
            match = re.search(r"ACTION:\s*(BUY|SELL|HOLD|CLOSE_ALL)", line, re.IGNORECASE)
            if match:
                action = match.group(1).upper()
                break

        confidence = 0.5
        conf_match = re.search(r"[Cc]onfidence[:\s]+([0-9.]+)", response)
        if conf_match:
            try:
                confidence = min(float(conf_match.group(1)), 1.0)
                if confidence > 1.0:
                    confidence /= 10.0
            except ValueError:
                pass

        reasoning = response.replace(f"ACTION: {action}", "").strip()
        return AgentDecision(action=action, reasoning=reasoning[:500],
                             confidence=confidence, raw_response=response)
