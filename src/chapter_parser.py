"""Parse chapter content from HTML."""

import re
import logging
from typing import Optional, Dict
from bs4 import BeautifulSoup

import config

logger = logging.getLogger(__name__)


class ChapterParser:
    """Extract chapter information from HTML."""

    def __init__(self, html: str, url: str = ""):
        """Initialize the parser.

        Args:
            html: HTML content of the chapter page
            url: URL of the chapter (for reference)
        """
        self.html = html
        self.url = url
        self.soup = BeautifulSoup(html, 'lxml')

    def extract_chapter_text(self) -> str:
        """Extract the main chapter text content.

        Returns:
            Chapter text as string
        """
        # Try different selectors
        for selector in config.SELECTORS["chapter_content"]:
            try:
                # Convert CSS selector to BeautifulSoup selector
                if selector.startswith("."):
                    # Class selector
                    class_name = selector[1:].replace(".", " ")
                    elements = self.soup.find_all(class_=class_name)
                elif selector.startswith("article"):
                    elements = self.soup.find_all("article")
                else:
                    # Try general selection
                    elements = self.soup.select(selector)

                if elements:
                    # Get text from all matching elements
                    text_parts = []
                    for elem in elements:
                        # Get all paragraphs or text content
                        paragraphs = elem.find_all(['p', 'div'])
                        if paragraphs:
                            for p in paragraphs:
                                text = p.get_text(strip=True)
                                if text and len(text) > 20:  # Filter out short/empty elements
                                    text_parts.append(text)
                        else:
                            text = elem.get_text(strip=True)
                            if text and len(text) > 20:
                                text_parts.append(text)

                    if text_parts:
                        result = "\n\n".join(text_parts)
                        logger.info(f"Extracted {len(result)} characters using selector: {selector}")
                        return result

            except Exception as e:
                logger.debug(f"Error with selector {selector}: {e}")
                continue

        # Fallback: try to find the largest text block
        logger.warning("No selector worked, trying fallback method...")
        return self._extract_largest_text_block()

    def _extract_largest_text_block(self) -> str:
        """Fallback method to extract the largest text block.

        Returns:
            Largest text block found
        """
        # Find all divs and articles
        candidates = self.soup.find_all(['div', 'article', 'section'])

        largest_text = ""
        for elem in candidates:
            text = elem.get_text(separator="\n\n", strip=True)
            if len(text) > len(largest_text):
                largest_text = text

        if largest_text:
            logger.info(f"Extracted {len(largest_text)} characters using fallback")
            return largest_text

        logger.error("Could not extract chapter text!")
        return ""

    def extract_chapter_title(self) -> Optional[str]:
        """Extract the chapter title.

        Returns:
            Chapter title or None
        """
        for selector in config.SELECTORS["chapter_title"]:
            try:
                if selector.startswith("."):
                    class_name = selector[1:]
                    elem = self.soup.find(class_=class_name)
                elif selector.startswith("h1"):
                    elem = self.soup.find("h1")
                else:
                    elem = self.soup.select_one(selector)

                if elem:
                    title = elem.get_text(strip=True)
                    logger.debug(f"Found title: {title}")
                    return title

            except Exception as e:
                logger.debug(f"Error extracting title with {selector}: {e}")
                continue

        return None

    def extract_chapter_number(self) -> Optional[int]:
        """Try to extract chapter number from URL or title.

        Returns:
            Chapter number or None
        """
        # Try to extract from URL first
        # Example: /read/v01/c01 -> chapter 1
        match = re.search(r'/c(\d+)', self.url)
        if match:
            return int(match.group(1))

        # Try to extract from title
        title = self.extract_chapter_title()
        if title:
            match = re.search(r'(?:chapter|глава|ch\.?)\s*(\d+)', title, re.IGNORECASE)
            if match:
                return int(match.group(1))

        return None

    def extract_volume_number(self) -> Optional[int]:
        """Try to extract volume number from URL.

        Returns:
            Volume number or None
        """
        # Example: /read/v01/c01 -> volume 1
        match = re.search(r'/v(\d+)', self.url)
        if match:
            return int(match.group(1))
        return None

    def get_metadata(self) -> Dict[str, any]:
        """Extract all metadata from the chapter.

        Returns:
            Dictionary with chapter metadata
        """
        return {
            "title": self.extract_chapter_title(),
            "chapter": self.extract_chapter_number(),
            "volume": self.extract_volume_number(),
            "url": self.url,
        }
