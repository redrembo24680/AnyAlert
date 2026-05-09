import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import re


async def test_parse_allo(url: str):
    print(f"Starting ALLO parse: {url}")

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
            await page.wait_for_timeout(3500)

            # Extract title
            print("Searching for title...")
            title = None
            title_el = await page.query_selector('h1')
            if title_el:
                title = (await title_el.inner_text()).strip()

            body = await page.locator('body').inner_text()

            # Extract prices
            print("Searching for price...")
            price = None
            old_price = None

            # Strategy: Find "Купить"/"Замовити" button and get prices nearby
            try:
                buy_btn = await page.query_selector('button:has-text("Замовити"), button:has-text("Купить"), button:has-text("Buy")')
                if buy_btn:
                    print(f"  Found buy button")
                    # Get parent container
                    parent = buy_btn
                    for _ in range(5):
                        parent = await parent.evaluate_handle('el => el.parentElement')
                        if parent:
                            parent_text = await parent.evaluate('el => el.innerText')
                            price_matches = re.findall(
                                r"(\d[\d\s\u00A0]*)\s*₴", parent_text)
                            if price_matches:
                                print(
                                    f"  Found prices in parent: {price_matches}")
                                prices_clean = []
                                for pm in price_matches[:3]:
                                    clean = float(
                                        re.sub(r"[\s\u00A0]", "", pm))
                                    if 100 < clean < 1000000:
                                        prices_clean.append(clean)
                                if prices_clean:
                                    price = prices_clean[-1]
                                    if len(prices_clean) > 1:
                                        old_price = prices_clean[0]
                                break
            except Exception as e:
                print(f"  Error finding price via button: {e}")

            # Fallback
            if not price:
                print("  Fallback: searching for price via regex...")
                price_matches = re.findall(r"(\d[\d\s\u00A0]*)\s*₴", body)
                if price_matches:
                    prices_clean = []
                    for pm in price_matches[:5]:
                        try:
                            clean = float(re.sub(r"[\s\u00A0]", "", pm))
                            if 100 < clean < 1000000:
                                prices_clean.append(clean)
                        except:
                            pass
                    if prices_clean:
                        price = max(prices_clean)

            # Extract availability
            print("Searching for availability...")
            availability = None
            status = None
            if re.search(r"в\s+наявност|в\s+наличии|in stock|available", body, flags=re.I):
                availability = True
                status = "In stock"
            elif re.search(r"немає\s+в\s+наявност|out of stock|sold out", body, flags=re.I):
                availability = False
                status = "Out of stock"

            # Extract rating
            rating = None
            rating_patterns = [
                r"(\d+[.,]\d+)\s*(?:/|из|out of|rating)",
                r"(\d+[.,]\d+)",
            ]
            for pattern in rating_patterns:
                rating_match = re.search(pattern, body, flags=re.I)
                if rating_match:
                    try:
                        rating = float(rating_match.group(1).replace(',', '.'))
                        if 0 <= rating <= 10:
                            print(f"  Found rating: {rating}")
                            break
                    except:
                        pass

            # Extract reviews
            reviews_count = None
            reviews_patterns = [
                r'(\d+)\s*(?:відгук|review|comment|оценк)',
                r'"(\d+)"',
            ]
            for pattern in reviews_patterns:
                reviews_match = re.search(pattern, body, flags=re.I)
                if reviews_match:
                    try:
                        reviews_count = int(reviews_match.group(1))
                        if reviews_count > 0:
                            print(f"  Found reviews: {reviews_count}")
                            break
                    except:
                        pass

            # Extract cashback
            cashback = None
            cb_patterns = [
                r"\+(\d[\d\s\u00A0]*)\s*₴\s*(?:bonus|кешбек|cashback)",
                r"(\d[\d\s\u00A0]*)\s*₴\s*(?:бонус|cashback)",
            ]
            for pattern in cb_patterns:
                cb_match = re.search(pattern, body, flags=re.I)
                if cb_match:
                    try:
                        cashback = float(
                            re.sub(r"[\s\u00A0]", "", cb_match.group(1)))
                        if cashback > 0:
                            print(f"  Found cashback: {cashback}")
                            break
                    except:
                        pass

            print("\n--- ALLO PARSE RESULT ---")
            print(f"Title: {title}")
            print(f"Price: {price}")
            print(f"Old Price: {old_price}")
            print(f"Availability: {availability}")
            print(f"Status: {status}")
            print(f"Rating: {rating}")
            print(f"Reviews: {reviews_count}")
            print(f"Cashback: {cashback}")
            print("-------------------------\n")

        except Exception as e:
            print(f"Error during parsing: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()
            print("Browser closed.")


if __name__ == '__main__':
    url = "https://allo.ua/ua/products/mobile/samsung-galaxy-a57-5g-8-256gb-navy-sm-a576bdbdeuc.html"
    asyncio.run(test_parse_allo(url))
