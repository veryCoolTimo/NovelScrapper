"""Manage downloading and organizing novel chapters."""

import os
import re
import asyncio
import logging
from pathlib import Path
from typing import List, Optional
from tqdm import tqdm

from src.scraper import NovelScraper
from src.chapter_parser import ChapterParser
import config

logger = logging.getLogger(__name__)


class NovelManager:
    """Manage the download of a complete novel."""

    def __init__(self, start_url: str, output_dir: str = config.OUTPUT_DIR, proxy: Optional[str] = None, cookies_file: Optional[str] = None):
        """Initialize the novel manager.

        Args:
            start_url: URL of the first chapter to download
            output_dir: Base output directory
            proxy: Optional proxy server URL
            cookies_file: Path to cookies JSON file
        """
        self.start_url = start_url
        self.proxy = proxy
        self.cookies_file = cookies_file
        self.output_dir = Path(output_dir)
        self.novel_name = self._extract_novel_name(start_url)
        self.novel_dir = self.output_dir / self.novel_name
        self.chapters_dir = self.novel_dir / config.CHAPTERS_SUBDIR

        # Create directories
        self.chapters_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Novel directory: {self.novel_dir}")

    def _extract_novel_name(self, url: str) -> str:
        """Extract novel name from URL.

        Args:
            url: Novel chapter URL

        Returns:
            Novel name for directory
        """
        # Extract from URL patterns:
        # ranobelib.me: /ru/book/195738--myst-might-mayhem/read/...
        # ranobe.org: /r/195738--myst-might-mayhem/v01/c01
        patterns = [
            r'/ru/book/\d+--([^/]+)',  # ranobelib.me
            r'/r/\d+--([^/]+)',         # ranobe.org
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return "unknown-novel"

    async def download_chapter(self, scraper: NovelScraper, url: str, chapter_num: int) -> bool:
        """Download a single chapter.

        Args:
            scraper: NovelScraper instance
            url: Chapter URL
            chapter_num: Chapter number for filename

        Returns:
            True if successful, False otherwise
        """
        try:
            # Navigate to chapter
            success = await scraper.navigate_to_chapter(url)
            if not success:
                logger.error(f"Failed to load chapter {chapter_num}")
                return False

            # Get HTML and parse
            html = await scraper.get_page_html()
            parser = ChapterParser(html, url)

            # Extract content
            text = parser.extract_chapter_text()
            if not text or len(text) < 100:
                logger.error(f"Chapter {chapter_num} has insufficient content ({len(text)} chars)")
                # Save screenshot for debugging
                await scraper.screenshot(str(self.novel_dir / f"error_chapter_{chapter_num}.png"))
                return False

            # Get metadata
            metadata = parser.get_metadata()
            title = metadata.get("title") or f"Chapter {chapter_num}"

            # Format chapter content
            chapter_content = self._format_chapter(title, text, chapter_num, url)

            # Save to file
            filename = f"chapter_{chapter_num:03d}.txt"
            filepath = self.chapters_dir / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(chapter_content)

            logger.info(f"Saved chapter {chapter_num}: {title} ({len(text)} chars)")
            return True

        except Exception as e:
            logger.error(f"Error downloading chapter {chapter_num}: {e}")
            return False

    def _format_chapter(self, title: str, text: str, chapter_num: int, url: str) -> str:
        """Format chapter content with header.

        Args:
            title: Chapter title
            text: Chapter text
            chapter_num: Chapter number
            url: Source URL

        Returns:
            Formatted chapter text
        """
        header = f"""{'=' * 80}
Chapter {chapter_num}: {title}
{'=' * 80}
Source: {url}

"""
        return header + text + "\n\n"

    async def download_chapters(self, start_chapter: int = 1, end_chapter: Optional[int] = None, max_chapters: int = 1000):
        """Download chapters sequentially.

        Args:
            start_chapter: Starting chapter number
            end_chapter: Ending chapter number (None = until failure)
            max_chapters: Maximum chapters to download
        """
        async with NovelScraper(proxy=self.proxy, cookies_file=self.cookies_file) as scraper:
            # Generate chapter URLs based on start URL pattern
            current_url = self.start_url

            # Parse URL to get base pattern
            # Examples:
            # ranobelib.me: /ru/book/195738--myst-might-mayhem/read/v01/c01
            # ranobe.org: https://ranobe.org/r/195738--myst-might-mayhem/v01/c01
            match = re.match(r'(.*)/v(\d+)/c(\d+)', current_url)
            if not match:
                logger.error("Could not parse URL pattern")
                return

            base_url = match.group(1)
            volume = int(match.group(2))

            chapter_num = start_chapter
            consecutive_failures = 0
            max_consecutive_failures = 3

            # Progress bar
            pbar = tqdm(total=end_chapter if end_chapter else max_chapters, initial=start_chapter - 1, desc="Downloading")

            while chapter_num <= max_chapters:
                if end_chapter and chapter_num > end_chapter:
                    break

                # Generate URL (preserve original format - v1 or v01)
                chapter_url = f"{base_url}/v{volume}/c{chapter_num}"

                # Download chapter
                success = await self.download_chapter(scraper, chapter_url, chapter_num)

                if success:
                    consecutive_failures = 0
                    pbar.update(1)

                    # Delay between chapters
                    await asyncio.sleep(config.DELAY_BETWEEN_CHAPTERS)

                else:
                    consecutive_failures += 1
                    logger.warning(f"Failed to download chapter {chapter_num} (failure {consecutive_failures}/{max_consecutive_failures})")

                    if consecutive_failures >= max_consecutive_failures:
                        logger.info(f"Stopping after {consecutive_failures} consecutive failures")
                        break

                chapter_num += 1

            pbar.close()
            logger.info(f"Downloaded {chapter_num - start_chapter - consecutive_failures} chapters")

    def merge_chapters(self) -> str:
        """Merge all downloaded chapters into a single file.

        Returns:
            Path to the merged file
        """
        output_file = self.novel_dir / config.FINAL_FILENAME

        # Get all chapter files sorted
        chapter_files = sorted(self.chapters_dir.glob("chapter_*.txt"))

        if not chapter_files:
            logger.error("No chapter files found to merge")
            return ""

        logger.info(f"Merging {len(chapter_files)} chapters...")

        with open(output_file, 'w', encoding='utf-8') as outfile:
            # Write header
            outfile.write(f"{'=' * 80}\n")
            outfile.write(f"{self.novel_name.replace('-', ' ').title()}\n")
            outfile.write(f"{'=' * 80}\n\n")

            # Merge chapters
            for chapter_file in tqdm(chapter_files, desc="Merging"):
                with open(chapter_file, 'r', encoding='utf-8') as infile:
                    content = infile.read()
                    outfile.write(content)
                    outfile.write("\n\n")

        logger.info(f"Merged novel saved to: {output_file}")
        return str(output_file)

    def get_chapter_count(self) -> int:
        """Get the number of downloaded chapters.

        Returns:
            Number of chapter files
        """
        return len(list(self.chapters_dir.glob("chapter_*.txt")))
