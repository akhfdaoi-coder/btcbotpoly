from __future__ import annotations

import requests

from .config import SETTINGS


class TelegramNotifier:
    def __init__(self) -> None:
        self.enabled = bool(SETTINGS.enable_telegram and SETTINGS.telegram_bot_token and SETTINGS.telegram_chat_id)

    def send(self, text: str) -> bool:
        if not self.enabled:
            return False
        url = f"https://api.telegram.org/bot{SETTINGS.telegram_bot_token}/sendMessage"
        response = requests.post(url, json={"chat_id": SETTINGS.telegram_chat_id, "text": text}, timeout=15)
        response.raise_for_status()
        return True
