import re
import logging
from datetime import datetime, timezone
from typing import Any, Dict

from playwright.async_api import async_playwright
from playwright_stealth import Stealth

logger = logging.getLogger(__name__)

_PRICE_RE = re.compile(r"(\d[\d\s\u00A0]*)\s*₴")


def _normalize_digits(raw: str) -> float | None:
    digits = re.sub(r"[\s\u00A0]", "", raw)
    if not digits or len(digits) < 2:
        return None
    try:
        value = float(digits)
    except ValueError:
        return None
    return value if 10 <= value <= 1000000 else None


def _extract_prices(text: str) -> list[float]:
    prices: list[float] = []
    for raw in _PRICE_RE.findall(text):
        value = _normalize_digits(raw)
        if value is not None:
            prices.append(value)
    return prices


def _pick_price_pair(prices: list[float]) -> tuple[float | None, float | None]:
    if not prices:
        return None, None
    if len(prices) == 1:
        return prices[0], None

    for index in range(len(prices) - 1, 0, -1):
        first, second = prices[index - 1], prices[index]
        lower = min(first, second)
        higher = max(first, second)
        discount_pct = ((higher - lower) / higher) * 100
        if 5 < discount_pct < 80:
            return lower, higher

    price = prices[-2]
    old_price = prices[-1]
    if price > old_price:
        price, old_price = old_price, price
    return price, old_price


async def async_parse_retail(url: str) -> Dict[str, Any]:
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
        await Stealth().apply_stealth_async(page)

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(2500)

            body_text = await page.locator("body").inner_text()

            title = None
            title_element = await page.query_selector("h1")
            if title_element:
                title = (await title_element.inner_text()).strip()
            if not title:
                og_title_element = await page.query_selector('meta[property="og:title"]')
                if og_title_element:
                    og_title = await og_title_element.get_attribute("content")
                    if og_title:
                        title = og_title.strip()

            if not title:
                try:
                    page_title = await page.title()
                    if page_title:
                        title = page_title.strip()
                except Exception:
                    pass

            # Prefer prices located inside the purchase block (near the Buy button).
            prices = []
            try:
                buy_btn = await page.query_selector('button:has-text("Купить")')
                if buy_btn:
                    parent = await buy_btn.query_selector('xpath=..')
                    if parent:
                        try:
                            container_text = await parent.inner_text()
                        except Exception:
                            container_text = ""
                        prices = _extract_prices(container_text)
            except Exception:
                prices = []

            # Fallback: parse whole body if not found in buy block
            if not prices:
                prices = _extract_prices(body_text)

            price, old_price = _pick_price_pair(prices)
            discount_percent = None
            if price is not None and old_price is not None and old_price > price:
                discount_percent = round(
                    ((old_price - price) / old_price) * 100, 2)

            # Extract rating with multiple patterns
            rating = None
            rating_patterns = [
                r"(\d+[.,]\d+)\s*(?:/\s*5|з 5|/5|оценк|rating)",
                r"(\d+[.,]\d+)\s*(?:\/)?",
            ]
            for pattern in rating_patterns:
                rating_match = re.search(
                    pattern, body_text, flags=re.IGNORECASE)
                if rating_match:
                    try:
                        rating = float(rating_match.group(1).replace(",", "."))
                        break
                    except ValueError:
                        pass

            # Extract reviews count with multiple patterns
            reviews_count = None
            reviews_patterns = [
                r'(\d+)\s*(?:відгук|відгуків|reviews|оценк|проголос)',
                r'"(\d+)"',  # "123" format
                r'(\d+)\s*(?:comment|отзыв)',
            ]
            for pattern in reviews_patterns:
                reviews_match = re.search(
                    pattern, body_text, flags=re.IGNORECASE)
                if reviews_match:
                    try:
                        reviews_count = int(reviews_match.group(1))
                        break
                    except ValueError:
                        pass

            # Cashback: check buy block first then fallback to body
            cashback_amount = None
            try:
                cb_match = None
                # Try multiple patterns for cashback
                cashback_patterns = [
                    r"\+(\d[\d\s\u00A0]*)\s*₴\s*(?:на\s+бонус|кешбек|cashback|bonus)",
                    r"(\d[\d\s\u00A0]*)\s*₴\s*(?:бонус|на\s+бонусный|cashback)",
                    r"\+(\d[\d\s\u00A0]*)\s*₴",
                ]

                # Check buy container first
                if 'container_text' in locals() and container_text:
                    for cb_pattern in cashback_patterns:
                        cb_match = re.search(
                            cb_pattern, container_text, flags=re.IGNORECASE)
                        if cb_match:
                            break

                # Fallback to body
                if not cb_match:
                    for cb_pattern in cashback_patterns:
                        cb_match = re.search(
                            cb_pattern, body_text, flags=re.IGNORECASE)
                        if cb_match:
                            break

                if cb_match:
                    cashback_amount = _normalize_digits(cb_match.group(1))
            except Exception:
                cashback_amount = None

            personal_price_available = bool(
                re.search(
                    (
                        r"персональн[а-яіїєґ]*\s+цiн[а-яіїєґ]*|"
                        r"персональн[а-яіїєґ]*\s+ці[а-яіїєґ]*на|"
                        r"personal price"
                    ),
                    body_text,
                    flags=re.IGNORECASE,
                )
            )
            gift_offer_available = bool(
                re.search(
                    r"подарунк|подарок|gift\s+offer|buy.*with.*gift",
                    body_text,
                    flags=re.IGNORECASE,
                )
            )

            # Try to extract selected color and memory variant from variant blocks
            color = None
            try:
                color_el = await page.query_selector("xpath=//div[contains(.,'Другой цвет')]|//div[contains(.,'Колір')]")
                if color_el:
                    a = await color_el.query_selector('a')
                    if a:
                        color = (await a.inner_text()).strip()
            except Exception:
                color = None

            memory_variant = None
            try:
                mem_el = await page.query_selector("xpath=//div[contains(.,'Память')]|//div[contains(.,"'Память'")]")
                if mem_el:
                    a = await mem_el.query_selector('a')
                    if a:
                        memory_variant = (await a.inner_text()).strip()
            except Exception:
                memory_variant = None

            availability = None
            status = "unknown"
            if re.search(
                r"в\s+наявності|є\s+в\s+наявності|in stock|available",
                body_text,
                flags=re.IGNORECASE,
            ):
                availability = True
                status = "in_stock"
            elif re.search(
                r"немає\s+в\s+наявності|out of stock|sold out",
                body_text,
                flags=re.IGNORECASE,
            ):
                availability = False
                status = "out_of_stock"

            trade_in_available = bool(
                re.search(r"trade-?in|обмін", body_text, flags=re.IGNORECASE)
            )
            credit_available = bool(
                re.search(r"кредит|розстрочка|оплата частинами",
                          body_text, flags=re.IGNORECASE)
            )
            delivery_available = bool(
                re.search(r"доставка", body_text, flags=re.IGNORECASE))
            pickup_available = bool(
                re.search(r"самовивіз|pickup|самовывоз",
                          body_text, flags=re.IGNORECASE)
            )

            return {
                "title": title,
                "price": price,
                "old_price": old_price,
                "discount_percent": discount_percent,
                "cashback_amount": cashback_amount,
                "personal_price_available": personal_price_available,
                "gift_offer_available": gift_offer_available,
                "status": status,
                "availability": availability,
                "rating": rating,
                "reviews_count": reviews_count,
                "trade_in_available": trade_in_available,
                "credit_available": credit_available,
                "delivery_available": delivery_available,
                "pickup_available": pickup_available,
                "color": color,
                "memory_variant": memory_variant,
                "checked_at": datetime.now(timezone.utc).isoformat(),
            }
        finally:
            await browser.close()
