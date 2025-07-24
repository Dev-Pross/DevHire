import asyncio
import json
from loguru import logger

from browser import BrowserManager
from navigator import Navigator
from applier import Applier

async def main():
    with open("jobs_urls_jds.json", "r", encoding="utf-8") as f:
        jobs = json.load(f)

    browser_mgr = BrowserManager(headless=False)
    await browser_mgr.setup()
    page = await browser_mgr.new_page()

    navigator = Navigator(browser_mgr)
    applier = Applier(navigator)

    for job_url in jobs:
        logger.info(f"Processing job: {job_url}")
        ok = await navigator.goto_job(page, job_url)
        if not ok:
            logger.error("Navigation failed/skipping job.")
            continue
        if not await applier.is_application_open(page):
            logger.warning("Skipping closed job.")
            continue
        ok = await applier.easy_apply(page)
        if not ok:
            logger.error("Couldn't find Easy Apply button or modal didn't load, skipping.")
            continue
        await asyncio.sleep(2)
        await applier.fill_and_submit(page)
        logger.info("Job apply process complete. Waiting before next...")
        await asyncio.sleep(8)

    await browser_mgr.cleanup()

if __name__ == "__main__":
    asyncio.run(main())