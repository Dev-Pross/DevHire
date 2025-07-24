from loguru import logger
import asyncio

class Navigator:
    def __init__(self, browser_mgr):
        self.browser_mgr = browser_mgr

    async def goto_job(self, page, url):
        try:
            logger.info(f"Navigating to {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(3)
            cur_url = page.url
            if any(x in cur_url.lower() for x in ["login", "authwall", "uas/authenticate"]):
                logger.error(f"Redirected to login/auth wall: {cur_url}")
                return False
            logger.info("On job page!")
            return True
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            return False