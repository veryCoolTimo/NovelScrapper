#!/usr/bin/env python3
"""Main entry point for the novel scraper."""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from src.novel_manager import NovelManager
import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('scraper.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Download novel chapters from ranobe sites',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download all chapters starting from chapter 1
  python main.py --url "https://ranobelib.me/ru/book/195738--myst-might-mayhem/read/v01/c01"

  # Download chapters 1-20
  python main.py --url "..." --start 1 --end 20

  # Download with proxy
  python main.py --url "..." --proxy "http://user:pass@host:port"

  # Download without merging
  python main.py --url "..." --no-merge
        """
    )

    parser.add_argument(
        '--url',
        required=True,
        help='URL of the first chapter to download'
    )

    parser.add_argument(
        '--start',
        type=int,
        default=1,
        help='Starting chapter number (default: 1)'
    )

    parser.add_argument(
        '--end',
        type=int,
        default=None,
        help='Ending chapter number (default: download until failure)'
    )

    parser.add_argument(
        '--max',
        type=int,
        default=1000,
        help='Maximum chapters to download (default: 1000)'
    )

    parser.add_argument(
        '--output',
        default=config.OUTPUT_DIR,
        help=f'Output directory (default: {config.OUTPUT_DIR})'
    )

    parser.add_argument(
        '--proxy',
        help='Proxy server (format: http://user:pass@host:port)'
    )

    parser.add_argument(
        '--no-merge',
        action='store_true',
        help='Do not merge chapters into a single file'
    )

    parser.add_argument(
        '--headful',
        action='store_true',
        help='Run browser in headful mode (show browser window)'
    )

    parser.add_argument(
        '--delay',
        type=float,
        default=config.DELAY_BETWEEN_CHAPTERS,
        help=f'Delay between chapters in seconds (default: {config.DELAY_BETWEEN_CHAPTERS})'
    )

    return parser.parse_args()


async def main():
    """Main async function."""
    args = parse_args()

    # Update config with args
    if args.headful:
        config.HEADLESS_MODE = False
    config.DELAY_BETWEEN_CHAPTERS = args.delay

    logger.info("=" * 80)
    logger.info("Novel Scraper Starting")
    logger.info("=" * 80)
    logger.info(f"URL: {args.url}")
    logger.info(f"Start chapter: {args.start}")
    logger.info(f"End chapter: {args.end if args.end else 'Until failure'}")
    logger.info(f"Output: {args.output}")
    logger.info(f"Proxy: {args.proxy if args.proxy else 'None'}")
    logger.info("=" * 80)

    try:
        # Initialize manager
        manager = NovelManager(
            start_url=args.url,
            output_dir=args.output,
            proxy=args.proxy
        )

        # Download chapters
        logger.info("Starting download...")
        await manager.download_chapters(
            start_chapter=args.start,
            end_chapter=args.end,
            max_chapters=args.max
        )

        # Merge chapters
        if not args.no_merge:
            logger.info("Merging chapters...")
            output_file = manager.merge_chapters()
            if output_file:
                logger.info(f"✓ Novel saved to: {output_file}")
        else:
            logger.info("Skipping merge (--no-merge specified)")

        # Summary
        chapter_count = manager.get_chapter_count()
        logger.info("=" * 80)
        logger.info(f"✓ Download complete!")
        logger.info(f"  Chapters downloaded: {chapter_count}")
        logger.info(f"  Output directory: {manager.novel_dir}")
        logger.info("=" * 80)

    except KeyboardInterrupt:
        logger.info("\n\nDownload interrupted by user")
        logger.info("You can resume by adjusting --start parameter")
        sys.exit(1)

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
