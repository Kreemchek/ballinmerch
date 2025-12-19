#!/usr/bin/env python3
"""
Скрапит каталог товаров с https://ballinmerch.ru/ и сохраняет в catalog.json

Что собираем по каждому товару:
- id (productLid)
- title (название)
- sku
- badge (NEW / -20% и т.п.)
- category (tshirt/hoodie/shorts/longsleeve)
- price_current, price_old
- images: front/back (берем data-original если есть)
"""

import asyncio
import json
import re
from pathlib import Path

from playwright.async_api import async_playwright


def _to_int(value: str | None) -> int | None:
    if not value:
        return None
    s = re.sub(r"[^\d]", "", value)
    if not s:
        return None
    try:
        return int(s)
    except ValueError:
        return None


async def scrape_catalog() -> list[dict]:
    url = "https://ballinmerch.ru/"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 900})

        await page.goto(url, wait_until="networkidle")
        await page.wait_for_timeout(3500)

        # Убираем TG-попап, чтобы не мешал взаимодействию/DOM (на всякий)
        await page.evaluate(
            """
            () => {
              document.querySelectorAll('.t-popup_show[data-tooltip-hook="#popup:tg"]').forEach(p => p.style.display='none');
              document.querySelectorAll('.t-popup__overlay').forEach(o => o.style.display='none');
            }
            """
        )

        # Прогружаем ленивые картинки
        for _ in range(6):
            await page.mouse.wheel(0, 2500)
            await page.wait_for_timeout(500)

        items = await page.evaluate(
            """
            () => {
              const text = (el) => (el?.textContent || '').trim();
              const toInt = (s) => {
                const digits = (s || '').replace(/[^0-9]/g, '');
                if (!digits) return null;
                const n = parseInt(digits, 10);
                return Number.isFinite(n) ? n : null;
              };
              const pickImg = (img) => img?.getAttribute('data-original') || img?.getAttribute('src') || null;

              const products = Array.from(document.querySelectorAll('.js-product'));
              const out = [];

              for (const el of products) {
                const id = el.dataset.productLid || null;
                const title = text(el.querySelector('.js-product-name')) || null;
                const sku = text(el.querySelector('.js-product-sku')) || null;
                const badge = text(el.querySelector('.t754__mark')) || null;

                const priceCurrent = toInt(text(el.querySelector('.js-product-price')));
                const priceOld = toInt(text(el.querySelector('.t754__price_old .t754__price-value')));

                const frontImgEl =
                  el.querySelector('img.js-product-img') ||
                  el.querySelector('img[imgfield*="li_gallery"][data-original]') ||
                  el.querySelector('img[data-original]') ||
                  el.querySelector('img');

                const backImgEl =
                  el.querySelector('img.t754__img_second') ||
                  (() => {
                    const imgs = Array.from(el.querySelectorAll('img[data-original], img[src]'));
                    return imgs.length > 1 ? imgs[1] : null;
                  })();

                const front = pickImg(frontImgEl);
                const back = pickImg(backImgEl);

                const t = (title || '').toLowerCase();
                const s = (sku || '').toLowerCase();
                let category = 'tshirt';
                if (s === 'gift' || t.includes('сертификат')) category = 'certificate';
                if (t.includes('hoodie') || t.includes('zip-hoodie') || t.includes('zip hoodie')) category = 'hoodie';
                else if (t.includes('shorts')) category = 'shorts';
                else if (t.includes('long sleeve') || t.includes('longsleeve')) category = 'longsleeve';

                out.push({
                  id,
                  title,
                  sku,
                  badge,
                  category,
                  price_current: priceCurrent,
                  price_old: priceOld,
                  images: { front, back: back && back !== front ? back : null },
                });
              }

              // дедуп по id
              const seen = new Set();
              return out.filter(p => {
                if (!p.id) return false;
                if (seen.has(p.id)) return false;
                seen.add(p.id);
                return true;
              });
            }
            """
        )

        await browser.close()
        return items


async def main() -> None:
    items = await scrape_catalog()
    out_path = Path("catalog.json")
    out_path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ Saved {len(items)} products to {out_path.resolve()}")


if __name__ == "__main__":
    asyncio.run(main())


