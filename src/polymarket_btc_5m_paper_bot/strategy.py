from __future__ import annotations

from datetime import datetime
from typing import Optional

from .config import SETTINGS
from .models import BtcSignal, MarketCandidate, OrderBookSnapshot, Position, State


def end_ts_ms(market: MarketCandidate) -> Optional[int]:
    if not market.end_date_iso:
        return None
    try:
        return int(datetime.fromisoformat(market.end_date_iso.replace("Z", "+00:00")).timestamp() * 1000)
    except Exception:
        return None


def choose_current_market(markets: list[MarketCandidate]) -> Optional[MarketCandidate]:
    valid = [m for m in markets if m.up_token_id and m.down_token_id]
    if not valid:
        return None
    return sorted(valid, key=lambda m: end_ts_ms(m) or 0, reverse=True)[0]


def enter_if_needed(
    state: State,
    market: MarketCandidate,
    up_book: OrderBookSnapshot,
    down_book: OrderBookSnapshot,
    signal: BtcSignal,
    now_ms: int,
):
    if state.position is not None:
        return state, None, "Position already open"

    if state.cash_eur < SETTINGS.stake_eur:
        return state, None, "Not enough paper cash"

    if state.last_market_id_traded == market.market_id:
        return state, None, "Already traded this market"

    side = signal.side
    book = up_book if side == "UP" else down_book
    if book.best_ask is None:
        return state, None, f"No ask for {side}"

    if book.spread is not None and book.spread > SETTINGS.max_spread:
        # Since user wants frequent trades, allow fallback to other side if spread is better.
        alt_side = "DOWN" if side == "UP" else "UP"
        alt_book = down_book if side == "UP" else up_book
        if alt_book.best_ask is not None and (alt_book.spread is None or alt_book.spread <= SETTINGS.max_spread):
            side = alt_side
            book = alt_book
        else:
            return state, None, f"Spread too wide on both sides"

    entry = book.best_ask
    stake = min(SETTINGS.stake_eur, state.cash_eur)
    shares = stake / entry

    state.cash_eur -= stake
    state.last_market_id_traded = market.market_id
    state.position = Position(
        market_id=market.market_id,
        market_question=market.question,
        side=side,
        entry_price=entry,
        stake_eur=stake,
        shares=shares,
        entry_timestamp_ms=now_ms,
        target_price=min(0.99, entry + SETTINGS.profit_target_cents),
        stop_price=max(0.01, entry - SETTINGS.stop_loss_cents),
    )

    row = {
        "timestamp_ms": now_ms,
        "action": "BUY",
        "market_id": market.market_id,
        "question": market.question,
        "side": side,
        "entry_price": entry,
        "stake_eur": stake,
        "shares": shares,
        "btc_price": signal.price,
        "ret_1m": signal.ret_1m,
        "ret_3m": signal.ret_3m,
        "ret_5m": signal.ret_5m,
        "note": f"forced_trade_side={side}, strength={signal.strength:.6f}",
    }
    return state, row, f"BUY {side} @ {entry:.3f}"


def exit_if_needed(
    state: State,
    market: MarketCandidate,
    up_book: OrderBookSnapshot,
    down_book: OrderBookSnapshot,
    signal: BtcSignal,
    now_ms: int,
):
    pos = state.position
    if pos is None:
        return state, None, "No position"

    book = up_book if pos.side == "UP" else down_book
    if book.best_bid is None:
        return state, None, f"HOLD {pos.side} no bid"

    seconds_after_entry = (now_ms - pos.entry_timestamp_ms) / 1000
    end_ts = end_ts_ms(market)
    seconds_left = (end_ts - now_ms) / 1000 if end_ts else None

    should_exit = False
    reason = "Position open"

    if seconds_after_entry >= SETTINGS.min_seconds_after_entry_to_exit:
        if book.best_bid >= pos.target_price:
            should_exit = True
            reason = "Profit target"
        elif book.best_bid <= pos.stop_price:
            should_exit = True
            reason = "Stop loss"
        elif SETTINGS.signal_flip_exit and signal.side != pos.side:
            should_exit = True
            reason = "Signal flip"

    if seconds_left is not None and seconds_left <= SETTINGS.force_exit_seconds_left:
        should_exit = True
        reason = "Forced exit before resolution"

    if not should_exit:
        return state, None, f"HOLD {pos.side} bid={book.best_bid:.3f}"

    proceeds = pos.shares * book.best_bid
    pnl = proceeds - pos.stake_eur
    state.cash_eur += proceeds
    state.realized_pnl_eur += pnl
    if pnl >= 0:
        state.wins += 1
    else:
        state.losses += 1

    row = {
        "timestamp_ms": now_ms,
        "action": "SELL",
        "market_id": pos.market_id,
        "question": pos.market_question,
        "side": pos.side,
        "exit_price": book.best_bid,
        "entry_price": pos.entry_price,
        "stake_eur": pos.stake_eur,
        "proceeds_eur": proceeds,
        "pnl_eur": pnl,
        "note": reason,
    }
    state.position = None
    return state, row, f"SELL {row['side']} @ {book.best_bid:.3f} pnl={pnl:.2f}€ {reason}"
