from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from .config import SETTINGS
from .models import Position, State


class StateStore:
    def __init__(self) -> None:
        self.state_path = Path(SETTINGS.state_path)
        self.trade_log_path = Path(SETTINGS.trade_log_path)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.trade_log_path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> State:
        if not self.state_path.exists():
            return State(
                cash_eur=SETTINGS.starting_balance_eur,
                realized_pnl_eur=0.0,
                wins=0,
                losses=0,
                last_market_id_traded=None,
                position=None,
            )
        payload = json.loads(self.state_path.read_text())
        pos = payload.get("position")
        return State(
            cash_eur=float(payload["cash_eur"]),
            realized_pnl_eur=float(payload["realized_pnl_eur"]),
            wins=int(payload["wins"]),
            losses=int(payload["losses"]),
            last_market_id_traded=payload.get("last_market_id_traded"),
            position=Position(**pos) if pos else None,
        )

    def save(self, state: State) -> None:
        self.state_path.write_text(json.dumps(asdict(state), indent=2))

    def append_trade(self, row: dict) -> None:
        df = pd.DataFrame([row])
        if self.trade_log_path.exists():
            df.to_csv(self.trade_log_path, mode="a", header=False, index=False)
        else:
            df.to_csv(self.trade_log_path, index=False)
