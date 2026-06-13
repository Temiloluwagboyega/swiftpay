import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def send_payment_notification(
    *,
    chat_id: str,
    amount,
    coin: str,
    note: str,
    payer_username: str = "",
) -> bool:
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        logger.warning("TELEGRAM_BOT_TOKEN not set; skipping notification.")
        return False

    payer = f"@{payer_username}" if payer_username else "Someone"
    note_line = f'\nNote: "{note}"' if note else ""
    text = (
        f"Payment received!\n\n"
        f"{payer} paid {amount} {coin}.{note_line}"
    )

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        response = requests.post(
            url,
            json={"chat_id": chat_id, "text": text},
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
        return bool(payload.get("ok"))
    except requests.RequestException:
        logger.exception("Failed to send Telegram notification to %s", chat_id)
        return False
