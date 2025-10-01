# Технический План - NovelScraper для Ranobelib.me

## Анализ Требований

**Цель:** Создать скрапер для скачивания новелл с ranobelib.me в формат .txt

**Пример URL:** https://ranobelib.me/ru/195738--myst-might-mayhem/read/v01/c01

### Ключевые Особенности Сайта
1. **JavaScript-рендеринг** - контент загружается динамически
2. **Возможная геоблокировка** - может потребоваться прокси (проверить)
3. **Структура URL:** `/ru/{novel_id}--{novel-slug}/read/v{volume}/c{chapter}`

---

## Архитектура Решения

### Выбор Технологий

**Playwright (Python)** - рекомендуется
- ✅ Поддержка JavaScript-рендеринга
- ✅ Headless режим (быстрее, меньше ресурсов)
- ✅ Встроенная поддержка прокси
- ✅ Автоматические ожидания загрузки элементов
- ✅ Скриншоты для отладки

**Альтернатива:** Selenium (более медленный)

### Структура Проекта

```
NovelScraper/
├── docs/                      # Документация
│   └── technical-plan.md
├── src/
│   ├── scraper.py            # Основной скрапер
│   ├── chapter_parser.py     # Парсинг HTML глав
│   ├── novel_manager.py      # Управление скачиванием новеллы
│   └── utils.py              # Вспомогательные функции
├── output/                   # Скачанные новеллы
│   └── {novel_name}/
│       ├── chapters/         # Отдельные главы
│       └── full.txt          # Объединенный файл
├── config.py                 # Конфигурация (прокси, задержки)
├── requirements.txt
└── main.py                   # Точка входа
```

---

## Детальный План Реализации

### 1. Настройка Окружения

**Зависимости:**
```txt
playwright==1.40.0
beautifulsoup4==4.12.2
lxml==4.9.3
tqdm==4.66.1
```

**Установка:**
```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Модуль Scraper (`scraper.py`)

**Функционал:**
- Инициализация Playwright browser
- Поддержка прокси (опционально)
- Навигация по страницам с retry-логикой
- Обработка ошибок (timeout, 403, 502)

**Ключевые методы:**
```python
class NovelScraper:
    def __init__(self, proxy=None, headless=True)
    async def navigate_to_chapter(self, url)
    async def wait_for_content_load(self)
    async def get_page_html(self)
    async def close(self)
```

### 3. Модуль Chapter Parser (`chapter_parser.py`)

**Функционал:**
- Извлечение текста главы из HTML
- Определение CSS-селекторов для контента
- Очистка текста от рекламы/скриптов
- Извлечение метаданных (номер главы, название)

**Селекторы для исследования:**
- `.reader-container` (предполагаемый контейнер текста)
- `.chapter-content`
- `article`
- Нужно проверить реальную структуру через DevTools

**Ключевые методы:**
```python
class ChapterParser:
    def __init__(self, html)
    def extract_chapter_text(self) -> str
    def extract_chapter_title(self) -> str
    def extract_chapter_number(self) -> int
```

### 4. Модуль Novel Manager (`novel_manager.py`)

**Функционал:**
- Определение всех глав новеллы
- Генерация списка URL глав
- Скачивание глав с progress bar
- Сохранение в отдельные .txt файлы
- Объединение в один файл

**Алгоритм:**
1. Получить страницу тома (volume)
2. Парсинг списка глав
3. Итерация по главам с задержкой (rate limiting)
4. Сохранение каждой главы
5. Финальное объединение

**Ключевые методы:**
```python
class NovelManager:
    def __init__(self, novel_url, output_dir)
    async def get_chapter_list(self) -> List[str]
    async def download_chapter(self, chapter_url, chapter_num)
    async def download_all_chapters(self)
    def merge_chapters(self)
```

### 5. Конфигурация (`config.py`)

```python
# Настройки скрапера
HEADLESS_MODE = True
PAGE_LOAD_TIMEOUT = 30000  # ms
DELAY_BETWEEN_CHAPTERS = 2  # seconds

# Прокси (опционально)
PROXY_ENABLED = False
PROXY_SERVER = None  # "http://user:pass@host:port"

# Пути
OUTPUT_DIR = "./output"
```

### 6. Main Entry Point (`main.py`)

**CLI интерфейс:**
```python
import argparse

parser.add_argument('--url', required=True, help='Novel URL')
parser.add_argument('--proxy', help='Proxy server')
parser.add_argument('--output', default='./output')
parser.add_argument('--start-chapter', type=int, default=1)
parser.add_argument('--end-chapter', type=int, default=None)
```

---

## Алгоритм Работы

### Основной Flow

```
1. Пользователь предоставляет URL первой главы
   ↓
2. Scraper открывает страницу через Playwright
   ↓
3. Ожидание загрузки контента (wait for selector)
   ↓
4. Извлечение HTML
   ↓
5. Parser извлекает текст главы
   ↓
6. Сохранение в файл: output/{novel_name}/chapters/chapter_001.txt
   ↓
7. Переход к следующей главе (кнопка "Next" или генерация URL)
   ↓
8. Повтор шагов 2-7 для всех глав
   ↓
9. Объединение всех глав в full.txt
```

### Определение Следующей Главы

**Стратегия 1:** Поиск кнопки "Следующая глава"
```python
next_button = page.locator('a.next-chapter')  # Селектор нужно уточнить
```

**Стратегия 2:** Генерация URL по паттерну
```python
# /ru/195738--myst-might-mayhem/read/v01/c01
# /ru/195738--myst-might-mayhem/read/v01/c02
chapter_num += 1
next_url = f"{base_url}/v{volume:02d}/c{chapter_num:02d}"
```

**Стратегия 3:** Парсинг списка глав из оглавления
```python
# Получить страницу новеллы
# Найти все ссылки на главы
chapters = page.locator('.chapter-list a').all()
```

---

## Обработка Проблем

### 1. Геоблокировка / Cloudflare

**Симптомы:**
- 403 Forbidden
- Cloudflare challenge page

**Решения:**
- Использовать прокси (DataImpulse: $5 за 2.5GB)
- Добавить реалистичные headers
- Использовать stealth плагин для Playwright

```python
from playwright.async_api import async_playwright

async with async_playwright() as p:
    browser = await p.chromium.launch(
        proxy={"server": PROXY_SERVER} if PROXY_ENABLED else None
    )
    context = await browser.new_context(
        user_agent='Mozilla/5.0 ...',
        viewport={'width': 1920, 'height': 1080}
    )
```

### 2. Rate Limiting

**Защита:**
- Задержка между запросами (2-5 секунд)
- Exponential backoff при ошибках
- Respect robots.txt (если есть)

```python
import asyncio
import random

await asyncio.sleep(random.uniform(2.0, 4.0))
```

### 3. Изменение Структуры HTML

**Защита:**
- Множественные селекторы (fallback)
- Логирование структуры при ошибках
- Сохранение скриншотов при сбоях

```python
selectors = [
    '.reader-container .text',
    '.chapter-content',
    'article .content',
    'div[class*="reader"] p'
]

for selector in selectors:
    content = page.locator(selector)
    if await content.count() > 0:
        return await content.text_content()
```

---

## План Тестирования

### Этап 1: Proof of Concept
- [x] Проверка доступности сайта
- [ ] Открытие одной главы через Playwright
- [ ] Определение правильного селектора для текста
- [ ] Извлечение текста одной главы
- [ ] Сохранение в .txt

### Этап 2: Базовый Функционал
- [ ] Скачивание 5 глав
- [ ] Определение навигации между главами
- [ ] Автоматическое объединение глав
- [ ] Progress bar

### Этап 3: Надежность
- [ ] Обработка ошибок (timeout, 404)
- [ ] Retry-логика
- [ ] Возобновление при прерывании
- [ ] Логирование

### Этап 4: Оптимизация
- [ ] Тестирование прокси (если нужен)
- [ ] Настройка задержек
- [ ] Параллельное скачивание (опционально, рискованно)

---

## Вопросы для Уточнения

1. **Прокси:** Нужно ли использовать прокси? Проверить доступность с текущего IP
2. **HTML структура:** Нужен полный HTML страницы с текстом главы для определения селекторов
3. **Объем:** Сколько глав в типичной новелле? (для оценки времени)
4. **Формат вывода:** Только .txt или также EPUB?
5. **Метаданные:** Включать ли название главы, номер, разделители?

---

## Следующие Шаги

1. **Получить реальный HTML страницы с текстом главы**
   - Открыть https://ranobelib.me/ru/195738--myst-might-mayhem/read/v01/c01 в браузере
   - F12 → Elements → Скопировать outerHTML элемента с текстом

2. **Определить CSS-селекторы**
   - Контейнер с текстом главы
   - Кнопка "Следующая глава"
   - Список всех глав (если есть)

3. **Создать PoC скрипт**
   - Одна глава → .txt файл

4. **Расширить до полного скрапера**

---

## Оценка Времени

- Настройка окружения: **30 мин**
- Определение селекторов: **1 час**
- Базовый скрапер (1 глава): **2 часа**
- Полный функционал (все главы + merge): **3 часа**
- Обработка ошибок + тестирование: **2 часа**

**Итого:** ~8 часов для полнофункционального скрапера

---

## Пример Использования

```bash
# Скачать всю новеллу
python main.py --url "https://ranobelib.me/ru/195738--myst-might-mayhem/read/v01/c01"

# С прокси
python main.py --url "..." --proxy "http://user:pass@proxy:port"

# Диапазон глав
python main.py --url "..." --start-chapter 10 --end-chapter 50
```

---

## Статус Реализации

### ✅ Завершено

1. **Базовая Структура Проекта**
   - Создана структура директорий (src/, output/, docs/)
   - Настроен .gitignore
   - Создан README.md с инструкциями

2. **Основные Модули**
   - `config.py` - конфигурация с настройками
   - `src/scraper.py` - браузер автоматизация через Playwright
   - `src/chapter_parser.py` - парсинг HTML глав
   - `src/novel_manager.py` - управление скачиванием
   - `main.py` - CLI интерфейс

3. **Функционал**
   - Асинхронная загрузка через Playwright
   - Множественные CSS селекторы (fallback)
   - Retry логика при ошибках
   - Progress bar (tqdm)
   - Автоматическое объединение глав
   - Логирование в файл и консоль
   - Поддержка прокси

---

## TODO: Что Нужно Доделать

### Критичные Задачи

1. **Установка Зависимостей**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   playwright install chromium
   ```

2. **Тестирование и Отладка Селекторов**
   - Запустить на одной главе
   - Определить правильные CSS селекторы для ranobelib.me
   - Обновить `config.SELECTORS` если нужно
   - Протестировать извлечение текста

3. **Проверка Доступности**
   - Проверить, нужен ли прокси для доступа
   - Если да - подключить DataImpulse ($5)

### Оптимизация (Опционально)

4. **Улучшение Парсера**
   - Точная настройка селекторов после тестов
   - Улучшение очистки текста от рекламы
   - Определение кнопки "Next Chapter"

5. **Дополнительные Функции**
   - Сохранение метаданных (автор, описание)
   - EPUB формат вывода
   - Resume функция (продолжить с главы X)
   - Параллельное скачивание (осторожно!)

6. **Улучшение Навигации**
   - Автоопределение всех глав из оглавления
   - Поддержка нескольких томов

7. **Обработка Ошибок**
   - Cloudflare bypass (если нужен)
   - Captcha обработка
   - Более интеллектуальные retry стратегии

### Как Тестировать

```bash
# После установки зависимостей
python main.py --url "https://ranobelib.me/ru/195738--myst-might-mayhem/read/v01/c01" --start 1 --end 3 --headful
```

Это скачает 3 главы с видимым браузером для отладки.

---

**Дата создания:** 2025-10-01
**Последнее обновление:** 2025-10-01
**Статус:** Базовая реализация завершена, требуется тестирование
