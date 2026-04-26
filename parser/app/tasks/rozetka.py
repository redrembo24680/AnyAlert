import logging
import asyncio
from typing import Dict, Any, List
import httpx
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from app.worker import celery_app
from app.config import settings
from datetime import datetime, timezone

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
                
    except Exception as exc:
        logger.error(f"Failed to fetch trackers: {exc}")

async def async_parse_rozetka(url: str) -> Dict[str, Any]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
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
            
            # Extract price
            # Rozetka usually has price in .product-price__big
            price_element = await page.query_selector('.product-price__big')
            price = None
            if price_element:
                price_text = await price_element.inner_text()
                # Clean up price (e.g. "1 999 ₴" -> 1999.0)
                price_text = price_text.replace('\xa0', '').replace(' ', '').replace('₴', '').strip()
                try:
                    price = float(price_text)
                except ValueError:
                    pass
            
            # Extract status
            # Rozetka usually has status in .status-label
            status_element = await page.query_selector('.status-label')
            status = "unknown"
            if status_element:
                status = await status_element.inner_text()
                status = status.strip()
                
            return {
                "title": title,
                "price": price,
                "status": status,
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
        
        # Send result back to backend
        webhook_url = f"{settings.BACKEND_API_URL}/trackers/{tracker_id}/webhook"
        update_data = {
            "title": result.get("title"),
            "last_price": result["price"],
            "last_status": result["status"],
            "last_checked_at": result["checked_at"]
        }
        
        response = httpx.post(webhook_url, json=update_data, timeout=10.0)
        response.raise_for_status()
        
        logger.info(f"Successfully parsed and updated tracker {tracker_id}")
        return result
        
    except Exception as exc:
        logger.error(f"Error parsing tracker {tracker_id}: {str(exc)}")
        raise self.retry(exc=exc, countdown=60)
