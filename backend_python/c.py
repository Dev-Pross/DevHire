from pathlib import Path
import logging
import time
import json
import random
import asyncio

import requests
from playwright.async_api import async_playwright

# ─────────────────────────────  LOGGING  ──────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ────────────────────────  STORAGE INJECTOR ──────────────────────────
def load_storage(storage_path):
    """Load storage JSON as dict, returns {} if missing or error."""
    try:
        with open(storage_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"⚠️ Could not load storage file {storage_path}: {e}")
        return {}

async def inject_storage(page, local_data, session_data):
    """Inject localStorage and sessionStorage into the page using add_init_script."""
    if local_data:
        local_js = ";".join([
            f"localStorage.setItem({json.dumps(str(k))}, {json.dumps(str(v))});"
            for k, v in local_data.items()
        ])
        await page.add_init_script(local_js)
        logger.info(f"🪣 Injected {len(local_data)} localStorage items")

    if session_data:
        session_js = ";".join([
            f"sessionStorage.setItem({json.dumps(str(k))}, {json.dumps(str(v))});"
            for k, v in session_data.items()
        ])
        await page.add_init_script(session_js)
        logger.info(f"🪣 Injected {len(session_data)} sessionStorage items")

# ────────────────────────  COOKIE MANAGER  ───────────────────────────
class CookieManager:
    def __init__(self, cookies_dir: str = "data_dump"):
        self.cookies_dir = Path(cookies_dir)
        self.linkedin_cookies: dict[str, str] = {}

        self.essential_cookies = [
            "li_at", "JSESSIONID", "bcookie", "bscookie", "lang", "lidc",
            "UserMatchHistory", "li_a", "li_mc",
        ]

    def load_all_linkedin_cookies(self) -> bool:
        try:
            combined = self.cookies_dir / "cookies.json"
            if combined.exists():
                self.linkedin_cookies = json.loads(combined.read_text(encoding="utf-8"))
                logger.info(
                    "✅ Loaded %s LinkedIn cookies from JSON: %s",
                    len(self.linkedin_cookies), list(self.linkedin_cookies.keys()),
                )
                return True

            loaded = {}
            for name in self.essential_cookies:
                f = self.cookies_dir / f"{name}.txt"
                if f.exists():
                    val = f.read_text(encoding="utf-8").strip()
                    if val:
                        loaded[name] = val
            if loaded:
                self.linkedin_cookies = loaded
                logger.info(
                    "✅ Loaded %s LinkedIn cookies from individual files",
                    len(loaded),
                )
                return True

            logger.error("❌ No LinkedIn cookies found")
            return False
        except Exception as exc:
            logger.error("❌ Cookie load error: %s", exc)
            return False

    def get_cookie(self, name: str = "li_at") -> str | None:
        if not self.linkedin_cookies:
            self.load_all_linkedin_cookies()
        val = self.linkedin_cookies.get(name)
        if val:
            logger.info("✅ %s cookie retrieved", name)
        return val

    def get_all_cookies(self) -> dict[str, str]:
        if not self.linkedin_cookies:
            self.load_all_linkedin_cookies()
        return self.linkedin_cookies.copy()

    def has_essential_cookies(self) -> bool:
        if not self.linkedin_cookies:
            self.load_all_linkedin_cookies()
        missing = [c for c in ["li_at"] if c not in self.linkedin_cookies]
        if missing:
            logger.error("❌ Missing essential cookies: %s", missing)
            return False
        return True

# ────────────────────────  BROWSER MANAGER  ──────────────────────────
class BrowserManager:
    def __init__(self, headless: bool = False, max_concurrent_pages: int = 3):
        self.headless = headless
        self.max_concurrent_pages = max_concurrent_pages

        self.playwright = None
        self.browser = None
        self.context = None

        self.cookie_manager = CookieManager()
        self.linkedin_cookies: dict[str, str] = {}
        self.active_pages = []

    def load_all_linkedin_cookies(self) -> bool:
        try:
            cookies_file = Path("data_dump/cookies.json")
            if cookies_file.exists():
                self.linkedin_cookies = json.loads(cookies_file.read_text())
                return True

            all_cookies = self.cookie_manager.get_all_cookies()
            if all_cookies:
                self.linkedin_cookies = all_cookies
                return True

            return False
        except Exception as exc:
            logger.error("❌ Error loading cookies: %s", exc)
            return False

    async def setup(self) -> bool:
        try:
            if not self.load_all_linkedin_cookies():
                logger.error("❌ No LinkedIn cookies available")
                return False

            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--no-first-run",
                    "--disable-default-apps",
                    "--disable-features=VizDisplayCompositor",
                    "--disable-web-security",
                    "--disable-background-timer-throttling",
                    "--disable-backgrounding-occluded-windows",
                    "--disable-renderer-backgrounding"
                ],
            )

            self.context = await self.browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1366, "height": 768},
                locale="en-US",
                timezone_id="America/New_York",
                permissions=["geolocation"],
                ignore_https_errors=False,
                java_script_enabled=True,
            )

            # Inject fingerprinting and anti-bot properties (add more as needed)
            await self.context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
                Object.defineProperty(navigator, 'platform', { get: () => 'Win32' });
                Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
                Object.defineProperty(window, 'devicePixelRatio', { get: () => 1 });
                Object.defineProperty(navigator, 'vendor', { get: () => 'Google Inc.' });
                Object.defineProperty(navigator, 'oscpu', { get: () => 'Windows NT 10.0; Win64; x64' });
                window.screen = Object.assign(window.screen, { width: 1366, height: 768 });
                // Add more spoofing if needed
                """)
            await self._handle_heartbeat_requests_on_context(self.context)

            cookies_to_add = [
                {
                    "name": k,
                    "value": v,
                    "domain": ".linkedin.com",
                    "path": "/",
                    "httpOnly": k in ("li_at", "JSESSIONID"),
                    "secure": True,
                    "sameSite": "Lax" if k not in ("li_at", "JSESSIONID") else "None",
                }
                for k, v in self.linkedin_cookies.items()
            ]
            await self.context.add_cookies(cookies_to_add)

            await self._setup_realistic_headers(self.context)

            logger.info("🔐 %s LinkedIn cookies injected", len(cookies_to_add))
            cookie_names = [cookie["name"] for cookie in cookies_to_add]
            logger.info("📋 Injected cookies: %s", cookie_names)

            return True
        except Exception as exc:
            logger.error("❌ Browser setup failed: %s", exc)
            return False

    async def _handle_heartbeat_requests_on_context(self, context):
        async def route_handler(route):
            url = route.request.url
            if "realtimeFrontendClientConnectivityTracking" in url:
                hdrs = dict(route.request.headers)
                hdrs.update({
                    "x-li-page-instance": "urn:li:page:d_flagship3_job_details",
                    "x-restli-protocol-version": "2.0.0",
                    "x-li-lang": "en_US",
                    "sec-fetch-mode": "cors",
                    "sec-fetch-site": "same-origin",
                })
                await route.continue_(headers=hdrs)
            else:
                await route.continue_()
        await context.route("**/*", route_handler)

    async def _setup_realistic_headers(self, context):
        await context.set_extra_http_headers({
            "sec-ch-ua": '"Chromium";v="120", "Google Chrome";v="120", "Not A Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "x-requested-with": "XMLHttpRequest",
            "x-li-lang": "en_US",
            "x-li-track": '{"clientVersion":"1.2.3","osName":"Windows","osVersion":"10"}',
        })

    async def create_page(self):
        if not self.context or len(self.active_pages) >= self.max_concurrent_pages:
            return None
        page = await self.context.new_page()
        self.active_pages.append(page)
        logger.info("📄 Page created (Active: %s)", len(self.active_pages))
        return page

    async def close_page(self, page):
        try:
            if page in self.active_pages:
                self.active_pages.remove(page)
            await page.close()
        except Exception as exc:
            logger.error("❌ Page close error: %s", exc)

    async def cleanup(self):
        for p in self.active_pages[:]:
            await self.close_page(p)
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

# ──────────────────────────  PAGE NAVIGATOR  ──────────────────────────
class PageNavigator:
    def __init__(self, browser_manager: BrowserManager):
        self.browser_manager = browser_manager

    async def navigate_to_job(self, page, job_url: str) -> bool:
        try:
            logger.info("🔄 Navigating directly to job URL...")
            await page.wait_for_timeout(random.randint(2000, 5000))
            await page.goto(job_url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(5000)
            current_url = page.url
            logger.info(f"📍 Current URL: {current_url}")
            if any(blocked in current_url.lower() for blocked in ["login", "authwall", "uas/authenticate"]):
                logger.error(f"❌ redirected to login: {current_url}")
                return False
            logger.info("✅ Successfully navigated to job page")
            return True
        except Exception as exc:
            logger.error("❌ navigation error: %s", exc)
            return False

# ──────────────  APPLY BUTTON FINDER WITH MODAL WAIT & FALLBACK  ──────────────
class ApplyButtonFinder:
    def __init__(self, page_navigator: PageNavigator):
        self.page_navigator = page_navigator

    async def find_and_click_apply_button(self, page):
        logger.info("🔍 Enhanced Easy Apply button search...")
        try:
            logger.info("📊 Looking for ALL buttons containing 'Apply'...")
            all_apply_buttons = await page.locator('button:has-text("Apply")').all()
            logger.info(f"Found {len(all_apply_buttons)} buttons with 'Apply' text")
            for i, button in enumerate(all_apply_buttons):
                try:
                    text = await button.text_content() or ""
                    class_attr = await button.get_attribute('class') or ""
                    is_visible = await button.is_visible()
                    is_enabled = await button.is_enabled()
                    logger.info(f"  Button {i+1}: '{text.strip()}' | Visible: {is_visible} | Enabled: {is_enabled}")
                    logger.info(f"    Classes: {class_attr}")
                    if "Easy Apply" in text and is_visible and is_enabled:
                        logger.info(f"🎯 Attempting to click button {i+1}...")
                        await button.scroll_into_view_if_needed()
                        await page.wait_for_timeout(1000)
                        await button.click()
                        logger.info("✅ Clicked Easy Apply button, waiting for modal...")
                        # Wait for modal/dialog after click
                        try:
                            await page.wait_for_selector('.jobs-easy-apply-modal', timeout=10000)
                            logger.info("✅ Easy Apply modal appeared!")
                            return True
                        except Exception as e:
                            logger.error(f"❌ Modal did not appear: {e}")
                            # Fallback: Try JS click
                            try:
                                await page.evaluate('(el) => el.click()', button)
                                await page.wait_for_selector('.jobs-easy-apply-modal', timeout=5000)
                                logger.info("✅ Modal appeared after JS click!")
                                return True
                            except Exception as e:
                                logger.error(f"❌ Still no modal: {e}")
                                return False
                except Exception as e:
                    logger.error(f"Error examining button {i+1}: {e}")
                    continue
            logger.error("❌ All approaches failed to find/click Easy Apply button")
            return False
        except Exception as exc:
            logger.error(f"❌ Enhanced button search failed: {exc}")
            return False

    async def fetch_input_content(self, page):
        """
        Fetches the value inside the first name input field in the LinkedIn Easy Apply modal.
        You can generalize for other fields if needed!
        """
        # The id is visible in the screenshot: 
        # single-line-text-form-component-formElement-urn-li-jobs-applyformcommon-easyApplyFormElement-4270075460-21781429932-text
        input_id = "single-line-text-form-component-formElement-urn-li-jobs-applyformcommon-easyApplyFormElement-4270075460-21781429932-text"
        selector = f"input#{input_id}"
        try:
            await page.wait_for_selector(selector, timeout=10000)
            value = await page.locator(selector).input_value()
            logger.info(f"🔎 Content of input field (id={input_id}): {value}")
            return value
        except Exception as e:
            logger.error(f"❌ Could not fetch input content for {input_id}: {e}")
            return None

# ─────────────────────────────  TEST MAIN  ────────────────────────────
async def apply_button_finder_main():
    browser_mgr = BrowserManager(headless=False)
    if not await browser_mgr.setup():
        return

    local_data = load_storage("data_dump/localStorage.json")
    session_data = load_storage("data_dump/sessionStorage.json")

    page = await browser_mgr.create_page()
    await inject_storage(page, local_data, session_data)

    nav = PageNavigator(browser_mgr)
    finder = ApplyButtonFinder(nav)

    job_url = (
        "https://in.linkedin.com/jobs/view/react-js-software-engineer-paytm-money-at-one97-communications-limited-4270075460/"
    )

    if await nav.navigate_to_job(page, job_url):
        modal_ok = await finder.find_and_click_apply_button(page)
        await asyncio.sleep(2)  # wait for modal to fully render fields
        if modal_ok:
            input_content = await finder.fetch_input_content(page)
            logger.info(f"Fetched input field content: {input_content}")
        await asyncio.sleep(10)
    else:
        logger.error("❌ Failed to navigate to job")

    await browser_mgr.cleanup()

# ───────────────────────────────  RUN  ────────────────────────────────
if __name__ == "__main__":
    asyncio.run(apply_button_finder_main())