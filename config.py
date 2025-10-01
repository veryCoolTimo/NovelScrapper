"""Configuration settings for the novel scraper."""

# Scraper settings
HEADLESS_MODE = True
PAGE_LOAD_TIMEOUT = 30000  # milliseconds
DELAY_BETWEEN_CHAPTERS = 2.0  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 5.0  # seconds

# Proxy settings (optional)
PROXY_ENABLED = False
PROXY_SERVER = None  # "http://user:pass@host:port"

# Output settings
OUTPUT_DIR = "./output"
CHAPTERS_SUBDIR = "chapters"
FINAL_FILENAME = "full.txt"

# Browser settings
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
VIEWPORT = {"width": 1920, "height": 1080}

# CSS Selectors (will be refined after testing)
SELECTORS = {
    "chapter_content": [
        ".reader-container .text",
        ".chapter-content",
        "article .content",
        ".reader__container",
        "div[class*='reader'] p",
    ],
    "chapter_title": [
        ".reader-header h1",
        ".chapter-title",
        "h1.title",
    ],
    "next_chapter": [
        "a.next-chapter",
        "a[rel='next']",
        ".reader-navigation .next",
    ]
}
