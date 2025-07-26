from playwright.async_api import async_playwright
from playwright_stealth.stealth import Stealth

class BrowserManager:
    def __init__(self):
        self.browser = None
        self.context = None

    async def setup(self):
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=False)
        self.context = await self.browser.new_context(
            viewport={'width': 1280, 'height': 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        )
        return self.context

    async def new_page(self):
        page = await self.context.new_page()
        # Apply stealth
        stealth = Stealth()
        await stealth.apply_stealth_async(page)
        return page

    async def close(self):
        await self.context.close()
        await self.browser.close()
