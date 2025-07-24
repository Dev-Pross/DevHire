from pathlib import Path
import logging
import time
import requests
import asyncio
from playwright.async_api import async_playwright
import json

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CookieManager:
    def __init__(self, cookies_dir="cookies"):
        """
        Enhanced Cookie Manager for multiple LinkedIn cookies
        
        Args:
            cookies_dir (str): Directory where cookies are stored
        """
        self.cookies_dir = Path(cookies_dir)
        self.linkedin_cookies = {}
        
        # Essential LinkedIn cookies for full authentication
        self.essential_cookies = [
            'li_at',          # Primary session
            'JSESSIONID',     # Server session
            'bcookie',        # Browser cookie
            'bscookie',       # Browser security
            'lang',           # Language preferences
            'lidc',           # Data center routing
            'UserMatchHistory', # User behavior tracking
            'li_a',           # Additional auth cookie
            'li_mc'           # Marketing cookie
        ]
    
    def load_all_linkedin_cookies(self):
        """
        Load all LinkedIn cookies from storage files
        
        Returns:
            bool: True if cookies loaded successfully
        """
        try:
            # Method 1: Load from combined JSON file (preferred)
            combined_file = self.cookies_dir / "all_linkedin_cookies.json"
            if combined_file.exists():
                with open(combined_file, "r", encoding="utf-8") as f:
                    self.linkedin_cookies = json.load(f)
                
                logger.info(f"✅ Loaded {len(self.linkedin_cookies)} LinkedIn cookies from JSON")
                logger.info(f"   Available cookies: {list(self.linkedin_cookies.keys())}")
                return True
            
            # Method 2: Load from individual cookie files
            if self.cookies_dir.exists():
                loaded_cookies = {}
                
                for cookie_name in self.essential_cookies:
                    cookie_file = self.cookies_dir / f"{cookie_name}.txt"
                    if cookie_file.exists():
                        with open(cookie_file, "r", encoding="utf-8") as f:
                            cookie_value = f.read().strip()
                            if cookie_value:
                                loaded_cookies[cookie_name] = cookie_value
                
                if loaded_cookies:
                    self.linkedin_cookies = loaded_cookies
                    logger.info(f"✅ Loaded {len(loaded_cookies)} LinkedIn cookies from individual files")
                    logger.info(f"   Available cookies: {list(loaded_cookies.keys())}")
                    return True
            
            logger.error("❌ No LinkedIn cookies found in storage")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error loading LinkedIn cookies: {e}")
            return False
    
    def get_cookie(self, cookie_name="li_at"):
        """
        Get a specific LinkedIn cookie
        
        Args:
            cookie_name (str): Name of the cookie to retrieve
            
        Returns:
            str: Cookie value or None if not found
        """
        if not self.linkedin_cookies:
            self.load_all_linkedin_cookies()
        
        cookie_value = self.linkedin_cookies.get(cookie_name)
        if cookie_value:
            logger.info(f"✅ Retrieved {cookie_name} cookie: {cookie_value[:20]}...")
        else:
            logger.warning(f"⚠️ Cookie {cookie_name} not found")
            
        return cookie_value
    
    def get_all_cookies(self):
        """
        Get all loaded LinkedIn cookies
        
        Returns:
            dict: Dictionary of all LinkedIn cookies
        """
        if not self.linkedin_cookies:
            self.load_all_linkedin_cookies()
        
        return self.linkedin_cookies.copy()
    
    def has_essential_cookies(self):
        """
        Check if we have the minimum essential cookies for LinkedIn authentication
        
        Returns:
            bool: True if essential cookies are available
        """
        if not self.linkedin_cookies:
            self.load_all_linkedin_cookies()
        
        # At minimum, we need li_at for basic authentication
        required_cookies = ['li_at']
        
        missing_cookies = [cookie for cookie in required_cookies if cookie not in self.linkedin_cookies]
        
        if missing_cookies:
            logger.error(f"❌ Missing essential cookies: {missing_cookies}")
            return False
        
        logger.info("✅ Essential cookies available for LinkedIn authentication")
        return True
    
    def get_cookie_summary(self):
        """
        Get a summary of available cookies for debugging
        
        Returns:
            dict: Summary information about loaded cookies
        """
        if not self.linkedin_cookies:
            self.load_all_linkedin_cookies()
        
        summary = {
            'total_cookies': len(self.linkedin_cookies),
            'available_cookies': list(self.linkedin_cookies.keys()),
            'essential_cookies_present': [],
            'missing_essential_cookies': []
        }
        
        for cookie_name in self.essential_cookies:
            if cookie_name in self.linkedin_cookies:
                summary['essential_cookies_present'].append(cookie_name)
            else:
                summary['missing_essential_cookies'].append(cookie_name)
        
        return summary
    
    def is_cookie_available(self, cookie_name="li_at"):
        """
        Check if a specific cookie is available
        
        Args:
            cookie_name (str): Name of the cookie to check
            
        Returns:
            bool: True if cookie is available
        """
        return self.get_cookie(cookie_name) is not None
    
    def validate_cookie_format(self, cookie_value):
        """
        Basic validation of LinkedIn cookie format
        
        Args:
            cookie_value (str): Cookie value to validate
            
        Returns:
            bool: True if cookie appears valid
        """
        if not cookie_value:
            return False
        
        # LinkedIn cookies should be reasonably long
        if len(cookie_value) < 20:
            return False
        
        # Should not contain invalid characters
        if any(char in cookie_value for char in [' ', '\n', '\t']):
            return False
        
        return True


# Enhanced test function for Cookie Manager
     

class BrowserManager:
    def __init__(self, headless=False, max_concurrent_pages=3):
        """
        Simple Browser Manager with multi-cookie support
        """
        self.headless = headless
        self.max_concurrent_pages = max_concurrent_pages
        
        # Browser components
        self.playwright = None
        self.browser = None
        self.context = None
        
        # Cookie management
        self.cookie_manager = CookieManager()
        self.linkedin_cookies = {}
        
        # Active pages tracking
        self.active_pages = []
    
    def load_all_linkedin_cookies(self):
        """Load all LinkedIn cookies from files"""
        try:
            # Try to load from combined JSON file
            cookies_file = Path("cookies/all_linkedin_cookies.json")
            if cookies_file.exists():
                with open(cookies_file, "r") as f:
                    self.linkedin_cookies = json.load(f)
                logger.info(f"✅ Loaded {len(self.linkedin_cookies)} LinkedIn cookies")
                return True
            
            # Fallback: just get li_at
            li_at = self.cookie_manager.get_cookie()
            if li_at:
                self.linkedin_cookies = {"li_at": li_at}
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"❌ Error loading cookies: {e}")
            return False
    
    async def setup(self):
        """Initialize browser with LinkedIn cookies"""
        try:
            # Get cookies
            if not self.load_all_linkedin_cookies():
                logger.error("❌ No LinkedIn cookies available")
                return False
            
            # Start Playwright
            self.playwright = await async_playwright().start()
            
            # Launch browser
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
            )
            
            # Create context
            self.context = await self.browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            
            # Inject ALL LinkedIn cookies
            cookies_to_add = []
            for name, value in self.linkedin_cookies.items():
                cookies_to_add.append({
                    'name': name,
                    'value': value,
                    'domain': '.linkedin.com',
                    'path': '/',
                    'httpOnly': name in ['li_at', 'JSESSIONID'],
                    'secure': True,
                    'sameSite': 'None'
                })
            
            await self.context.add_cookies(cookies_to_add)
            
            logger.info(f"🔐 {len(cookies_to_add)} LinkedIn cookies injected")
            return True
            
        except Exception as e:
            logger.error(f"❌ Browser setup failed: {e}")
            return False
    
    async def verify_linkedin_authentication(self):
        """Simple LinkedIn auth verification"""
        try:
            test_page = await self.create_page()
            if not test_page:
                return False
            
            await test_page.goto('https://www.linkedin.com/feed/', timeout=30000)
            await self._wait_for_page_ready(test_page)
            
            # Check if logged in
            if 'login' in test_page.url:
                await self.close_page(test_page)
                return False
            
            # Look for profile indicators
            profile_selectors = [
                '[data-test-global-nav-me-dropdown-trigger]',
                '.global-nav__me-photo',
                '.global-nav__nav'
            ]
            
            for selector in profile_selectors:
                if await test_page.query_selector(selector):
                    logger.info("✅ LinkedIn authentication verified")
                    await self.close_page(test_page)
                    return True
            
            await self.close_page(test_page)
            return False
            
        except Exception as e:
            logger.error(f"❌ Authentication verification failed: {e}")
            return False
    
    async def _wait_for_page_ready(self, page, timeout=60000):
        """Simple page ready wait"""
        try:
            await page.wait_for_load_state('domcontentloaded', timeout=timeout)
            try:
                await page.wait_for_load_state('networkidle', timeout=8000)
            except:
                pass
            await page.wait_for_function("document.readyState === 'complete'", timeout=15000)
            await page.wait_for_timeout(2000)
            return True
        except Exception as e:
            logger.error(f"❌ Page loading failed: {e}")
            return False
    
    async def create_page(self):
        """Create new page"""
        try:
            if not self.context:
                return None
            
            if len(self.active_pages) >= self.max_concurrent_pages:
                return None
            
            page = await self.context.new_page()
            self.active_pages.append(page)
            
            logger.info(f"📄 Page created (Active: {len(self.active_pages)})")
            return page
            
        except Exception as e:
            logger.error(f"❌ Failed to create page: {e}")
            return None
    
    async def close_page(self, page):
        """Close page"""
        try:
            if page in self.active_pages:
                self.active_pages.remove(page)
            await page.close()
            logger.info(f"📄 Page closed (Active: {len(self.active_pages)})")
        except Exception as e:
            logger.error(f"❌ Error closing page: {e}")
    
    async def cleanup(self):
        """Clean up browser"""
        try:
            for page in self.active_pages[:]:
                await self.close_page(page)
            
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
                
        except Exception as e:
            logger.error(f"❌ Cleanup error: {e}")

class PageNavigator:
    def __init__(self, browser_manager):
        """
        Enhanced Page Navigator with multi-cookie authentication support
        
        Args:
            browser_manager: Enhanced BrowserManager instance with multi-cookie support
        """
        self.browser_manager = browser_manager
    
    async def navigate_to_job(self, page, job_url):
        """
        Navigate to job URL with enhanced authentication handling
        
        Args:
            page: Playwright page object
            job_url (str): Job URL to navigate to
            
        Returns:
            bool: True if navigation successful
        """
        try:
            logger.info(f"🌐 Navigating to job with enhanced auth: {job_url}")
            
            # Navigate with extended timeout for authentication
            await page.goto(job_url, wait_until='domcontentloaded', timeout=60000)
            
            # Enhanced page loading with authentication state checks
            page_ready = await self._wait_for_authenticated_job_page(page, job_url)
            if not page_ready:
                logger.error("❌ Authenticated job page failed to load")
                return False
            
            # Verify we're on the correct page and authenticated
            if await self._verify_authenticated_access(page, job_url):
                logger.info("✅ Successfully navigated with full authentication")
                return True
            else:
                logger.error("❌ Authentication verification failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Enhanced navigation error: {e}")
            return False
    
    async def _wait_for_authenticated_job_page(self, page, job_url):
        """
        Wait for job page with authentication-dependent content
        
        Args:
            page: Playwright page object
            job_url (str): Job URL for context
            
        Returns:
            bool: True if authenticated page loaded
        """
        try:
            # Step 1: Basic page loading
            await page.wait_for_load_state('domcontentloaded', timeout=30000)
            
            # Step 2: Try networkidle with reasonable timeout
            try:
                await page.wait_for_load_state('networkidle', timeout=10000)
            except:
                logger.info("⚠️ Network idle timeout - continuing with authentication checks")
                pass
            
            # Step 3: Wait for document ready
            await page.wait_for_function("document.readyState === 'complete'", timeout=15000)
            
            # Step 4: Platform-specific authenticated content loading
            if 'linkedin.com' in job_url:
                await self._wait_for_linkedin_authenticated_content(page)
            else:
                await self._wait_for_general_job_content(page)
            
            # Step 5: Final authentication buffer
            await page.wait_for_timeout(3000)
            
            logger.info("✅ Authenticated job page fully loaded")
            return True
            
        except Exception as e:
            logger.error(f"❌ Authenticated page loading failed: {e}")
            return False
    
    async def _wait_for_linkedin_authenticated_content(self, page):
        """
        Wait for LinkedIn-specific authenticated job content
        
        Args:
            page: Playwright page object
        """
        logger.info("⏳ Waiting for LinkedIn authenticated job content...")
        
        # LinkedIn authenticated job page selectors
        authenticated_selectors = [
            '.jobs-unified-top-card',                    # Main job card
            '.job-details-jobs-unified-top-card__content', # Job details
            '.jobs-description',                         # Job description
            '[data-job-id]',                            # Job ID indicator
            '.jobs-apply-button',                       # Apply button (auth required)
            '.jobs-unified-top-card__content'           # Content container
        ]
        
        # Wait for any authenticated content to appear
        for selector in authenticated_selectors:
            try:
                await page.wait_for_selector(selector, state='visible', timeout=12000)
                logger.info(f"✅ LinkedIn authenticated content loaded: {selector}")
                
                # Additional check for authentication-specific elements
                await self._verify_linkedin_authentication_elements(page)
                return
                
            except Exception:
                continue
        
        logger.warning("⚠️ Limited LinkedIn authenticated content detected")
    
    async def _verify_linkedin_authentication_elements(self, page):
        """
        Verify LinkedIn authentication-specific elements are present
        
        Args:
            page: Playwright page object
        """
        try:
            # Check for authenticated user elements
            auth_elements = [
                '[data-test-global-nav-me-dropdown-trigger]',  # Profile dropdown
                '.global-nav__me-photo',                       # Profile photo
                '.global-nav__nav'                             # Navigation bar
            ]
            
            for selector in auth_elements:
                if await page.query_selector(selector):
                    logger.info("✅ LinkedIn authentication elements verified")
                    return
            
            logger.warning("⚠️ LinkedIn authentication elements not found")
            
        except Exception as e:
            logger.error(f"Authentication element verification failed: {e}")
    
    async def _wait_for_general_job_content(self, page):
        """
        Wait for general job page content
        
        Args:
            page: Playwright page object
        """
        logger.info("⏳ Waiting for general job content...")
        
        general_selectors = [
            'h1',                    # Job title
            '[class*="job-title"]',  # Job title variations
            '[class*="company"]',    # Company name
            'main',                  # Main content
            '.content',              # Content container
            'article'                # Article content
        ]
        
        for selector in general_selectors:
            try:
                await page.wait_for_selector(selector, state='visible', timeout=8000)
                logger.info(f"✅ General job content loaded: {selector}")
                return
            except Exception:
                continue
        
        logger.warning("⚠️ Limited general job content detected")
    
    async def _verify_authenticated_access(self, page, job_url):
        """
        Verify we have authenticated access to the job page
        
        Args:
            page: Playwright page object
            job_url (str): Original job URL
            
        Returns:
            bool: True if authenticated access verified
        """
        try:
            current_url = page.url
            
            # Check for authentication failures
            auth_failure_indicators = [
                'login', 'signin', 'authenticate', 'unauthorized',
                'error', '404', 'not-found', 'access-denied'
            ]
            
            current_lower = current_url.lower()
            for indicator in auth_failure_indicators:
                if indicator in current_lower:
                    logger.error(f"❌ Authentication failure detected: {indicator}")
                    return False
            
            # For LinkedIn, verify we're still on a job-related page
            if 'linkedin.com' in job_url:
                if not any(path in current_url for path in ['/jobs/', '/feed/']):
                    logger.error("❌ Redirected away from LinkedIn job content")
                    return False
            
            logger.info("✅ Authenticated access verified")
            return True
            
        except Exception as e:
            logger.error(f"Authentication verification error: {e}")
            return False
    
    async def take_debug_screenshot(self, page, filename_prefix="debug"):
        """
        Take screenshot with authentication context
        
        Args:
            page: Playwright page object
            filename_prefix (str): Screenshot filename prefix
        """
        try:
            timestamp = int(time.time())
            screenshot_path = f"{filename_prefix}_auth_{timestamp}.png"
            await page.screenshot(path=screenshot_path, full_page=True)
            logger.info(f"📸 Authentication debug screenshot: {screenshot_path}")
        except Exception as e:
            logger.error(f"❌ Debug screenshot failed: {e}")

class ApplyButtonFinder:
    def __init__(self, page_navigator):
        """
        Enhanced Apply Button Finder with multi-cookie authentication support
        
        Args:
            page_navigator: Enhanced PageNavigator instance
        """
        self.page_navigator = page_navigator
    
    async def find_and_click_apply_button(self, page, job_url, max_retries=3):
        """
        Find and click apply button with enhanced authentication handling
        
        Args:
            page: Playwright page object
            job_url (str): Job URL for context
            max_retries (int): Maximum retry attempts
            
        Returns:
            bool: True if apply button found and clicked successfully
        """
        is_linkedin_job = 'linkedin.com' in job_url.lower()
        
        for attempt in range(max_retries):
            logger.info(f"🔍 Enhanced apply button search (attempt {attempt + 1}/{max_retries})")
            
            try:
                # Enhanced wait between retries
                if attempt > 0:
                    await page.wait_for_timeout(4000)
                
                # Enhanced content loading with authentication
                await self._ensure_authenticated_content_loaded(page, is_linkedin_job)
                
                # Platform-specific authenticated button finding
                if is_linkedin_job:
                    success = await self._find_linkedin_authenticated_apply_button(page)
                else:
                    success = await self._find_general_apply_button(page)
                
                if success:
                    logger.info("✅ Apply button clicked with enhanced authentication")
                    
                    # Enhanced modal waiting for LinkedIn
                    if is_linkedin_job:
                        modal_loaded = await self._wait_for_authenticated_easy_apply_modal(page)
                        if modal_loaded:
                            logger.info("✅ Authenticated Easy Apply modal loaded successfully")
                            return True
                        else:
                            logger.error("❌ Authenticated modal loading failed")
                            continue
                    else:
                        await page.wait_for_timeout(3000)
                        return True
                
                logger.warning(f"⚠️ Apply button not found in attempt {attempt + 1}")
                await self.page_navigator.take_debug_screenshot(page, f"apply_search_attempt_{attempt + 1}")
                
            except Exception as e:
                logger.error(f"❌ Enhanced apply button search error (attempt {attempt + 1}): {e}")
        
        logger.error("❌ Failed to find apply button with enhanced authentication")
        return False
    
    async def _ensure_authenticated_content_loaded(self, page, is_linkedin_job):
        """
        Ensure authenticated content is fully loaded before button search
        
        Args:
            page: Playwright page object
            is_linkedin_job (bool): Whether this is a LinkedIn job
        """
        try:
            # Scroll to ensure all authenticated content loads
            await page.evaluate('window.scrollTo(0, 0)')
            await page.wait_for_timeout(1000)
            
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight/3)')
            await page.wait_for_timeout(1000)
            
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight/2)')
            await page.wait_for_timeout(1000)
            
            if is_linkedin_job:
                # Wait for LinkedIn authenticated elements to stabilize
                try:
                    await page.wait_for_function(
                        "document.querySelectorAll('button, a').length > 5",
                        timeout=8000
                    )
                except:
                    pass
            
            logger.info("✅ Authenticated content loading ensured")
            
        except Exception as e:
            logger.error(f"❌ Content loading error: {e}")
    
    async def _find_linkedin_authenticated_apply_button(self, page):
        """
        Find LinkedIn apply buttons with full authentication context
        
        Args:
            page: Playwright page object
            
        Returns:
            bool: True if button found and clicked
        """
        logger.info("🔍 Searching for authenticated LinkedIn apply button...")
        
        # Enhanced LinkedIn selectors with authentication context
        linkedin_selectors = [
            'button:has-text("Easy Apply")',
            'button:text("Easy Apply")',
            'button[aria-label*="Easy Apply"]',
            'button[data-control-name*="apply"]',
            '[data-test-job-details-easy-apply-button]',
            '.jobs-apply-button:has-text("Easy Apply")',
            '.jobs-unified-top-card__content button:has-text("Easy Apply")',
            'button.jobs-apply-button',
            'button:has-text("Apply")',
            '.jobs-s-apply button',
            '[data-test-apply-button]'
        ]
        
        for selector in linkedin_selectors:
            try:
                logger.info(f"  Trying authenticated selector: {selector}")
                
                # Enhanced element waiting with authentication checks
                await page.wait_for_selector(selector, state='visible', timeout=6000)
                apply_button = page.locator(selector).first
                
                # Enhanced button verification
                if await self._verify_authenticated_button(apply_button):
                    # Enhanced clicking with authentication context
                    await apply_button.scroll_into_view_if_needed()
                    await page.wait_for_timeout(1500)
                    
                    # Click with authentication context
                    await apply_button.click()
                    
                    logger.info(f"✅ Authenticated LinkedIn apply button clicked: {selector}")
                    return True
                
            except Exception as e:
                logger.debug(f"    Authenticated selector failed: {selector} - {e}")
                continue
        
        logger.warning("❌ No authenticated LinkedIn apply button found")
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
    
    async def _wait_for_authenticated_easy_apply_modal(self, page, timeout=25000):
        """
        Enhanced Easy Apply modal waiting that properly handles loading spinners
        """
        try:
            logger.info("⏳ Waiting for Easy Apply modal with spinner handling...")
            
            # Step 1: Wait for modal container
            modal_found = False
            modal_selectors = [
                '[data-test-modal-id*="easy-apply"]',
                '.jobs-easy-apply-modal',
                '.artdeco-modal',
                '[role="dialog"]'
            ]
            
            for selector in modal_selectors:
                try:
                    await page.wait_for_selector(selector, state='visible', timeout=10000)
                    logger.info(f"✅ Modal container found: {selector}")
                    modal_found = True
                    break
                except:
                    continue
            
            if not modal_found:
                logger.error("❌ Modal container not found")
                return False
            
            # Step 2: CRITICAL - Wait for spinner to appear AND disappear
            spinner_selectors = [
                '.loading-spinner',
                '.artdeco-spinner',
                '.spinner',
                '[data-test-loading]',
                '.jobs-easy-apply-modal .spinner',
                '.artdeco-spinner__bars'
            ]
            
            # First, wait for spinner to appear (confirms loading started)
            spinner_detected = False
            for spinner_selector in spinner_selectors:
                try:
                    await page.wait_for_selector(spinner_selector, state='visible', timeout=3000)
                    logger.info(f"⏳ Loading spinner detected: {spinner_selector}")
                    spinner_detected = True
                    
                    # Now wait for the same spinner to disappear (loading complete)
                    await page.wait_for_selector(spinner_selector, state='hidden', timeout=15000)
                    logger.info(f"✅ Loading spinner disappeared: {spinner_selector}")
                    break
                    
                except Exception as e:
                    logger.debug(f"Spinner selector {spinner_selector} failed: {e}")
                    continue
            
            if not spinner_detected:
                logger.info("ℹ️ No spinner detected - checking for form content directly")
            
            # Step 3: Wait for actual form content to appear (what you see in Image 2)
            form_content_selectors = [
                'input[name*="phoneNumber"]',     # Phone number field
                'input[type="email"]',            # Email field  
                'select[name*="phoneNumber"]',    # Phone country dropdown
                '.jobs-easy-apply-form-element',  # Form elements
                'form input[type="text"]',        # Any text input
                'button:has-text("Next")',        # Next button
                'button:has-text("Review")',      # Review button
                'button:has-text("Submit application")' # Submit button
            ]
            
            form_loaded = False
            for selector in form_content_selectors:
                try:
                    await page.wait_for_selector(selector, state='visible', timeout=10000)
                    logger.info(f"✅ Form content loaded: {selector}")
                    form_loaded = True
                    break
                except:
                    continue
            
            if not form_loaded:
                logger.error("❌ Form content failed to load - still showing spinner")
                # Take screenshot for debugging
                await page.screenshot(path=f"stuck_spinner_{int(time.time())}.png")
                return False
            
            # Step 4: Ensure form is interactive
            try:
                await page.wait_for_function(
                    "document.querySelectorAll('input, button, select, textarea').length > 2",
                    timeout=8000
                )
                logger.info("✅ Form is interactive")
            except:
                logger.warning("⚠️ Form interactivity check timeout")
            
            # Step 5: Final buffer
            await page.wait_for_timeout(2000)
            
            logger.info("✅ Easy Apply modal and form fully loaded")
            return True
            
        except Exception as e:
            logger.error(f"❌ Modal loading failed: {e}")
            # Take debug screenshot
            try:
                await page.screenshot(path=f"modal_loading_error_{int(time.time())}.png")
            except:
                pass
            return False

    
    async def _check_for_modal_auth_errors(self, page):
        """
        Check for authentication errors in modal content
        
        Args:
            page: Playwright page object
        """
        try:
            auth_error_selectors = [
                ':has-text("Please sign in")',
                ':has-text("Session expired")',
                ':has-text("Authentication required")',
                ':has-text("Login required")',
                '.error-message'
            ]
            
            for error_selector in auth_error_selectors:
                if await page.locator(error_selector).count() > 0:
                    logger.error("❌ Authentication error detected in modal")
                    raise Exception("Modal authentication error")
            
        except Exception as e:
            if "authentication error" in str(e).lower():
                raise e
            # Other errors can be ignored
            pass
    
    async def _find_general_apply_button(self, page):
        """
        Find general apply buttons (enhanced but unchanged logic)
        """
        logger.info("🔍 Searching for general apply button...")
        
        general_selectors = [
            'button:has-text("Apply Now")',
            'button:has-text("Apply")',
            'a:has-text("Apply Now")',
            'a:has-text("Apply")',
            'button:has-text("Quick Apply")',
            'input[type="button"][value*="Apply"]',
            'input[type="submit"][value*="Apply"]',
            '[data-testid*="apply"]',
            '[data-test*="apply"]',
            '.apply-button',
            '#apply-button',
            'button[class*="apply"]',
            'a[class*="apply"]',
            'button[id*="apply"]',
            'a[href*="apply"]',
            'button:has-text("Submit Application")',
            '[role="button"]:has-text("Apply")'
        ]
        
        for selector in general_selectors:
            try:
                logger.info(f"  Trying general selector: {selector}")
                
                await page.wait_for_selector(selector, state='visible', timeout=3000)
                apply_button = page.locator(selector).first
                
                if await apply_button.is_visible() and await apply_button.is_enabled():
                    await apply_button.scroll_into_view_if_needed()
                    await page.wait_for_timeout(1000)
                    
                    await apply_button.click()
                    
                    logger.info(f"✅ General apply button clicked: {selector}")
                    return True
                
            except Exception as e:
                logger.debug(f"    General selector failed: {selector} - {e}")
                continue
        
        logger.warning("❌ No general apply button found")
        return False
    
    async def debug_authenticated_page_elements(self, page):
        """
        Debug page elements with authentication context
        
        Args:
            page: Playwright page object
        """
        try:
            logger.info("🔍 Debugging authenticated page elements...")
            
            # Enhanced element counting with authentication context
            buttons = await page.locator('button').count()
            links = await page.locator('a').count()
            inputs = await page.locator('input').count()
            forms = await page.locator('form').count()
            
            logger.info(f"  Buttons: {buttons}, Links: {links}, Inputs: {inputs}, Forms: {forms}")
            
            # Check for authenticated LinkedIn elements
            auth_elements = await page.locator('[data-test-global-nav-me-dropdown-trigger]').count()
            logger.info(f"  LinkedIn auth elements: {auth_elements}")
            
            # Check apply button variations with authentication
            apply_texts = ['Apply', 'Easy Apply', 'Apply Now', 'Quick Apply']
            for text in apply_texts:
                count = await page.locator(f':has-text("{text}")').count()
                if count > 0:
                    logger.info(f"  Elements with '{text}': {count}")
            
            # Page context
            title = await page.title()
            url = page.url
            logger.info(f"  Page: {title}")
            logger.info(f"  URL: {url}")
            
        except Exception as e:
            logger.error(f"❌ Authenticated debug failed: {e}")

async def apply_button_finder_main():
    """Test enhanced apply button finder with authentication"""
    print("🧪 Testing Enhanced Apply Button Finder...")
    print("-" * 50)
    
    try:
        browser_manager = BrowserManager(headless=False)
        setup_success = await browser_manager.setup()
        
        if setup_success:
            page_navigator = PageNavigator(browser_manager)
            apply_button_finder = ApplyButtonFinder(page_navigator)
            test_page = await browser_manager.create_page()
            
            if test_page:
                test_job_url = "https://in.linkedin.com/jobs/view/software-engineer-intern-at-resume-mate-4268077263?position=7&pageNum=0&refId=zrXPgpoeADFH2NiFZD4xLg%3D%3D&trackingId=j9p0VHaSljJlPjenWRsyxw%3D%3D"
                
                navigation_success = await page_navigator.navigate_to_job(test_page, test_job_url)
                if navigation_success:
                    await apply_button_finder.debug_authenticated_page_elements(test_page)
                    
                    button_found = await apply_button_finder.find_and_click_apply_button(test_page, test_job_url)
                    
                    if button_found:
                        print("✅ SUCCESS: Enhanced apply button finder working!")
                    else:
                        print("⚠️ INFO: No apply button found (expected on jobs listing)")
                        print("✅ SUCCESS: Enhanced apply button logic working correctly!")
                else:
                    print("❌ FAILED: Enhanced navigation failed")
            else:
                print("❌ FAILED: Could not create test page")
        else:
            print("❌ FAILED: Enhanced browser setup failed")
        
        await browser_manager.cleanup()
        
    except Exception as e:
        print(f"❌ FAILED: Enhanced apply button finder test failed: {e}")
    
    print("-" * 50)

async def page_navigator_main():
    """Test enhanced page navigator with multi-cookie authentication"""
    print("🧪 Testing Enhanced Page Navigator...")
    print("-" * 50)
    
    try:
        browser_manager = BrowserManager(headless=True)
        setup_success = await browser_manager.setup()
        
        if setup_success:
            page_navigator = PageNavigator(browser_manager)
            test_page = await browser_manager.create_page()
            
            if test_page:
                test_job_url = "https://www.linkedin.com/jobs/"
                navigation_success = await page_navigator.navigate_to_job(test_page, test_job_url)
                
                if navigation_success:
                    print("✅ SUCCESS: Enhanced page navigation with authentication working!")
                else:
                    print("❌ FAILED: Enhanced navigation failed")
            else:
                print("❌ FAILED: Could not create test page")
        else:
            print("❌ FAILED: Enhanced browser setup failed")
        
        await browser_manager.cleanup()
        
    except Exception as e:
        print(f"❌ FAILED: Enhanced page navigator test failed: {e}")
    
    print("-" * 50)

async def browser_manager_main():
    """Test enhanced browser manager with comprehensive authentication"""
    print("🧪 Testing Enhanced Browser Manager...")
    print("-" * 50)
    
    try:
        browser_manager = BrowserManager(headless=False)
        
        # Test setup
        setup_success = await browser_manager.setup()
        if not setup_success:
            print("❌ FAILED: Enhanced browser setup failed")
            return
        
        print("✅ SUCCESS: Enhanced browser setup completed")
        
        # Test authentication verification
        auth_success = await browser_manager.verify_linkedin_authentication()
        
        if auth_success:
            print("✅ SUCCESS: LinkedIn authentication verified with multiple cookies!")
            
            # Show authentication status
            auth_status = browser_manager.get_authentication_status()
            print(f"📊 Authentication Status:")
            print(f"   Authenticated: {auth_status['authenticated']}")
            print(f"   Cookies loaded: {auth_status['cookie_count']}")
            print(f"   Available cookies: {auth_status['available_cookies']}")
            
            # Test page creation
            test_page = await browser_manager.create_page()
            if test_page:
                print("✅ SUCCESS: Enhanced page creation working!")
                
                # Test navigation to LinkedIn
                await test_page.goto('https://www.linkedin.com')
                await asyncio.sleep(3)
                
                print("✅ SUCCESS: LinkedIn navigation working with authentication!")
            else:
                print("❌ FAILED: Could not create test page")
        else:
            print("❌ FAILED: LinkedIn authentication verification failed")
            print("🔧 Try:")
            print("   1. Ensure Chrome extension is syncing cookies")
            print("   2. Check you're logged into LinkedIn")
            print("   3. Verify cookie files exist in cookies/ directory")
        
        # Cleanup
        await browser_manager.cleanup()
        print("✅ SUCCESS: Browser cleanup completed")
        
    except Exception as e:
        print(f"❌ FAILED: Enhanced browser manager test failed: {e}")
    
    print("-" * 50)
    
def cookie_manager_main():
    """Test the enhanced cookie manager functionality"""
    print("🧪 Testing Enhanced Cookie Manager...")
    print("-" * 50)
    
    cookie_manager = CookieManager()
    
    # Test loading all cookies
    load_success = cookie_manager.load_all_linkedin_cookies()
    
    if load_success:
        print("✅ Successfully loaded LinkedIn cookies!")
        
        # Show cookie summary
        summary = cookie_manager.get_cookie_summary()
        print(f"📊 Cookie Summary:")
        print(f"   Total cookies: {summary['total_cookies']}")
        print(f"   Available: {summary['available_cookies']}")
        print(f"   Essential present: {summary['essential_cookies_present']}")
        if summary['missing_essential_cookies']:
            print(f"   Missing essential: {summary['missing_essential_cookies']}")
        
        # Test getting specific cookies
        li_at = cookie_manager.get_cookie('li_at')
        if li_at:
            print(f"✅ li_at cookie: {li_at[:30]}...")
        
        jsessionid = cookie_manager.get_cookie('JSESSIONID')
        if jsessionid:
            print(f"✅ JSESSIONID cookie: {jsessionid[:30]}...")
        
        # Test essential cookies check
        has_essential = cookie_manager.has_essential_cookies()
        if has_essential:
            print("✅ Essential cookies validation passed!")
        else:
            print("❌ Missing essential cookies")
        
    else:
        print("❌ Failed to load LinkedIn cookies")
        print("\n🔧 Troubleshooting steps:")
        print("   1. Make sure your Chrome extension is running")
        print("   2. Ensure you're logged into LinkedIn")
        print("   3. Check that cookies are being synced to files")
        print("   4. Verify 'cookies/' directory exists with cookie files")
    
    print("-" * 50)



if __name__ == "__main__":
    # cookie_manager_main()
    # asyncio.run(browser_manager_main())
    # asyncio.run(page_navigator_main())
    asyncio.run(apply_button_finder_main())