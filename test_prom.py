#!/usr/bin/env python3
import asyncio
import re
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from datetime import datetime, timezone


async def test_parse_prom(url: str):
    print(f"Починаємо парсинг: {url}")

    async with async_playwright() as p:
        # Запускаємо браузер. headless=False дозволяє вам бачити, що відбувається
        browser = await p.chromium.launch(headless=False)

        # Налаштовуємо контекст (userAgent важливий для обходу захисту)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        # Застосовуємо stealth для приховування від анти-бот систем
        await Stealth().apply_stealth_async(page)

        try:
            print("Завантаження сторінки...")
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)

            # Трохи почекаємо, щоб відпрацювали JS-скрипти на сторінці
            await page.wait_for_timeout(2500)

            # Дістаємо назву товару
            print("Шукаємо назву...")
            title = None
            title_el = await page.query_selector("h1")
            if title_el:
                title = (await title_el.inner_text()).strip()
            if not title:
                og = await page.get_attribute('meta[property="og:title"]', 'content')
                if og:
                    title = og.strip()

            # Дістаємо весь текст сторінки для парсингу цін
            body_text = await page.locator('body').inner_text()

            # Дістаємо поточну ціну та стару ціну
            print("Шукаємо ціни...")
            price = None
            old_price = None
            discount_percent = None

            # Витягуємо всі ціни зі сторінки
            all_prices_raw = re.findall(r"(\d[\d\s\u00A0]*)\s*₴", body_text)
            
            # Фільтруємо ціни (видаляємо ті, що розбиті на кілька рядків)
            valid_prices = []
            for price_str in all_prices_raw:
                # Витягуємо тільки цифри
                digit_count = re.sub(r"[\s\u00A0\n]", "", price_str)
                # Приймаємо ціни з 2-6 цифрами
                if 2 <= len(digit_count) <= 6:
                    try:
                        val = float(digit_count)
                        # Розумний діапазон цін (10 - 1 000 000 грн)
                        if 10 <= val <= 1000000:
                            valid_prices.append(val)
                    except ValueError:
                        pass

            # Розумна фільтрація: шукаємо пару з реалістичною знижкою
            if len(valid_prices) >= 2:
                # Шукаємо з кінця назад - шукаємо пару з знижкою 5-80%
                for i in range(len(valid_prices) - 1, 0, -1):
                    p1, p2 = valid_prices[i - 1], valid_prices[i]
                    
                    # Перевіряємо, чи це дійсна пара ціна/стара ціна
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
                
                # Запасний варіант: якщо не знайшли пару з знижкою, беремо останні дві
                if price is None:
                    price = valid_prices[-2]
                    old_price = valid_prices[-1]
                    if price > old_price:
                        price, old_price = old_price, price
            elif valid_prices:
                price = valid_prices[-1]

            # Розраховуємо відсоток знижки
            if price and old_price and old_price > price:
                discount_percent = round(((old_price - price) / old_price) * 100, 2)

            # Дістаємо статус наявності
            print("Шукаємо статус наявності...")
            status = "невідомо"
            availability = False
            if re.search(r"\b(Готово до відправки|В наявності|є в наявності|На складі|In stock)\b", body_text, flags=re.IGNORECASE):
                availability = True
                status = "Є в наявності"
            elif re.search(r"\b(Немає в наявності|відсутній|sold out|out of stock)\b", body_text, flags=re.IGNORECASE):
                availability = False
                status = "Немає в наявності"

            # Дістаємо рейтинг
            print("Шукаємо рейтинг...")
            rating = None
            rating_match = re.search(r"(\d{1,3})\s*%", body_text)
            if rating_match:
                try:
                    rating = float(rating_match.group(1))
                except ValueError:
                    rating = None

            # Дістаємо кількість відгуків
            reviews = None
            reviews_match = re.search(r"Відгуки[\w\s]*\D(\d{1,6})", body_text)
            if reviews_match:
                try:
                    reviews = int(reviews_match.group(1))
                except ValueError:
                    reviews = None

            print("\n--- РЕЗУЛЬТАТИ ---")
            print(f"Назва: {title}")
            print(f"Поточна ціна: {price} грн" if price else "Поточна ціна: не знайдена")
            print(
                f"Стара ціна: {old_price} грн" if old_price else "Старої ціни нема (немає знижки)")
            print(
                f"Відсоток знижки: {discount_percent}%" if discount_percent else "Знижки нема")
            print(f"Статус: {status}")
            print(
                f"Наявність: {'✅ Є в наявності' if availability else '❌ Немає в наявності'}")
            print(f"Рейтинг: {rating}%" if rating else "Рейтинг не знайдено")
            print(f"Кількість відгуків: {reviews}" if reviews else "Відгуки не знайдені")
            print("------------------\n")

        except Exception as e:
            print(f"Виникла помилка під час парсингу: {e}")
            raise
        finally:
            await browser.close()
            print("Браузер закрито.")

if __name__ == "__main__":
    # URL для тесту
    test_url = "https://prom.ua/ua/p2994053180-nike-air-jordan.html"

    # Запускаємо асинхронну функцію
    asyncio.run(test_parse_prom(test_url))
