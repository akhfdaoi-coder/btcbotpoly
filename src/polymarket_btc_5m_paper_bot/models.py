from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class MarketCandidate:
    market_id: str
    question: str
    slug: Optional[str]
    up_token_id: Optional[str]
    down_token_id: Optional[str]
    active: bool
    closed: bool
    end_date_iso: Optional[str]


@dataclass
class OrderBookSnapshot:
    best_bid: Optional[float]
    best_ask: Optional[float]
    spread: Optional[float]


@dataclass
class BtcSignal:
    price: float
    ret_1m: float
    ret_3m: float
    ret_5m: float
    side: str
    strength: float


@dataclass
class Position:
    market_id: str
    market_question: str
    side: str
    entry_price: float
    stake_eur: float
    shares: float
    entry_timestamp_ms: int
    target_price: float
    stop_price: float


@dataclass
class State:
    cash_eur: float
    realized_pnl_eur: float
    wins: int
    losses: int
    last_market_id_traded: Optional[str]
    position: Optional[Position] = None
