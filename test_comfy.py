import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import re


async def test_parse_comfy(url: str):
    print(f"Starting Comfy parse: {url}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)

        try:
            print("Loading page...")
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(4000)

            # Extract title (h1 with КРАЩ badge)
            print("Searching for title...")
            title = None
            title_el = await page.query_selector('h1')
            if title_el:
                title = (await title_el.inner_text()).strip()
                # Remove badge text if present
                title = re.sub(r"^[^\w]*", "", title).strip()

            # Extract current price - find button "Купить" and get price from its container
            print("Searching for price...")
            price = None
            old_price = None

            # Strategy 1: Find "Купить" button and get prices from nearest container
            try:
                buy_btn = await page.query_selector('button:has-text("Купить")')
                if buy_btn:
                    print(f"  Found Купить button")
                    # Get the price container (usually parent divs above the button)
                    parent = buy_btn
                    for _ in range(5):  # Go up 5 levels max
                        parent = await parent.evaluate_handle('el => el.parentElement')
                        if parent:
                            parent_text = await parent.evaluate('el => el.innerText')
                            price_matches = re.findall(
                                r"(\d[\d\s\u00A0]*)\s*₴", parent_text)
                            if price_matches:
                                print(
                                    f"  Found prices in parent: {price_matches}")
                                # First number is usually current or old price
                                if len(price_matches) >= 2:
                                    # Try to pick the right one (usually the largest is old, smallest is new)
                                    prices_clean = []
                                    for pm in price_matches[:3]:  # Take first 3
                                        clean = float(
                                            re.sub(r"[\s\u00A0]", "", pm))
                                        prices_clean.append(clean)
                                    if prices_clean:
                                        # Assuming last is current price (closest to button)
                                        price = prices_clean[-1]
                                        if len(prices_clean) > 1:
                                            old_price = prices_clean[0]
                                break
            except Exception as e:
                print(f"  Error finding price via button: {e}")

            # Fallback: Search for price elements by common patterns
            if not price:
                print("  Fallback: searching for price via text patterns...")
                body = await page.locator('body').inner_text()
                price_matches = re.findall(r"(\d[\d\s\u00A0]*)\s*₴", body)
                if price_matches:
                    # Take the largest number as most likely price
                    prices_clean = []
                    for pm in price_matches[:5]:  # First 5
                        try:
                            clean = float(re.sub(r"[\s\u00A0]", "", pm))
                            if 100 < clean < 1000000:  # Reasonable price range
                                prices_clean.append(clean)
                        except:
                            pass
                    if prices_clean:
                        price = max(prices_clean)
                        print(
                            f"  Fallback prices found: {prices_clean}, using: {price}")

            # Extract availability/status
            print("Searching for availability...")
            availability = None
            status = None
            body = await page.locator('body').inner_text()

            if re.search(r"в\s+наличии|є\s+в\s+наявност|in stock|available", body, flags=re.I):
                availability = True
                status = "В наличии"
            elif re.search(r"немає\s+в\s+наявност|out of stock|sold out|нет в наличии", body, flags=re.I):
                availability = False
                status = "Нет в наличии"

            # Extract rating and reviews count
            rating = None
            reviews_count = None

            # Try to find rating - look for number before slash or "оценка"
            rating_patterns = [
                r"(\d+[.,]\d+)\s*(?:\/|\s+оценк|rating)",  # 4.6 / оценка
                r"(\d+[.,]\d+)\s*(?:/)?",  # Just number with dot/comma
            ]
            for pattern in rating_patterns:
                rating_match = re.search(pattern, body, flags=re.I)
                if rating_match:
                    try:
                        rating = float(rating_match.group(1).replace(',', '.'))
                        print(f"  Found rating: {rating}")
                        break
                    except:
                        pass

            # Try multiple patterns for reviews
            reviews_patterns = [
                r"(\d+)\s*(?:отзыв|відгук|review|comment|проголос)",
                r'"(\d+)"',  # "133" format
            ]
            for pattern in reviews_patterns:
                reviews_match = re.search(pattern, body, flags=re.I)
                if reviews_match:
                    try:
                        reviews_count = int(reviews_match.group(1))
                        print(f"  Found reviews: {reviews_count}")
                        break
                    except:
                        pass

            # Extract cashback
            cashback = None
            cashback_patterns = [
                r"\+(\d[\d\s\u00A0]*)\s*₴\s*(?:на\s+бонус|кешбек|cashback|bonus)",
                r"(\d[\d\s\u00A0]*)\s*₴\s*(?:бонус|на\s+бонусный|cashback)",
                r"\+(\d[\d\s\u00A0]*)\s*₴",  # Just +amount ₴
            ]
            for pattern in cashback_patterns:
                cashback_match = re.search(pattern, body, flags=re.I)
                if cashback_match:
                    try:
                        cashback = float(
                            re.sub(r"[\s\u00A0]", "", cashback_match.group(1)))
                        print(f"  Found cashback: {cashback}")
                        break
                    except:
                        pass

            print("\n--- COMFY PARSE RESULT ---")
            print(f"Title: {title}")
            print(f"Price: {price}")
            print(f"Old Price: {old_price}")
            print(f"Availability: {availability}")
            print(f"Status: {status}")
            print(f"Rating: {rating}")
            print(f"Reviews: {reviews_count}")
            print(f"Cashback: {cashback}")
            print("--------------------------\n")

        except Exception as e:
            print(f"Error during parsing: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()
            print("Browser closed.")


if __name__ == '__main__':
    url = "https://comfy.ua/smartfon-apple-iphone-17-pro-256gb-cosmic-orange.html"
    asyncio.run(test_parse_comfy(url))
