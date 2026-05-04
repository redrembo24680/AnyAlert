import asyncio
import logging

import httpx

from app.config import settings
from app.worker import celery_app
from app.tasks.retail_common import async_parse_retail

logger = logging.getLogger(__name__)


def _is_blocked_or_invalid_result(result: dict) -> bool:
    """Detect anti-bot/interruption pages to avoid overwriting valid DB values with nulls."""
    title = (result.get("title") or "").strip().lower()
    if "pardon our interruption" in title:
        return True

    # For product/offers tracking we expect at least current price on successful parse.
    return result.get("price") is None


@celery_app.task(bind=True, max_retries=3)
def parse_comfy_product(self, tracker_id: int, url: str):
    logger.info(f"[COMFY] Parsing tracker {tracker_id} for URL: {url}")

    try:
        result = asyncio.run(async_parse_retail(url))
        if _is_blocked_or_invalid_result(result):
            raise ValueError(
                "COMFY returned anti-bot/invalid page; skipping webhook update"
            )

        webhook_url = f"{settings.BACKEND_API_URL}/webhooks/{tracker_id}/comfy"
        update_data = {
            "last_price": result.get("price"),
            "last_old_price": result.get("old_price"),
            "last_discount_percent": result.get("discount_percent"),
            "last_cashback_amount": result.get("cashback_amount"),
            "last_personal_price_available": result.get("personal_price_available"),
            "last_gift_offer_available": result.get("gift_offer_available"),
            "last_status": result.get("status"),
            "last_availability": result.get("availability"),
            "last_rating": result.get("rating"),
            "last_reviews_count": result.get("reviews_count"),
            "last_views": None,
            "last_trade_in_available": result.get("trade_in_available"),
            "last_credit_available": result.get("credit_available"),
            "last_delivery_available": result.get("delivery_available"),
            "last_pickup_available": result.get("pickup_available"),
            "last_color": result.get("color"),
            "last_memory_variant": result.get("memory_variant"),
            "last_checked_at": result.get("checked_at"),
        }

        response = httpx.post(webhook_url, json=update_data, timeout=10.0)
        response.raise_for_status()
        logger.info(
            f"[COMFY] Successfully parsed and updated tracker {tracker_id}")
        return result
    except Exception as exc:
        logger.error(f"[COMFY] Error parsing tracker {tracker_id}: {str(exc)}")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=3)
def parse_comfy_offers(self, tracker_id: int, url: str):
    logger.info(
        f"[COMFY-OFFERS] Parsing offers for tracker {tracker_id} URL: {url}")

    try:
        result = asyncio.run(async_parse_retail(url))
        if _is_blocked_or_invalid_result(result):
            raise ValueError(
                "COMFY offers returned anti-bot/invalid page; skipping webhook update"
            )

        webhook_url = f"{settings.BACKEND_API_URL}/webhooks/{tracker_id}/comfy-offers"
        update_data = {
            "last_price": result.get("price"),
            "last_old_price": result.get("old_price"),
            "last_discount_percent": result.get("discount_percent"),
            "last_cashback_amount": result.get("cashback_amount"),
            "last_reviews_count": None,
            "last_views": None,
            "last_personal_price_available": result.get("personal_price_available"),
            "last_gift_offer_available": result.get("gift_offer_available"),
            "last_color": result.get("color"),
            "last_memory_variant": result.get("memory_variant"),
            "last_checked_at": result.get("checked_at"),
        }

        response = httpx.post(webhook_url, json=update_data, timeout=10.0)
        response.raise_for_status()
        logger.info(
            f"[COMFY-OFFERS] Successfully parsed offers for tracker {tracker_id}")
        return result
    except Exception as exc:
        logger.error(
            f"[COMFY-OFFERS] Error parsing offers for tracker {tracker_id}: {str(exc)}")
        raise self.retry(exc=exc, countdown=60)
