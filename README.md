# Polymarket BTC 5-Minute Paper Bot

Aggressive paper-trading bot for Polymarket BTC "Up or Down - 5 Minutes" markets.

Defaults:
- Paper bankroll: 20 EUR
- Stake per prediction: 3 EUR
- Attempts one paper trade per new BTC 5-minute market
- Uses recent BTC momentum to choose UP or DOWN
- Exits before resolution using target, stop, signal flip, or forced exit

## Important
This is paper trading only. It does not place real orders and does not connect to a wallet.

## Railway start command
python -m src.polymarket_btc_5m_paper_bot.alert_bot

## Telegram
Use:
- ENABLE_TELEGRAM=true
- TELEGRAM_BOT_TOKEN=your_token
- TELEGRAM_CHAT_ID=your_numeric_chat_id

## Useful test variables
STARTING_BALANCE_EUR=20
STAKE_EUR=3
LOOP_INTERVAL_SECONDS=10
FORCE_TRADE_EVERY_NEW_MARKET=true
PROFIT_TARGET_CENTS=0.08
STOP_LOSS_CENTS=0.06
FORCE_EXIT_SECONDS_LEFT=25
