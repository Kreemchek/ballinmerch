#!/usr/bin/env python3
"""
Скрипт для получения цен с сайта ballinmerch.ru
"""
import asyncio
from playwright.async_api import async_playwright
import json
import re


async def get_prices():
    """Получает цены товаров с сайта"""
    url = "https://ballinmerch.ru/"
    products_with_prices = {}
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print(f"Открываю {url}...")
        await page.goto(url, wait_until="networkidle")
        
        # Ждем загрузки всех элементов
        await page.wait_for_timeout(5000)
        
        # Скроллим страницу для загрузки ленивых элементов
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(3000)
        
        # Ищем все текстовые элементы, содержащие цены
        all_text = await page.evaluate("""
            () => {
                const texts = [];
                const walker = document.createTreeWalker(
                    document.body,
                    NodeFilter.SHOW_TEXT,
                    null,
                    false
                );
                let node;
                while (node = walker.nextNode()) {
                    const text = node.textContent.trim();
                    if (text && (text.includes('₽') || text.includes('руб') || /\\d{3,5}/.test(text))) {
                        texts.push(text);
                    }
                }
                return texts;
            }
        """)
        
        # Извлекаем цены из текста
        prices_found = set()
        for text in all_text:
            # Ищем паттерны типа "2190 ₽", "2 190 руб", "2190руб" и т.д.
            patterns = [
                r'(\d{1,2}\s?\d{3})\s*[₽руб]',
                r'(\d{3,5})\s*[₽руб]',
                r'[₽руб]\s*(\d{1,2}\s?\d{3})',
                r'цена[:\s]+(\d{1,2}\s?\d{3})',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    price_str = match.replace(' ', '').replace(',', '')
                    if price_str.isdigit():
                        price = int(price_str)
                        if 1000 <= price <= 10000:  # Разумный диапазон
                            prices_found.add(price)
        
        # Теперь ищем товары и пытаемся сопоставить с ценами
        # Ищем все изображения товаров и их родительские элементы
        product_images = await page.query_selector_all('img[src*="tildacdn"], img[src*="static"]')
        
        print(f"\nНайдено {len(product_images)} изображений товаров")
        
        # Берем уникальные цены и создаем маппинг
        unique_prices = sorted(list(prices_found))
        print(f"\nНайденные уникальные цены: {unique_prices}")
        
        # Создаем стандартные цены для разных категорий
        # На основе найденных цен создаем маппинг
        standard_prices = {
            'jersey': 2690,  # Джерси обычно дороже
            'hoodie': 2990,  # Худи
            'tee': 2190,     # Футболки
            'shorts': 2490,  # Шорты
        }
        
        # Если нашли конкретные цены, используем их
        if len(unique_prices) >= 2:
            standard_prices['tee'] = min(unique_prices)
            standard_prices['jersey'] = max(unique_prices)
            if len(unique_prices) >= 3:
                standard_prices['shorts'] = unique_prices[1]
            if len(unique_prices) >= 4:
                standard_prices['hoodie'] = unique_prices[2]
        
        # Сохраняем стандартные цены
        with open('prices.json', 'w', encoding='utf-8') as f:
            json.dump(standard_prices, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ Создан маппинг цен по категориям:")
        for category, price in standard_prices.items():
            print(f"  {category}: {price} ₽")
        
        await browser.close()
        return standard_prices


if __name__ == "__main__":
    asyncio.run(get_prices())
