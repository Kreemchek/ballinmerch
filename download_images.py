#!/usr/bin/env python3
"""
Скрипт для скачивания всех изображений с сайта ballinmerch.ru
"""
import asyncio
import os
import urllib.parse
from pathlib import Path
from playwright.async_api import async_playwright


async def download_images():
    """Скачивает все изображения с сайта"""
    url = "https://ballinmerch.ru/"
    images_dir = Path("images")
    images_dir.mkdir(exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        print(f"Открываю {url}...")
        await page.goto(url, wait_until="networkidle")
        
        # Ждем загрузки всех изображений
        await page.wait_for_timeout(3000)
        
        # Находим все изображения
        images = await page.query_selector_all("img")
        print(f"Найдено {len(images)} изображений")
        
        downloaded = set()
        count = 0
        
        for img in images:
            try:
                # Получаем src изображения
                src = await img.get_attribute("src")
                if not src:
                    src = await img.get_attribute("data-src")
                
                if not src:
                    continue
                
                # Преобразуем относительный URL в абсолютный
                if src.startswith("//"):
                    src = "https:" + src
                elif src.startswith("/"):
                    src = urllib.parse.urljoin(url, src)
                elif not src.startswith("http"):
                    src = urllib.parse.urljoin(url, src)
                
                # Пропускаем data: URLs и уже скачанные
                if src.startswith("data:") or src in downloaded:
                    continue
                
                downloaded.add(src)
                
                # Получаем имя файла
                parsed_url = urllib.parse.urlparse(src)
                filename = os.path.basename(parsed_url.path)
                if not filename or "." not in filename:
                    filename = f"image_{count}.jpg"
                
                filepath = images_dir / filename
                
                # Скачиваем изображение
                print(f"Скачиваю: {src}")
                response = await page.request.get(src)
                
                if response.status == 200:
                    with open(filepath, "wb") as f:
                        f.write(await response.body())
                    count += 1
                    print(f"✓ Сохранено: {filepath}")
                else:
                    print(f"✗ Ошибка {response.status}: {src}")
                    
            except Exception as e:
                print(f"✗ Ошибка при обработке изображения: {e}")
                continue
        
        # Также ищем изображения в CSS (background-image)
        print("\nПоиск изображений в CSS...")
        styles = await page.query_selector_all("style, link[rel='stylesheet']")
        css_images = set()
        
        for style in styles:
            try:
                if await style.get_attribute("rel") == "stylesheet":
                    href = await style.get_attribute("href")
                    if href:
                        css_url = urllib.parse.urljoin(url, href)
                        css_response = await page.request.get(css_url)
                        if css_response.status == 200:
                            css_content = await css_response.text()
                            # Ищем url() в CSS
                            import re
                            urls = re.findall(r'url\(["\']?([^"\')]+)["\']?\)', css_content)
                            for css_url_path in urls:
                                if css_url_path.startswith("http"):
                                    css_images.add(css_url_path)
                                else:
                                    css_images.add(urllib.parse.urljoin(css_url, css_url_path))
                else:
                    css_content = await style.inner_text()
                    import re
                    urls = re.findall(r'url\(["\']?([^"\')]+)["\']?\)', css_content)
                    for css_url_path in urls:
                        if css_url_path.startswith("http"):
                            css_images.add(css_url_path)
                        elif not css_url_path.startswith("data:"):
                            css_images.add(urllib.parse.urljoin(url, css_url_path))
            except Exception as e:
                print(f"Ошибка при обработке CSS: {e}")
        
        # Скачиваем изображения из CSS
        for img_url in css_images:
            if img_url in downloaded or img_url.startswith("data:"):
                continue
            
            try:
                downloaded.add(img_url)
                parsed_url = urllib.parse.urlparse(img_url)
                filename = os.path.basename(parsed_url.path)
                if not filename or "." not in filename:
                    filename = f"css_image_{count}.png"
                
                filepath = images_dir / filename
                print(f"Скачиваю из CSS: {img_url}")
                response = await page.request.get(img_url)
                
                if response.status == 200:
                    with open(filepath, "wb") as f:
                        f.write(await response.body())
                    count += 1
                    print(f"✓ Сохранено: {filepath}")
            except Exception as e:
                print(f"✗ Ошибка: {e}")
        
        await browser.close()
        print(f"\n✓ Всего скачано {count} изображений в папку {images_dir}/")


if __name__ == "__main__":
    asyncio.run(download_images())

