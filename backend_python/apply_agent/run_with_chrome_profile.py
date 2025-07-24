import asyncio
from playwright.async_api import async_playwright

PROFILE_PATH = r"C:\Users\srini\AppData\Local\Google\Chrome\User Data\Profile 5"  # <-- use your copied folder

async def main():
    async with async_playwright() as p:
        # This launches Chromium with your full user profile
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_PATH,
            headless=False,  # Must be False to mimic real use
            args=[
                "--disable-blink-features=AutomationControlled",  # extra stealth
            ]
        )
        page = await browser.new_page()
        await page.goto("https://www.linkedin.com/")
        print("If you're logged in, you should see your LinkedIn feed/profile!")
        # Interact, or let your script do the rest (apply, etc)
        await page.wait_for_timeout(20000)  # 20 seconds to observe
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())