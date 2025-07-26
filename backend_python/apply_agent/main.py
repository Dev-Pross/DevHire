import json
import asyncio
from playwright.async_api import async_playwright
from config import LINKEDIN_ID, LINKEDIN_PASSWORD
from playwright_stealth.stealth import Stealth
from apply_agent.applier import EasyApplyAgent

LINKEDIN_FEED_URL = "https://www.linkedin.com/feed/"
LINKEDIN_LOGIN_URL = "https://www.linkedin.com/login"

async def login_if_required(page, username, password):
    await page.goto(LINKEDIN_FEED_URL, wait_until="networkidle")
    if page.url.startswith(LINKEDIN_LOGIN_URL) or await page.locator('input#username').count() > 0:
        print("Login required, performing login...")
        await page.fill('input#username', username)
        await page.fill('input#password', password)
        await page.click('button[type="submit"]')
        for _ in range(30):
            await asyncio.sleep(1)
            curr_url = page.url
            if "/feed" in curr_url:
                print("Logged in successfully!")
                return True
            if any(x in curr_url for x in ["/checkpoint", "/captcha", "/login"]):
                print(f"Encountered checkpoint at {curr_url}. Manual intervention probably needed.")
                return False
        print("Timeout waiting for feed after login.")
        return False
    else:
        print("Already logged in.")
        return True

async def main():
    with open("apply_agent/jobs_urls_jds.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    job_urls = list(data.keys())

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context()
    page = await context.new_page()

    stealth = Stealth()
    await stealth.apply_stealth_async(page)

    if not await login_if_required(page, LINKEDIN_ID, LINKEDIN_PASSWORD):
        print("Login failed, exiting.")
        await context.close()
        await browser.close()
        await playwright.stop()
        return

    easy_apply_agent = EasyApplyAgent(page)
    applications = 0

    for url in job_urls:
        print(f"Navigating to: {url}")
        await page.goto(url)
        await asyncio.sleep(2)  # let the page settle

        if await easy_apply_agent.find_and_click_easy_apply():
            success = await easy_apply_agent.fill_and_submit_modal()
            if success:
                applications += 1
                print(f"✅ Applied! Total applied: {applications}")
            else:
                print("❌ Could not complete application modal.")
        else:
            print("❌ Easy Apply button not found or modal failed to open.")

        await asyncio.sleep(3)  # delay between job applications

    print(f"Automation complete. Total applications submitted: {applications}")

    await context.close()
    await browser.close()
    await playwright.stop()

if __name__ == "__main__":
    asyncio.run(main())
