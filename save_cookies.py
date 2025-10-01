#!/usr/bin/env python3
"""Helper script to save cookies from browser session."""

import asyncio
import json
from playwright.async_api import async_playwright

async def save_cookies():
    """Open browser, wait for manual login, save cookies."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080}
        )
        page = await context.new_page()

        print("=" * 80)
        print("Browser opened. You have 120 seconds to:")
        print("1. Login to ranobelib.me")
        print("2. Navigate to any chapter page")
        print("3. Wait - cookies will be saved automatically")
        print("=" * 80)

        await page.goto("https://ranobelib.me")

        # Wait for user to login
        print("\nWaiting 120 seconds for login...")
        for i in range(12):
            await asyncio.sleep(10)
            print(f"{(i+1)*10} seconds elapsed...")

        # Save cookies
        cookies = await context.cookies()
        with open("cookies.json", "w") as f:
            json.dump(cookies, f, indent=2)

        print(f"\n✓ Saved {len(cookies)} cookies to cookies.json")

        await browser.close()
        print("Browser closed.")

if __name__ == "__main__":
    asyncio.run(save_cookies())
