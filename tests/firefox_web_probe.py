import asyncio

from playwright.async_api import async_playwright


async def main():
    url = "https://calc-unblocked.preview.emergentagent.com/web"
    async with async_playwright() as p:
        try:
            browser = await p.firefox.launch(headless=True)
        except Exception as exc:
            print(f"FIREFOX_UNAVAILABLE: {exc}")
            return 2

        page = await browser.new_page(viewport={"width": 1024, "height": 768})
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_selector('[data-testid="browser-page"]', timeout=15000)
            await page.click('[data-testid="browser-shortcut-youtube"]', force=True)
            await page.wait_for_timeout(8000)
            status = await page.locator('[data-testid="proxy-status"]').inner_text()
            address = await page.locator('[data-testid="browser-address"]').input_value()
            print(f"FIREFOX_STATUS: {status}")
            print(f"FIREFOX_ADDRESS: {address}")
            await browser.close()
            return 0
        except Exception as exc:
            print(f"FIREFOX_TEST_ERROR: {exc}")
            await browser.close()
            return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
