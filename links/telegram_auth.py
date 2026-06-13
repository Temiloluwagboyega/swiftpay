import hashlib
import hmac
import json
import logging
from urllib.parse import parse_qsl

from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed

logger = logging.getLogger(__name__)


def _build_data_check_string(data: dict) -> str:
    pairs = [f"{key}={value}" for key, value in sorted(data.items())]
    return "\n".join(pairs)


def verify_telegram_init_data(init_data: str) -> dict:
    """
    Validate Telegram WebApp initData per official docs.
    Returns parsed user payload on success.
    """
    if not init_data:
        if settings.DEBUG:
            return {
                "id": "123456789",
                "username": "debug_user",
                "first_name": "Debug",
            }
        raise AuthenticationFailed("Missing initData.")

    bot_token = settings.TELEGRAM_BOT_TOKEN
    if not bot_token:
        raise AuthenticationFailed("Telegram bot token is not configured.")

    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise AuthenticationFailed("Invalid initData: missing hash.")

    secret_key = hmac.new(
        b"WebAppData",
        bot_token.encode(),
        hashlib.sha256,
    ).digest()
    calculated_hash = hmac.new(
        secret_key,
        _build_data_check_string(parsed).encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise AuthenticationFailed("Invalid initData signature.")

    user_raw = parsed.get("user")
    if not user_raw:
        raise AuthenticationFailed("Invalid initData: missing user.")

    try:
        user = json.loads(user_raw)
    except json.JSONDecodeError as exc:
        raise AuthenticationFailed("Invalid initData user payload.") from exc

    if "id" not in user:
        raise AuthenticationFailed("Invalid initData: user id missing.")

    return user
