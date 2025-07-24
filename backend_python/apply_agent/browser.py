from playwright.async_api import async_playwright

PROFILE_PATH = r"C:\Users\srini\AppData\Local\Google\Chrome\User Data\Default"  # <--- change this!
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"  # your real Chrome.exe


async def main():
    with open("jobs_urls_jds.json", "r", encoding="utf-8") as f:
        jobs = json.load(f)
class BrowserManager:
    def __init__(self, headless=False):
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None

    async def setup(self):
        self.playwright = await async_playwright().start()
        # Use persistent context so all cookies and storage are from your real profile!
        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=PROFILE_PATH,
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled"
            ],
            executable_path=CHROME_PATH
        )

    async def new_page(self):
        return await self.context.new_page()

    async def cleanup(self):
        if self.context:
            await self.context.close()
        if self.playwright:
            await self.playwright.stop()