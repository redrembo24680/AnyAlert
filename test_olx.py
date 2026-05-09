import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import re


async def test_parse_olx(url: str):
    print(f"Починаємо парсинг OLX: {url}")

    async with async_playwright() as p:
        # Запускаємо браузер. headless=False дозволяє вам бачити, що відбувається
        browser = await p.chromium.launch(headless=False)

        # Налаштовуємо контекст
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        # Застосовуємо stealth
        await Stealth().apply_stealth_async(page)

        try:
            print("Завантаження сторінки OLX...")
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)

            # Чекаємо, щоб відпрацювали JS-скрипти
            await page.wait_for_timeout(5000)

            # Дістаємо назву товару
            print("Шукаємо назву...")
            title_element = await page.query_selector('h1')
            title = None
            if title_element:
                title = await title_element.inner_text()
                title = title.strip()
            if not title:
                og_title = await page.get_attribute('meta[property="og:title"]', 'content')
                if og_title:
                    title = og_title.strip()
            if not title:
                doc_title = await page.title()
                if doc_title:
                    title = doc_title.split(':', 1)[0].strip()

            # Дістаємо ціну
            print("Шукаємо ціну...")
            # Спробуємо кілька селекторів
            price = None
            price_selectors = [
                'div[data-testid="ad-price"]',
                'h2:has-text("грн")',
                'text=/\\d+\\s*грн/'
            ]

            for selector in price_selectors:
                try:
                    price_element = await page.query_selector(selector)
                    if price_element:
                        price_text = await price_element.inner_text()
                        print(f"Знайдено текст ціни: '{price_text}'")

                        # Витяг чисел
                        price_match = re.search(
                            r'(\d+(?:\s+\d+)*)', price_text)
                        if price_match:
                            price_str = price_match.group(1).replace(' ', '')
                            price = float(price_str)
                            break
                except:
                    pass

            if not price:
                print("Елемент ціни не знайдено!")

            # Дістаємо статус/стан товару
            print("Шукаємо стан товару...")
            status = "невідомо"
            status_element = await page.query_selector('text=/Стан:/i')
            if status_element:
                status = await status_element.inner_text()
                status = status.strip()
            else:
                print("Елемент стану не знайдено!")

            # Дістаємо кількість переглядів
            print("Шукаємо кількість переглядів...")
            views = None
            views_element = None

            # Пробуємо знайти і доскролити саме до блоку з переглядами.
            try:
                views_element = await page.wait_for_selector('[data-testid="page-view-counter"]', timeout=2000)
                await views_element.scroll_into_view_if_needed()
                await page.wait_for_timeout(600)
            except Exception:
                views_element = None

            if views_element is None:
                print("⚠️ Лічильник не у в'юпорті, скролю донизу...")
                for _ in range(6):
                    await page.mouse.wheel(0, 1400)
                    await page.wait_for_timeout(700)
                    try:
                        views_element = await page.wait_for_selector('[data-testid="page-view-counter"]', timeout=1200)
                        await views_element.scroll_into_view_if_needed()
                        await page.wait_for_timeout(600)
                        break
                    except Exception:
                        views_element = None

            if views_element:
                views_text = await views_element.inner_text()
                print(
                    f"✅ Знайдено переглядів через [data-testid]: '{views_text}'")
                views_match = re.search(r'([\d\s\u00A0]+)', views_text)
                if views_match:
                    digits = re.sub(r'[\s\u00A0]', '', views_match.group(1))
                    views = int(digits)

            if views is None:
                print("⚠️ Шукаю перегляди в тексті всієї сторінки...")
                body_text = await page.locator('body').inner_text()
                views_match = re.search(
                    r'Перегляд\w*[:\s]*([\d\s\u00A0]+)', body_text, flags=re.IGNORECASE)
                if not views_match:
                    views_match = re.search(
                        r'просмотр\w*[:\s]*([\d\s\u00A0]+)', body_text, flags=re.IGNORECASE)
                if views_match:
                    digits = re.sub(r'[\s\u00A0]', '', views_match.group(1))
                    views = int(digits)
                    print(f"✅ Знайдено перегляди з body-text: {views}")

            if not views:
                print("⚠️  Кількість переглядів не знайдена!")

            # Дістаємо рейтинг продавця
            print("Шукаємо рейтинг продавця...")
            rating = None
            rating_elements = await page.query_selector_all('p')
            if rating_elements:
                for elem in rating_elements:
                    rating_text = await elem.inner_text()
                    print(f"Перевіряємо параграф: '{rating_text}'")

                    # Ищем паттерн типа "4.9 / 5"
                    rating_match = re.search(
                        r'(\d+\.?\d*)\s*\/\s*5', rating_text)
                    if rating_match:
                        try:
                            rating = float(rating_match.group(1))
                            print(f"Знайдено рейтинг: {rating}")
                            break
                        except ValueError:
                            pass

            if not rating:
                print("Рейтинг не знайдено!")

            # Перевіряємо наявність товару
            print("Перевіряємо наявність...")
            availability = True
            removed_element = await page.query_selector('text=/Видалено|Closed|Inactive/i')
            if removed_element:
                availability = False
                print("Товар видалено або неактивний!")

            # Виводимо результати
            print("\n--- РЕЗУЛЬТАТИ OLX ---")
            print(f"Назва: {title}")
            print(f"Ціна: {price} грн" if price else "Ціна: не знайдена")
            print(f"Стан: {status}")
            print(
                f"Переглядів: {views}" if views else "Переглядів: не знайдено")
            print(f"Рейтинг: {rating}" if rating else "Рейтинг: не знайдено")
            print(
                f"Наявність: {'✅ Доступно' if availability else '❌ Недоступно'}")
            print("------------------\n")

        except Exception as e:
            print(f"Виникла помилка під час парсингу: {e}")
        finally:
            await browser.close()
            print("Браузер закрито.")

if __name__ == "__main__":
    # URL для тесту
    test_url = "https://www.olx.ua/d/uk/obyavlenie/poverbank-opt-powerbank-20000-paverbank-shvidka-zaryadka-22-5w-IDZh8ty.html"

    # Запускаємо асинхронну функцію
    asyncio.run(test_parse_olx(test_url))
