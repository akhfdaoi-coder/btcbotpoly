from __future__ import annotations

import time

from .market_data import CoinbaseBtcClient, PolymarketClient
from .state_store import StateStore
from .strategy import choose_current_market, enter_if_needed, exit_if_needed
from .telegram import TelegramNotifier


def run_once(send_alerts: bool = False) -> None:
    now_ms = int(time.time() * 1000)
    store = StateStore()
    notifier = TelegramNotifier()
    pm = PolymarketClient()
    btc = CoinbaseBtcClient()
    state = store.load()

    events = pm.fetch_active_events(limit=250)
    markets = pm.extract_btc_5m_markets(events)
    market = choose_current_market(markets)

    if not market:
        print("No active BTC 5m market found")
        return

    up_book = pm.get_order_book(market.up_token_id)
    down_book = pm.get_order_book(market.down_token_id)
    signal = btc.build_signal()

    if state.position is None:
        state, row, msg = enter_if_needed(state, market, up_book, down_book, signal, now_ms)
    else:
        state, row, msg = exit_if_needed(state, market, up_book, down_book, signal, now_ms)

    print(
        f"{msg} | btc={signal.price:.2f} | side_signal={signal.side} | "
        f"ret1m={signal.ret_1m:.4%} ret3m={signal.ret_3m:.4%} | cash={state.cash_eur:.2f}€ "
        f"realized={state.realized_pnl_eur:.2f}€ wins={state.wins} losses={state.losses}"
    )

    if row:
        store.append_trade(row)
        if send_alerts:
            notifier.send(
                f"Polymarket BTC 5m paper\n"
                f"Action: {row['action']}\n"
                f"Side: {row['side']}\n"
                f"Market: {market.question}\n"
                f"Price: {row.get('entry_price', row.get('exit_price'))}\n"
                f"PnL: {row.get('pnl_eur', 0):.2f}€\n"
                f"Cash: {state.cash_eur:.2f}€\n"
                f"Realized: {state.realized_pnl_eur:.2f}€"
            )

    store.save(state)
