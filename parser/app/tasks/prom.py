import logging
import asyncio

import httpx

from app.config import settings
from app.worker import celery_app
from app.tasks.retail_common import async_parse_retail

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def parse_prom_product(self, tracker_id: int, url: str):
    logger.info(f"Parsing PROM tracker {tracker_id} for URL: {url}")

    try:
        result = asyncio.run(async_parse_retail(url))

        webhook_url = f"{settings.BACKEND_API_URL}/trackers/{tracker_id}/webhook"
        update_data = {
            "title": result.get("title"),
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
            f"Successfully parsed and updated PROM tracker {tracker_id}")
        return result
    except Exception as exc:
        logger.error(f"Error parsing PROM tracker {tracker_id}: {str(exc)}")
        raise self.retry(exc=exc, countdown=60)
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
            await page.wait_for_timeout(2500)

            # Title
            title = None
            title_el = await page.query_selector("h1")
            if title_el:
                title = (await title_el.inner_text()).strip()
            if not title:
                og = await page.get_attribute('meta[property="og:title"]', 'content')
                if og:
                    title = og.strip()

            body_text = await page.locator('body').inner_text()

            # Current price and old price extraction
            price = None
            old_price = None
            discount_percent = None

            # Try to find price in specific selectors first (Prom.ua structure)
            price_selectors = [
                "div.product-price",
                "[data-testid*='price']",
                "span.price",
                "div[class*='price']"
            ]

            for selector in price_selectors:
                try:
                    price_text = await page.locator(selector).first.inner_text()
                    if price_text:
                        # Extract all numbers from the found element
                        prices_in_element = re.findall(
                            r"(\d[\d\s\u00A0]*)\s*₴", price_text)
                        if prices_in_element:
                            try:
                                # First price is current, second is old
                                digits = re.sub(
                                    r"[\s\u00A0]", "", prices_in_element[0])
                                price = float(digits)
                                if len(prices_in_element) > 1:
                                    digits = re.sub(
                                        r"[\s\u00A0]", "", prices_in_element[1])
                                    old_price = float(digits)
                                break
                            except ValueError:
                                pass
                except:
                    pass

            # Fallback: search body text for price patterns if not found via selectors
            # Filter out prices with excessive newlines/spaces (like "41\n2 295")
            if not price:
                all_prices_raw = re.findall(
                    r"(\d[\d\s\u00A0]*)\s*₴", body_text)
                # Filter: keep only valid prices (3-5 digits, reasonable range)
                valid_prices = []
                for price_str in all_prices_raw:
                    # Extract just the digits
                    digit_count = re.sub(r"[\s\u00A0\n]", "", price_str)
                    # Only accept if it's a reasonable price (2-6 digit number)
                    if 2 <= len(digit_count) <= 6:
                        try:
                            val = float(digit_count)
                            # Reasonable price range for products (10 UAH - 1M UAH)
                            if 10 <= val <= 1000000:
                                valid_prices.append(val)
                        except ValueError:
                            pass

                # Smart filtering: look for a pair where one is notably less than the other
                if len(valid_prices) >= 2:
                    # Try to find the best price pair by looking for a discount relationship
                    # Start from the end and work backwards to find a valid pair
                    for i in range(len(valid_prices) - 1, 0, -1):
                        p1, p2 = valid_prices[i - 1], valid_prices[i]

                        # Check if these form a valid price/old_price pair
                        # One should be 5-80% less than the other
                        if p1 < p2:
                            discount_pct = ((p2 - p1) / p2) * 100
                            if 5 < discount_pct < 80:
                                price = p1
                                old_price = p2
                                break
                        else:
                            discount_pct = ((p1 - p2) / p1) * 100
                            if 5 < discount_pct < 80:
                                price = p2
                                old_price = p1
                                break

                    # Fallback: if no discount pair found, just use last two
                    if price is None:
                        price = valid_prices[-2]
                        old_price = valid_prices[-1]
                        if price > old_price:
                            price, old_price = old_price, price
                elif valid_prices:
                    price = valid_prices[-1]

            # Calculate discount if both prices exist
            if price and old_price and old_price > price:
                discount_percent = round(
                    ((old_price - price) / old_price) * 100, 2)

            # Status / availability
            status = None
            availability = None
            # Check for common availability phrases
            if re.search(r"\b(Готово до відправки|В наявності|є в наявності|На складі|In stock)\b", body_text, flags=re.IGNORECASE):
                availability = True
                status = "in_stock"
            elif re.search(r"\b(Немає в наявності|відсутній|sold out|out of stock)\b", body_text, flags=re.IGNORECASE):
                availability = False
                status = "out_of_stock"
            else:
                # fallback to picking a short status snippet around price area
                status = "unknown"

            # Seller rating: look for percentage like "92%" or numeric rating
            rating = None
            rating_match = re.search(r"(\d{1,3})\s*%", body_text)
            if rating_match:
                try:
                    rating = float(rating_match.group(1))
                except ValueError:
                    rating = None

            # Reviews count (if present)
            reviews = None
            reviews_match = re.search(r"Відгуки[\w\s]*\D(\d{1,6})", body_text)
            if reviews_match:
                try:
                    reviews = int(reviews_match.group(1))
                except ValueError:
                    reviews = None

            return {
                "title": title,
                "price": price,
                "old_price": old_price,
                "discount_percent": discount_percent,
                "status": status,
                "availability": availability,
                "rating": rating,
                "reviews": reviews,
                "checked_at": datetime.now(timezone.utc).isoformat()
            }
        finally:
            await browser.close()


@celery_app.task(bind=True, max_retries=3)
def parse_prom_product(self, tracker_id: int, url: str):
    logger.info(f"Parsing PROM tracker {tracker_id} for URL: {url}")

    try:
        result = asyncio.run(async_parse_prom(url))

        # Send result back to backend
        webhook_url = f"{settings.BACKEND_API_URL}/trackers/{tracker_id}/webhook"
        update_data = {
            "title": result.get("title"),
            "last_price": result["price"],
            "last_old_price": result.get("old_price"),
            "last_discount_percent": result.get("discount_percent"),
            "last_status": result.get("status"),
            "last_availability": result.get("availability"),
            "last_rating": result.get("rating"),
            # Prom returns `reviews` (number of reviews) — map it to `last_views`
            "last_views": result.get("reviews"),
            "last_checked_at": result.get("checked_at")
        }

        response = httpx.post(webhook_url, json=update_data, timeout=10.0)
        response.raise_for_status()

        logger.info(
            f"Successfully parsed and updated PROM tracker {tracker_id}")
        return result

    except Exception as exc:
        logger.error(f"Error parsing PROM tracker {tracker_id}: {str(exc)}")
        raise self.retry(exc=exc, countdown=60)
