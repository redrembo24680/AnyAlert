import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import re

async def test_parse_rozetka(url: str):
    print(f"Починаємо парсинг: {url}")
    
    async with async_playwright() as p:
        # Запускаємо браузер. headless=False дозволяє вам бачити, що відбувається
        # Якщо хочете запускати у фоні без вікна браузера, змініть на True
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
            await page.wait_for_timeout(3000)
            
            # Дістаємо назву товару
            print("Шукаємо назву...")
            title_element = await page.query_selector('h1.title__font')
            title = None
            if title_element:
                title = await title_element.inner_text()
                title = title.strip()
            
            # Дістаємо ціну
            print("Шукаємо ціну...")
            price_element = await page.query_selector('.product-price__big')
            price = None
            if price_element:
                price_text = await price_element.inner_text()
                print(f"Знайдено текст ціни: '{price_text}'")
                
                # Очищаємо ціну від пробілів та знаку валюти
                clean_text = re.sub(r'[^\d]', '', price_text)
                if clean_text:
                    price = float(clean_text)
            else:
                print("Елемент ціни (.product-price__big) не знайдено!")
            
            # Дістаємо статус
            print("Шукаємо статус наявності...")
            status_element = await page.query_selector('.status-label')
            status = "невідомо"
            if status_element:
                status = await status_element.inner_text()
                status = status.strip()
            else:
                print("Елемент статусу (.status-label) не знайдено!")
                
            print("\n--- РЕЗУЛЬТАТИ ---")
            print(f"Назва: {title}")
            print(f"Ціна: {price} грн")
            print(f"Статус: {status}")
            print("------------------\n")
            
        except Exception as e:
            print(f"Виникла помилка під час парсингу: {e}")
        finally:
            await browser.close()
            print("Браузер закрито.")

if __name__ == "__main__":
    # URL для тесту
    test_url = "https://bt.rozetka.com.ua/ua/remington_ac9140b/p132415294/"
    
    # Запускаємо асинхронну функцію
    asyncio.run(test_parse_rozetka(test_url))
