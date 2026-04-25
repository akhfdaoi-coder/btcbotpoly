from __future__ import annotations

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


def _get_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return float(value)


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return int(value)


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    gamma_base_url: str = os.getenv("GAMMA_BASE_URL", "https://gamma-api.polymarket.com")
    clob_base_url: str = os.getenv("CLOB_BASE_URL", "https://clob.polymarket.com")
    coinbase_products_url: str = os.getenv("COINBASE_PRODUCTS_URL", "https://api.exchange.coinbase.com/products")

    request_timeout_seconds: int = _get_int("REQUEST_TIMEOUT_SECONDS", 20)
    loop_interval_seconds: int = _get_int("LOOP_INTERVAL_SECONDS", 10)

    starting_balance_eur: float = _get_float("STARTING_BALANCE_EUR", 20.0)
    stake_eur: float = _get_float("STAKE_EUR", 3.0)

    force_trade_every_new_market: bool = _get_bool("FORCE_TRADE_EVERY_NEW_MARKET", True)
    max_spread: float = _get_float("MAX_SPREAD", 0.18)
    profit_target_cents: float = _get_float("PROFIT_TARGET_CENTS", 0.08)
    stop_loss_cents: float = _get_float("STOP_LOSS_CENTS", 0.06)
    force_exit_seconds_left: int = _get_int("FORCE_EXIT_SECONDS_LEFT", 25)
    signal_flip_exit: bool = _get_bool("SIGNAL_FLIP_EXIT", True)
    min_seconds_after_entry_to_exit: int = _get_int("MIN_SECONDS_AFTER_ENTRY_TO_EXIT", 15)

    enable_telegram: bool = _get_bool("ENABLE_TELEGRAM", False)
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")

    state_path: str = os.getenv("STATE_PATH", "data/state.json")
    trade_log_path: str = os.getenv("TRADE_LOG_PATH", "data/trades.csv")


SETTINGS = Settings()
