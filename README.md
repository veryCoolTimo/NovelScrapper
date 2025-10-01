# Novel Scraper

Download novel chapters from ranobelib.me and save as .txt files.

## Installation

```bash
pip install -r requirements.txt
playwright install chromium
```

## Usage

```bash
# Download all chapters
python main.py --url "https://ranobelib.me/ru/195738--myst-might-mayhem/read/v01/c01"

# Download chapters 1-20
python main.py --url "..." --start 1 --end 20

# With proxy
python main.py --url "..." --proxy "http://user:pass@host:port"
```

## Options

- `--url` - URL of first chapter (required)
- `--start` - Starting chapter number (default: 1)
- `--end` - Ending chapter number (default: until failure)
- `--output` - Output directory (default: ./output)
- `--proxy` - Proxy server URL
- `--no-merge` - Don't merge chapters into single file
- `--headful` - Show browser window
- `--delay` - Delay between chapters in seconds (default: 2.0)

## Output

Chapters are saved to:
- Individual chapters: `output/{novel-name}/chapters/chapter_001.txt`
- Merged file: `output/{novel-name}/full.txt`
