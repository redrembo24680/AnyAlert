"""Telegram notification service.

Provides:
- send_message(): send a Telegram message to a user by telegram_id.
- generate_link_code(): create a short code stored in Redis that maps to a user_id.
- consume_link_code(): look up & delete the code, returning the user_id.
"""
import logging
import secrets
import string

import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)

_LINK_CODE_PREFIX = "tg_link:"
_CODE_ALPHABET = string.ascii_uppercase + string.digits
_CODE_LENGTH = 8


def _redis_client() -> aioredis.Redis:
    return aioredis.from_url(settings.redis_url, decode_responses=True)


def _link_key(code: str) -> str:
    return f"{_LINK_CODE_PREFIX}{code}"


async def generate_link_code(user_id: int) -> str:
    """Generate an 8-char code and store user_id in Redis with configured TTL."""
    code = "".join(secrets.choice(_CODE_ALPHABET) for _ in range(_CODE_LENGTH))
    ttl_seconds = settings.telegram_link_code_ttl_minutes * 60
    async with _redis_client() as r:
        await r.setex(_link_key(code), ttl_seconds, str(user_id))
    return code


async def consume_link_code(code: str) -> int | None:
    """Look up the code in Redis. Returns user_id and deletes the key (one-time use)."""
    async with _redis_client() as r:
        raw = await r.getdel(_link_key(code.upper()))
    if raw is None:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


async def send_message(telegram_id: int, text: str) -> None:
    """Send a Telegram message via the Bot API (fire-and-forget helper)."""
    if not settings.telegram_bot_token:
        logger.debug("Telegram bot token not configured, skipping message.")
        return
    try:
        from telegram import Bot
        async with Bot(token=settings.telegram_bot_token) as bot:
            await bot.send_message(chat_id=telegram_id, text=text, parse_mode="HTML")
    except Exception:
        logger.exception("Failed to send Telegram message to %s", telegram_id)
