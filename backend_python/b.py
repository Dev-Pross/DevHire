from pathlib import Path
import logging
import time
import json
import random
import asyncio

import requests  # if you really need it elsewhere
from playwright.async_api import async_playwright

# ─────────────────────────────  LOGGING  ──────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ────────────────────────  COOKIE  MANAGER  ───────────────────────────
class CookieManager:
    def __init__(self, cookies_dir: str = "cookies"):
        self.cookies_dir = Path(cookies_dir)
        self.linkedin_cookies: dict[str, str] = {}

        # cookies LinkedIn often requires
        self.essential_cookies = [
            "li_at",
            "JSESSIONID",
            "bcookie",
            "bscookie",
            "lang",
            "lidc",
            "UserMatchHistory",
            "li_a",
            "li_mc",
        ]

    def load_all_linkedin_cookies(self) -> bool:
        """Load cookies from combined JSON or individual *.txt files"""
        try:
            combined = self.cookies_dir / "all_linkedin_cookies.json"
            if combined.exists():
                self.linkedin_cookies = json.loads(combined.read_text(encoding="utf-8"))
                logger.info(
                    "✅ Loaded %s LinkedIn cookies from JSON: %s",
                    len(self.linkedin_cookies),
                    list(self.linkedin_cookies.keys()),
                )
                return True

            # individual files
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

# ────────────────────────  BROWSER  MANAGER  ──────────────────────────
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
            cookies_file = Path("cookies/all_linkedin_cookies.json")
            if cookies_file.exists():
                self.linkedin_cookies = json.loads(cookies_file.read_text())
                return True
            
            # Load ALL available cookies, not just li_at
            all_cookies = self.cookie_manager.get_all_cookies()
            if all_cookies:
                self.linkedin_cookies = all_cookies
                return True
                
            return False
        except Exception as exc:
            logger.error("❌ Error loading cookies: %s", exc)
            return False

    async def setup(self) -> bool:
        """launch browser, create context, inject cookies + heartbeat patch"""
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

            # Add stealth measures
            await self.context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });
            """)

            await self._handle_heartbeat_requests_on_context(self.context)

            # inject cookies with more realistic settings
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
            
            # ✅ FIXED: Correct way to log cookie names
            cookie_names = [cookie["name"] for cookie in cookies_to_add]
            logger.info("📋 Injected cookies: %s", cookie_names)
            
            return True
        except Exception as exc:
            logger.error("❌ Browser setup failed: %s", exc)
            return False

    async def _handle_heartbeat_requests_on_context(self, context):
        """Intercept LinkedIn realtime heartbeat requests to prevent 400 errors."""
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
        """Add common chromium/chrome headers to every request."""
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
        """Navigate directly to job page - skip validation to avoid LinkedIn blocking"""
        try:
            logger.info("🔄 Navigating directly to job URL...")
            
            await page.wait_for_timeout(random.randint(2000, 5000))
            await page.goto(job_url, wait_until="domcontentloaded", timeout=60000)
            # await page.wait_for_function("document.readyState==='complete'", timeout=15000)
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

# ─────────────────────────  APPLY BUTTON FINDER  ──────────────────────
class ApplyButtonFinder:
    def __init__(self, page_navigator: PageNavigator):
        self.page_navigator = page_navigator

    async def debug_page_structure(self, page):
        """Debug what's available on the job page"""
        try:
            logger.info("🔍 Debugging page structure...")
            
            # Check for any apply-related elements
            apply_elements = await page.locator('*:has-text("Apply"), *[class*="apply"], *[data-control-name*="apply"]').count()
            logger.info(f"📊 Found {apply_elements} apply-related elements")
            
            # List all buttons on the page
            buttons = await page.locator('button').all()
            logger.info(f"📊 Found {len(buttons)} buttons on page:")
            
            for i, button in enumerate(buttons[:10]):  # Show first 10 buttons
                try:
                    text = (await button.text_content() or "").strip()
                    class_name = await button.get_attribute('class') or ""
                    data_control = await button.get_attribute('data-control-name') or ""
                    logger.info(f"  Button {i+1}: '{text}' | class='{class_name[:50]}...' | data-control='{data_control}'")
                except:
                    logger.info(f"  Button {i+1}: [Error reading button info]")
            
            # Check for external apply links
            external_links = await page.locator('a[href*="apply"], a:has-text("Apply")').all()
            if external_links:
                logger.info(f"🔗 Found {len(external_links)} external apply links:")
                for i, link in enumerate(external_links[:5]):
                    try:
                        text = (await link.text_content() or "").strip()
                        href = await link.get_attribute('href') or ""
                        logger.info(f"  Link {i+1}: '{text}' → {href}")
                    except:
                        pass
            
            # Check for specific LinkedIn job elements
            job_card = await page.locator('.jobs-unified-top-card, .job-details-card').count()
            logger.info(f"📄 Job card elements found: {job_card}")
            
            # Look for "not available" or "external" messages
            external_msgs = await page.locator('*:has-text("company website"), *:has-text("external"), *:has-text("not available")').count()
            if external_msgs > 0:
                logger.warning("⚠️ This job may require external application")
                
        except Exception as e:
            logger.error(f"❌ Debug failed: {e}")

# Add this to your ApplyButtonFinder class
    async def find_and_click_apply_button(self, page):
        """Enhanced debugging version to see what's actually on the page"""
        logger.info("🔍 Enhanced Easy Apply button search...")
        
        try:
            # First, let's see ALL buttons with "Apply" in their text
            logger.info("📊 Looking for ALL buttons containing 'Apply'...")
            all_apply_buttons = await page.locator('button:has-text("Apply")').all()
            
            logger.info(f"Found {len(all_apply_buttons)} buttons with 'Apply' text")
            
            for i, button in enumerate(all_apply_buttons):
                try:
                    text = await button.text_content()
                    class_attr = await button.get_attribute('class')
                    is_visible = await button.is_visible()
                    is_enabled = await button.is_enabled()
                    
                    logger.info(f"  Button {i+1}: '{text.strip()}' | Visible: {is_visible} | Enabled: {is_enabled}")
                    logger.info(f"    Classes: {class_attr}")
                    
                    # If this looks like the Easy Apply button, try to click it
                    if "Easy Apply" in text and is_visible and is_enabled:
                        logger.info(f"🎯 Attempting to click button {i+1}...")
                        await button.scroll_into_view_if_needed()
                        await page.wait_for_timeout(1000)
                        await button.click()
                        logger.info("✅ Successfully clicked Easy Apply button!")
                        return True
                        
                except Exception as e:
                    logger.error(f"Error examining button {i+1}: {e}")
                    continue
            
            # If direct approach didn't work, try the class-based approach
            logger.info("🔍 Trying class-based selector: .jobs-apply-button")
            try:
                # Use a more direct approach
                jobs_apply_buttons = await page.locator('.jobs-apply-button').all()
                logger.info(f"Found {len(jobs_apply_buttons)} elements with .jobs-apply-button class")
                
                for i, button in enumerate(jobs_apply_buttons):
                    try:
                        text = await button.text_content()
                        is_visible = await button.is_visible()
                        is_enabled = await button.is_enabled()
                        
                        logger.info(f"  jobs-apply-button {i+1}: '{text.strip()}' | Visible: {is_visible} | Enabled: {is_enabled}")
                        
                        if is_visible and is_enabled and "Apply" in text:
                            logger.info(f"🎯 Clicking jobs-apply-button {i+1}...")
                            await button.scroll_into_view_if_needed()
                            await page.wait_for_timeout(1000)
                            await button.click()
                            await page.wait_for_timeout(10000)
                            logger.info("✅ Successfully clicked apply button!")

                            return True
                            
                    except Exception as e:
                        logger.error(f"Error with jobs-apply-button {i+1}: {e}")
                        continue
                        
            except Exception as e:
                logger.error(f"Class-based selector failed: {e}")
            
            # Last resort: Use XPath to find any button with "Easy Apply" text
            logger.info("🔍 Last resort: Using XPath...")
            try:
                xpath_button = page.locator("//button[contains(text(), 'Easy Apply')]").first
                if await xpath_button.count() > 0:
                    text = await xpath_button.text_content()
                    logger.info(f"XPath found button: '{text.strip()}'")
                    await xpath_button.scroll_into_view_if_needed()
                    await page.wait_for_timeout(1000)
                    await xpath_button.click()
                    logger.info("✅ XPath click successful!")
                    return True
            except Exception as e:
                logger.error(f"XPath approach failed: {e}")
            
            logger.error("❌ All approaches failed to find/click Easy Apply button")
            return False
            
        except Exception as exc:
            logger.error(f"❌ Enhanced button search failed: {exc}")
            return False

    async def _verify_authenticated_button(self, button):
            """
            Verify button is authenticated and clickable
            
            Args:
                button: Playwright button locator
                
            Returns:
                bool: True if button is authenticated and ready
            """
            try:
                # Check visibility and enabled state
                if not await button.is_visible() or not await button.is_enabled():
                    return False
                
                # Check if button has authentication-dependent attributes
                button_text = await button.text_content()
                if not button_text or len(button_text.strip()) == 0:
                    return False
                
                # Verify button is not in a loading or disabled state
                class_name = await button.get_attribute('class') or ''
                if any(state in class_name.lower() for state in ['disabled', 'loading', 'pending']):
                    return False
                
                return True
                
            except Exception:
                return False
        
# ─────────────────────────────  TEST MAIN  ────────────────────────────
async def apply_button_finder_main():
    browser_mgr = BrowserManager(headless=False)
    if not await browser_mgr.setup():
        return

    page = await browser_mgr.create_page()
    nav = PageNavigator(browser_mgr)
    finder = ApplyButtonFinder(nav)

    job_url = (
        "https://in.linkedin.com/jobs/view/senior-ai-backend-engineer-at-bonsen-ai-4269455696?position=50&pageNum=0&refId=6HvcECkGD2355naiixL3hg%3D%3D&trackingId=e7HJcNOXMtfxJ4T42iQg9A%3D%3D"
    )
    
    if await nav.navigate_to_job(page, job_url):
        await finder.find_and_click_apply_button(page)
        await asyncio.sleep(10)
    else:
        logger.error("❌ Failed to navigate to job")

    await browser_mgr.cleanup()

# ───────────────────────────────  RUN  ────────────────────────────────
if __name__ == "__main__":
    asyncio.run(apply_button_finder_main())
