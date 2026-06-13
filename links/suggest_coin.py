import json
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"
COINGECKO_IDS = {
    "USDT": "tether",
    "BTC": "bitcoin",
    "ETH": "ethereum",
}
DEFAULT_SUGGESTION = {
    "suggestion": "USDT",
    "reason": "USDT is the most stable option for everyday payments.",
}


def _fetch_market_snapshot() -> dict:
    ids = ",".join(COINGECKO_IDS.values())
    response = requests.get(
        COINGECKO_URL,
        params={
            "ids": ids,
            "vs_currencies": "usd",
            "include_24hr_change": "true",
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def _fallback_suggestion(market: dict) -> dict:
    changes = {}
    for coin, gecko_id in COINGECKO_IDS.items():
        entry = market.get(gecko_id, {})
        changes[coin] = entry.get("usd_24h_change")

    usdt_change = changes.get("USDT")
    if usdt_change is not None and abs(usdt_change) < 0.5:
        return {
            "suggestion": "USDT",
            "reason": "USDT is holding steady — best for predictable payment amounts.",
        }

    btc_change = changes.get("BTC")
    eth_change = changes.get("ETH")
    if btc_change is not None and eth_change is not None:
        if abs(btc_change) <= abs(eth_change):
            return {
                "suggestion": "BTC",
                "reason": f"BTC moved {btc_change:+.1f}% today vs ETH at {eth_change:+.1f}%.",
            }
        return {
            "suggestion": "ETH",
            "reason": f"ETH moved {eth_change:+.1f}% today vs BTC at {btc_change:+.1f}%.",
        }

    return DEFAULT_SUGGESTION.copy()


def _groq_suggestion(market: dict) -> dict | None:
    api_key = settings.GROQ_API_KEY
    if not api_key:
        return None

    try:
        from groq import Groq
    except ImportError:
        logger.warning("groq package not available")
        return None

    prompt = (
        "You are a crypto payment assistant for SwiftyPay. "
        "Given 24h price change data, suggest ONE coin from USDT, BTC, or ETH "
        "for receiving a payment. Respond with JSON only: "
        '{"suggestion":"USDT|BTC|ETH","reason":"one short sentence"}.\n\n'
        f"Market data: {json.dumps(market)}"
    )

    try:
        client = Groq(api_key=api_key)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=120,
        )
        content = completion.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.strip("`")
            if content.startswith("json"):
                content = content[4:].strip()
        parsed = json.loads(content)
        suggestion = parsed.get("suggestion", "").upper()
        reason = parsed.get("reason", "")
        if suggestion in COINGECKO_IDS and reason:
            return {"suggestion": suggestion, "reason": reason}
    except Exception:
        logger.exception("Groq coin suggestion failed")

    return None


def get_coin_suggestion() -> dict:
    try:
        market = _fetch_market_snapshot()
    except requests.RequestException:
        logger.exception("CoinGecko request failed")
        return DEFAULT_SUGGESTION.copy()

    groq_result = _groq_suggestion(market)
    if groq_result:
        return groq_result

    return _fallback_suggestion(market)
