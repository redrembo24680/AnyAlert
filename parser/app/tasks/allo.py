import asyncio
import logging

import httpx

from app.config import settings
from app.worker import celery_app
from app.tasks.retail_common import async_parse_retail

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def parse_allo_product(self, tracker_id: int, url: str):
    logger.info(f"Parsing ALLO tracker {tracker_id} for URL: {url}")

    try:
        result = asyncio.run(async_parse_retail(url))

        webhook_url = f"{settings.BACKEND_API_URL}/webhooks/{tracker_id}/allo"
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
            f"Successfully parsed and updated ALLO tracker {tracker_id}")
        return result
    except Exception as exc:
        logger.error(f"Error parsing ALLO tracker {tracker_id}: {str(exc)}")
        raise self.retry(exc=exc, countdown=60)
