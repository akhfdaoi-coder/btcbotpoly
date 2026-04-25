from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import requests

from .config import SETTINGS
from .models import BtcSignal, MarketCandidate, OrderBookSnapshot


class PolymarketClient:
    def __init__(self) -> None:
        self.session = requests.Session()

    def _get(self, url: str, params: Optional[Dict[str, Any]] = None) -> Any:
        response = self.session.get(url, params=params, timeout=SETTINGS.request_timeout_seconds)
        response.raise_for_status()
        return response.json()

    def fetch_active_events(self, limit: int = 250) -> List[Dict[str, Any]]:
        return self._get(
            f"{SETTINGS.gamma_base_url}/events",
            params={"active": "true", "closed": "false", "limit": limit},
        )

    def extract_btc_5m_markets(self, events: List[Dict[str, Any]]) -> List[MarketCandidate]:
        markets: List[MarketCandidate] = []
        for event in events:
            for market in event.get("markets", []):
                question = market.get("question") or market.get("title") or ""
                haystack = f"{question} {market.get('slug') or ''}".lower()
                if "btc" not in haystack or "up" not in haystack or "down" not in haystack:
                    continue
                if "5" not in haystack and "five" not in haystack:
                    continue

                outcomes = market.get("outcomes")
                token_ids = market.get("clobTokenIds")
                up_token_id = None
                down_token_id = None

                try:
                    if isinstance(outcomes, str):
                        outcomes = json.loads(outcomes)
                    if isinstance(token_ids, str):
                        token_ids = json.loads(token_ids)
                except Exception:
                    pass

                if isinstance(outcomes, list) and isinstance(token_ids, list):
                    mapping = {str(o).lower(): str(t) for o, t in zip(outcomes, token_ids)}
                    up_token_id = mapping.get("up") or mapping.get("yes")
                    down_token_id = mapping.get("down") or mapping.get("no")

                markets.append(
                    MarketCandidate(
                        market_id=str(market.get("id")),
                        question=question,
                        slug=market.get("slug"),
                        up_token_id=up_token_id,
                        down_token_id=down_token_id,
                        active=bool(market.get("active", False)),
                        closed=bool(market.get("closed", False)),
                        end_date_iso=market.get("endDate") or market.get("end_date_iso"),
                    )
                )
        return markets

    def get_order_book(self, token_id: str) -> OrderBookSnapshot:
        payload = self._get(f"{SETTINGS.clob_base_url}/book", params={"token_id": token_id})
        bids = payload.get("bids", []) or []
        asks = payload.get("asks", []) or []

        def price(row: Any) -> float:
            if isinstance(row, dict):
                return float(row["price"])
            return float(row[0])

        best_bid = max([price(b) for b in bids], default=None)
        best_ask = min([price(a) for a in asks], default=None)
        spread = None
        if best_bid is not None and best_ask is not None:
            spread = best_ask - best_bid

        return OrderBookSnapshot(best_bid=best_bid, best_ask=best_ask, spread=spread)


class CoinbaseBtcClient:
    def __init__(self) -> None:
        self.session = requests.Session()

    def fetch_closes(self) -> List[float]:
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(minutes=12)
        url = f"{SETTINGS.coinbase_products_url}/BTC-USD/candles"
        params = {
            "granularity": 60,
            "start": start_time.isoformat(),
            "end": end_time.isoformat(),
        }
        response = self.session.get(url, params=params, timeout=SETTINGS.request_timeout_seconds)
        response.raise_for_status()
        rows = response.json()
        rows.sort(key=lambda r: r[0])
        return [float(r[4]) for r in rows]

    def build_signal(self) -> BtcSignal:
        closes = self.fetch_closes()
        if len(closes) < 6:
            raise ValueError("Not enough BTC candles")

        price = closes[-1]
        ret_1m = (closes[-1] - closes[-2]) / closes[-2]
        ret_3m = (closes[-1] - closes[-4]) / closes[-4]
        ret_5m = (closes[-1] - closes[-6]) / closes[-6]

        weighted = (ret_1m * 0.50) + (ret_3m * 0.35) + (ret_5m * 0.15)
        side = "UP" if weighted >= 0 else "DOWN"
        strength = abs(weighted)

        return BtcSignal(
            price=price,
            ret_1m=ret_1m,
            ret_3m=ret_3m,
            ret_5m=ret_5m,
            side=side,
            strength=strength,
        )
