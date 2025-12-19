# Деплой на Vercel

## Шаги для деплоя:

### 1. Создай репозиторий на GitHub (если еще не создан)
- Перейди на https://github.com/new
- Название: `ballinmerch`
- Сделай репозиторий публичным или приватным (как нужно)
- НЕ добавляй README, .gitignore или лицензию (у нас уже есть)

### 2. Запушь код в репозиторий

Если SSH не работает, используй HTTPS:
```bash
git remote set-url origin https://github.com/Kreemchek/ballinmerch.git
git push -u origin main
```

Или если репозиторий еще не создан, создай его через GitHub веб-интерфейс, затем:
```bash
git push -u origin main
```

### 3. Деплой на Vercel

**Вариант 1: Через веб-интерфейс Vercel**
1. Зайди на https://vercel.com
2. Нажми "Add New Project"
3. Импортируй репозиторий `Kreemchek/ballinmerch`
4. Vercel автоматически определит настройки из `vercel.json`
5. Нажми "Deploy"

**Вариант 2: Через Vercel CLI**
```bash
npm i -g vercel
vercel login
cd /Users/zalogudachi/PycharmProjects/winwindeal
vercel
```

### 4. Настройки проекта на Vercel

После деплоя:
- **Framework Preset**: Other
- **Build Command**: (оставить пустым)
- **Output Directory**: (оставить пустым)
- **Install Command**: (оставить пустым)

Vercel автоматически будет обслуживать статические файлы.

### 5. Доменное имя

После деплоя Vercel даст тебе домен типа `ballinmerch.vercel.app`
Можешь добавить свой кастомный домен в настройках проекта.

## Структура проекта

- `index.html` - главная страница
- `styles.css` - стили
- `script.js` - JavaScript логика
- `catalog.json` - каталог товаров (81 товар)
- `images/` - все изображения товаров
- `vercel.json` - конфигурация для Vercel

## Обновление каталога

Если нужно обновить каталог товаров:
```bash
source venv/bin/activate
python3 scrape_catalog.py
git add catalog.json
git commit -m "Update catalog"
git push
```

Vercel автоматически пересоберет проект после push.

