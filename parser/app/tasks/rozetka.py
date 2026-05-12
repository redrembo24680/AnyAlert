import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict

import httpx
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

from app.config import settings
from app.worker import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def fetch_and_parse_all(self):
    """
    Periodic task to fetch all active trackers from backend and enqueue parse tasks.
    """
    logger.info("Fetching active trackers from backend...")

    url = f"{settings.BACKEND_API_URL}/trackers/active"
    try:
        response = httpx.get(url, timeout=10.0)
        response.raise_for_status()
        trackers = response.json()

        logger.info(f"Found {len(trackers)} active trackers.")
        for tracker in trackers:
            if tracker.get('network') == 'rozetka':
                parse_rozetka_product.delay(tracker['id'], tracker['url'])
            elif tracker.get('network') == 'olx':
                from app.tasks.olx import parse_olx_product
                parse_olx_product.delay(tracker['id'], tracker['url'])
            elif tracker.get('network') == 'prom':
                from app.tasks.prom import parse_prom_product
                parse_prom_product.delay(tracker['id'], tracker['url'])
            elif tracker.get('network') == 'allo':
                from app.tasks.allo import parse_allo_product
                parse_allo_product.delay(tracker['id'], tracker['url'])
            elif tracker.get('network') == 'comfy':
                from app.tasks.comfy import parse_comfy_offers, parse_comfy_product
                parse_comfy_product.delay(tracker['id'], tracker['url'])
                parse_comfy_offers.delay(tracker['id'], tracker['url'])
            elif tracker.get('network') == 'foxtrot':
                from app.tasks.foxtrot import parse_foxtrot_offers, parse_foxtrot_product
                parse_foxtrot_product.delay(tracker['id'], tracker['url'])
                parse_foxtrot_offers.delay(tracker['id'], tracker['url'])

    except Exception as exc:
        logger.error(f"Failed to fetch trackers: {exc}")


async def async_parse_rozetka(url: str) -> Dict[str, Any]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )
        page = await context.new_page()

        # Apply stealth to bypass basic bot protection
        await Stealth().apply_stealth_async(page)

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)

            # Extract title
            title_element = await page.query_selector('h1.title__font')
            title = None
            if title_element:
                title = await title_element.inner_text()
                title = title.strip()

            # Extract current price (new price)
            # Rozetka usually has price in .product-price__big
            price_element = await page.query_selector('.product-price__big')
            price = None
            if price_element:
                price_text = await price_element.inner_text()
                # Clean up price (e.g. "1 999 ₴" -> 1999.0)
                price_text = price_text.replace('\xa0', '').replace(
                    ' ', '').replace('₴', '').strip()
                try:
                    price = float(price_text)
                except ValueError:
                    pass

            # Extract old price (if discount exists)
            # Rozetka has old price in .product-price__small
            old_price = None
            discount_percent = None
            old_price_element = await page.query_selector('.product-price__small')
            if old_price_element:
                old_price_text = await old_price_element.inner_text()
                # Clean up old price (e.g. "3 045 ₴" -> 3045.0)
                old_price_text = old_price_text.replace(
                    '\xa0', '').replace(' ', '').replace('₴', '').strip()
                try:
                    old_price = float(old_price_text)
                    # Calculate discount percentage if both prices exist
                    if price and old_price and old_price > price:
                        discount_percent = round(
                            ((old_price - price) / old_price) * 100, 2)
                except ValueError:
                    pass

            # Extract status/availability
            # Rozetka usually has status in .status-label
            status_element = await page.query_selector('.status-label')
            status = "unknown"
            availability = False
            if status_element:
                status = await status_element.inner_text()
                status = status.strip()
                # Check if product is in stock
                availability = "Є в наявності" in status or "в наличии" in status.lower(
                ) or "available" in status.lower()

            # Extract rating
            # Rozetka has rating in span with classes text-xl font-bold
            rating_element = await page.query_selector('span.text-xl.font-bold')
            rating = None
            if rating_element:
                rating_text = await rating_element.inner_text()
                # Clean up rating (e.g. "4.92/" -> 4.92)
                rating_text = rating_text.replace('/', '').strip()
                try:
                    rating = float(rating_text)
                except ValueError:
                    pass

            # Extract body text for regex-based fields
            body_text = await page.locator("body").inner_text()

            # Cashback (Rozetka uses bonus points displayed as "+ X бонусів" or cashback)
            cashback_amount = None
            cashback_patterns = [
                r"\+\s*(\d[\d\s\u00A0]*)\s*(?:бонус|грн\s+кешбек|cashback)",
                r"(\d[\d\s\u00A0]*)\s*(?:бонус[ів]*|cashback)",
            ]
            for cb_pattern in cashback_patterns:
                cb_match = re.search(cb_pattern, body_text, flags=re.IGNORECASE)
                if cb_match:
                    digits = re.sub(r"[\s\u00A0]", "", cb_match.group(1))
                    try:
                        val = float(digits)
                        if 1 <= val <= 100000:
                            cashback_amount = val
                            break
                    except ValueError:
                        pass

            trade_in_available = bool(
                re.search(r"trade-?in|обмін\s+старого", body_text, flags=re.IGNORECASE)
            )
            credit_available = bool(
                re.search(r"кредит|розстрочка|оплата\s+частинами", body_text, flags=re.IGNORECASE)
            )
            gift_offer_available = bool(
                re.search(r"подарун|gift\s+offer|у\s+подарунок", body_text, flags=re.IGNORECASE)
            )
            personal_price_available = bool(
                re.search(
                    r"персональн[а-яіїєґ]*\s+цін|personal\s+price",
                    body_text,
                    flags=re.IGNORECASE,
                )
            )

            return {
                "title": title,
                "price": price,
                "old_price": old_price,
                "discount_percent": discount_percent,
                "status": status,
                "availability": availability,
                "rating": rating,
                "views": None,
                "reviews_count": None,
                "cashback_amount": cashback_amount,
                "trade_in_available": trade_in_available,
                "credit_available": credit_available,
                "gift_offer_available": gift_offer_available,
                "personal_price_available": personal_price_available,
                "checked_at": datetime.now(timezone.utc).isoformat()
            }
        finally:
            await browser.close()


@celery_app.task(bind=True, max_retries=3)
def parse_rozetka_product(self, tracker_id: int, url: str):
    """
    Parse a single Rozetka product using Playwright.
    """
    logger.info(f"Parsing tracker {tracker_id} for URL: {url}")

    try:
        # Run the async playwright parser in the synchronous celery task
        result = asyncio.run(async_parse_rozetka(url))

        # Send result back to backend (rozetka_tracker_data table)
        webhook_url = f"{settings.BACKEND_API_URL}/webhooks/{tracker_id}/rozetka"
        update_data = {
            "last_price": result["price"],
            "last_old_price": result["old_price"],
            "last_discount_percent": result["discount_percent"],
            "last_status": result["status"],
            "last_availability": result["availability"],
            "last_rating": result["rating"],
            "last_views": result["views"],
            "last_reviews_count": result["reviews_count"],
            "last_cashback_amount": result["cashback_amount"],
            "last_trade_in_available": result["trade_in_available"],
            "last_credit_available": result["credit_available"],
            "last_gift_offer_available": result["gift_offer_available"],
            "last_personal_price_available": result["personal_price_available"],
            "last_checked_at": result["checked_at"]
        }

        response = httpx.post(webhook_url, json=update_data, timeout=10.0)
        response.raise_for_status()

        logger.info(f"Successfully parsed and updated tracker {tracker_id}")
        return result

    except Exception as exc:
        logger.error(f"Error parsing tracker {tracker_id}: {str(exc)}")
        raise self.retry(exc=exc, countdown=60)
