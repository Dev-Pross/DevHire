import asyncio
import uuid
from pathlib import Path
import sys
import tempfile
import os
from datetime import datetime
import time
import re
import aiohttp
from bs4 import BeautifulSoup

from config import LINKEDIN_CONTEXT_OPTIONS
from database.linkedin_context import save_linkedin_context, get_linkedin_context, clear_linkedin_context

from playwright.async_api import async_playwright
# from concurrent.futures import ThreadPoolExecutor
import json

from google import genai
from google.genai import types

# from urllib.parse import urlparse
from config import GOOGLE_API, LINKEDIN_ID, LINKEDIN_PASSWORD

HEADLESS = os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() != "false"

# Color constants for enhanced debugging
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

# Configuration
PLATFORMS = {
    "linkedin": {
        "url_template": "https://www.linkedin.com/jobs/search/?f_AL=true&f_E=1%2C2&f_JT=F&f_TPR=r86400&f_WT=1%2C2%2C3&keywords={role}&location=India&origin=JOB_SEARCH_PAGE_JOB_FILTER&sortBy=DD",
        "base_url": "https://www.linkedin.com",
        "login_url": "https://www.linkedin.com/login"
    },
}

JOB_TITLES = [
    "Full Stack Developer", "Frontend Developer", "Backend Developer",
    "Software Engineer", "React Developer"
]

FILTERING_KEYWORDS = [
    "React.js", "JavaScript", "Node.js", "Express.js", "HTML", "CSS",
    "Bootstrap", "Java", "MySQL", "SQLite", "MongoDB", "JWT Token",
    "REST API", "Android Development", "Linux", "GitHub", "Git",
    "AI", "Machine Learning", "Data Structures", "Algorithms",
    "Python", "Spring Boot", "TypeScript"
]

PROCESSED_JOB_URLS = set()
LOGGED_IN_CONTEXT = None
# MODEL_NAME="gemini-2.5-flash"
model_2 = "gemini-3-flash-preview"
model_3 = 'gemini-2.5-flash-lite' # gemini-2.5-flash-lite gemini-2.5-flash-preview-09-2025
model_1 = 'gemini-2.5-flash'
model_4 = 'gemini-robotics-er-1.5-preview'

MODELS = [model_1, model_2, model_3, model_4]

MAX_PAGES = 3


def normalize_job_url(url: str) -> str:
    return (url or "").split('?')[0].strip()


def normalize_text(value) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())


def has_meaningful_value(value) -> bool:
    normalized = normalize_text(value).lower()
    if not normalized:
        return False

    placeholders = {
        "not specified",
        "not available",
        "unknown",
        "n/a",
        "none",
        "null",
        "title not extracted",
        "company not extracted",
        "id not extracted",
    }
    return normalized not in placeholders


def extract_job_id_from_url(url: str) -> str:
    match = re.search(r"/jobs/view/(\d+)", url or "")
    return match.group(1) if match else "ID not extracted"


def is_valid_raw_jobs_payload(payload) -> bool:
    if not isinstance(payload, dict) or not payload:
        return False

    sample_value = next(iter(payload.values()))
    return isinstance(sample_value, (str, dict))

# ---------------------------------------------------------------------------
# 1. ENHANCED LOGIN FUNCTIONALITY
# ---------------------------------------------------------------------------


async def debug_capture_page(page, step_name, job_title=""):
    """Capture screenshot and HTML at any step for debugging"""
    try:
        timestamp = datetime.now().strftime("%H%M%S")
        temp_dir = tempfile.gettempdir()
        
        safe_title = job_title.replace(' ', '_').replace('/', '_') if job_title else ""
        prefix = f"debug_{step_name}"
        if safe_title:
            prefix += f"_{safe_title}"
        
        png_path = os.path.join(temp_dir, f"{prefix}_{timestamp}.png")
        html_path = os.path.join(temp_dir, f"{prefix}_{timestamp}.html")
        
        await page.screenshot(path=png_path, full_page=True)
        html = await page.content()
        
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        
        print(f"🔍 DEBUG: Captured {step_name} - PNG: {os.path.basename(png_path)}")
        print(f"📄 DEBUG: HTML snippet: {html[:300]}...")
        
        return {"png_path": png_path, "html_path": html_path}
    except Exception as e:
        print(f"❌ DEBUG capture failed for {step_name}: {e}")
        return None



async def linkedin_login(browser, email_val, password_val):
    """Login to LinkedIn with FORCED 50% zoom"""
    global LOGGED_IN_CONTEXT
    
    print("🔐 Starting LinkedIn login...")
    
    context = await browser.new_context(**LINKEDIN_CONTEXT_OPTIONS)
    
    page = await context.new_page()
    
    try:
        await page.goto(PLATFORMS["linkedin"]["login_url"])
        await asyncio.sleep(2)

        await debug_capture_page(page, "01_login_page_loaded")
        
        # FORCE zoom that LinkedIn cannot override
        # await apply_forced_zoom(page)
        # await asyncio.sleep(3)  # Wait for zoom to apply
        
        print("✅ FORCED 50% zoom applied - LinkedIn should now be zoomed out")
        
        print("📧 Entering email...")
        email_input = await page.wait_for_selector('input[type="email"]:visible', timeout=10000)
        await email_input.fill(email_val)
        
        print("🔑 Entering password...")
        password_input = await page.wait_for_selector('input[type="password"]:visible', timeout=5000)
        await password_input.fill(password_val)
        
        await debug_capture_page(page, "02_credentials_filled")

        print("🚀 Clicking login button...")
        login_button = await page.wait_for_selector('button:has-text("Sign in"):not(:has-text("Apple")):not(:has-text("Microsoft")):visible, button:has-text("Log in"):not(:has-text("Apple")):not(:has-text("Microsoft")):visible, button[type="submit"]:visible', timeout=5000)
        await login_button.click()
        await asyncio.sleep(5)
        
        current_url = page.url
        if "feed" in current_url:
            print("✅ Login successful with FORCED zoom!")

        if "challenge" in current_url:
            print(f"{Colors.RED}❌ Login challenge detected! Please resolve manually.{Colors.END}")
            await debug_capture_page(page, "03_challenge_error")
            await asyncio.sleep(10)
            return
        
        if "feed" not in current_url:
             print(f"{Colors.RED}❌ Login Failed!{Colors.END}")
             await debug_capture_page(page, "03_Login_error")
             await asyncio.sleep(10)
             return
        
        
        await debug_capture_page(page, "03_after_login_click")

        # LOGGED_IN_CONTEXT = context

        await page.close()
        return context
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        await page.close()
        await context.close()
        return None

async def ensure_logged_in(browser, user_id, linkedin_email=None, linkedin_password=None):
    """Ensure we have a valid logged-in context"""
    global LOGGED_IN_CONTEXT
    
    db_context = get_linkedin_context(user_id)
    # print("context from db", db_context)
    print("HireHawk user", user_id)
    if db_context:
        print(f"♻️ FOUND STORAGE STATE IN DB!")
        print(f"✅ Creating new context with current browser using saved state!")
        
        # Extract fingerprint before passing to Playwright
        fingerprint = db_context.pop("fingerprint", {})
        
        context_kwargs = LINKEDIN_CONTEXT_OPTIONS.copy()
        if fingerprint:
            print("Applying user browser fingerprint to context...")
            if fingerprint.get("userAgent"):
                context_kwargs["user_agent"] = fingerprint["userAgent"]
            if fingerprint.get("timezone"):
                context_kwargs["timezone_id"] = fingerprint["timezone"]
            if fingerprint.get("language"):
                context_kwargs["locale"] = fingerprint["language"]
            if fingerprint.get("viewport"):
                context_kwargs["viewport"] = fingerprint["viewport"]
            if fingerprint.get("screen"):
                context_kwargs["screen"] = fingerprint["screen"]

        # Create NEW context with the CURRENT browser using saved storage_state
        try:
            context = await browser.new_context(
                storage_state=db_context,
                **context_kwargs
            )
            print(f"✅ New context created successfully with saved state!")
            LOGGED_IN_CONTEXT = context
            return context
        except Exception as e:
            print(f"⚠️ Failed to restore context: {e}, logging in again...")
            # clear_linkedin_context(user_id)
    
    # No saved state, perform login
    if not linkedin_email or not linkedin_password:
        raise Exception("MISSING CREDENTIALS: No saved session found and no LinkedIn credentials provided in the payload.")

    print(f"🔐 No storage state in DB, logging in using provided credentials...")

    context = await linkedin_login(browser, linkedin_email, linkedin_password)
    
    if context:
        # ✅ SAVE STORAGE STATE (not the context itself!)
        storage_state = await context.storage_state()

        save_linkedin_context(user_id,storage_state)
        print(f"💾 Storage state saved to DB!")
        LOGGED_IN_CONTEXT = context
    return context

# ---------------------------------------------------------------------------
# 2. FIXED PAGINATION - WAIT FOR JOBS AFTER EACH PAGE CLICK
# ---------------------------------------------------------------------------

async def load_all_available_jobs_fixed(page):
    """FIXED: Proper pagination with page-by-page job loading - returns unique job entries."""
    try:
        print("🔄 Starting FIXED pagination job loading...")
        
        unique_job_map = {}
        max_pages = MAX_PAGES
        
        for page_num in range(max_pages):
            print(f"📄 Processing page {page_num + 1}/{max_pages}")
            
            # Collect job entries from current page
            current_page_jobs = await collect_jobs_from_current_page(page)
            
            # Add new unique jobs
            new_jobs_count = 0
            for job in current_page_jobs:
                raw_url = job.get("url", "") if isinstance(job, dict) else ""
                clean_url = normalize_job_url(raw_url)
                if clean_url and clean_url not in unique_job_map:
                    unique_job_map[clean_url] = {
                        "url": clean_url,
                        "card_title": normalize_text(job.get("card_title", "")),
                    }
                    new_jobs_count += 1
            
            print(f"✅ Page {page_num + 1}: Added {new_jobs_count} new jobs (Total: {len(unique_job_map)})")
            
            # Try to navigate to next page
            next_clicked = await click_next_page_and_wait(page)
            if not next_clicked:
                print(f"🛑 No next page available, stopping at page {page_num + 1}")
                break
        
        print(f"✅ FIXED pagination complete: {len(unique_job_map)} unique jobs from multiple pages")
        return list(unique_job_map.values())
        
    except Exception as e:
        print(f"❌ FIXED pagination error: {e}")
        return []

async def scroll_current_page(page):
    """Fixed scrolling that actually moves the content"""
    try:
        print("🔄 Starting enhanced scrolling with multiple selectors...")
        
        # Extended list of possible LinkedIn job list selectors
        job_list_selectors = [
            '.scaffold-layout__content ul',
            '[data-view-name*="jobs-search"]',
            '.scaffold-layout__main ul',
            '.jobs-search-results-list',
            'ul[data-view-name="jobs-search-results-list"]',
            '.jobs-search-results__list',
            '.jobs-search-two-pane__results ul',
            '.jobs-search-results',
            'ul[role="list"]',
            'li[data-occludable-job-id]'
            '.display-flex .job-card-container',
            '.display-flex .job-card-container .relative .job-card-list'
        ]
        
        job_list_element = None
        working_selector = None
        
        # Find working selector
        for selector in job_list_selectors:
            try:
                print(f"🔍 Trying selector: {selector}")
                job_list_element = await page.wait_for_selector(selector, timeout=2000)
                if job_list_element and await job_list_element.is_visible():
                    working_selector = selector
                    print(f"✅ Found working selector: {selector}")
                    break
            except:
                continue
        
        if working_selector:

            await debug_capture_page(page, "07_container_found")
            # Enhanced scrolling with multiple methods
            for i in range(2):
                scroll_result = await page.evaluate(f'''
                    () => {{
                        const jobList = document.querySelector('{working_selector}');
                        if (jobList) {{
                            const beforeScroll = jobList.scrollTop;
                            
                            // Method 1: Standard scrollTop
                            jobList.scrollTop = jobList.scrollHeight;
                            
                            // Method 2: ScrollBy method
                            jobList.scrollBy(0, 1000);
                            setTimeout(() => {{
                                jobList.scrollBy(0, 500);
                            }}, 1000);
                            
                            // Method 3: Force scroll on parent containers
                            let parent = jobList.parentElement;
                            while (parent && parent !== document.body) {{
                                if (parent.scrollHeight > parent.clientHeight) {{
                                    parent.scrollTop = parent.scrollHeight;
                                    parent.scrollBy(0, 500);
                                    setTimeout(() => {{
                                        jobList.scrollBy(0, 500);
                                    }}, 1000);
                                }}
                                parent = parent.parentElement;
                            }}
                            
                            // Method 4: Scroll the main content area
                            const mainContent = document.querySelector('.scaffold-layout__main');
                            if (mainContent) {{
                                mainContent.scrollTop = mainContent.scrollHeight;
                            }}
                            
                            // Method 5: Page-level scroll as backup
                            window.scrollBy(0, 800);

                            
                            const afterScroll = Math.max(
                                jobList.scrollTop, 
                                window.pageYOffset,
                                document.documentElement.scrollTop
                            );
                            
                            return {{
                                scrolled: afterScroll > beforeScroll,
                                scrollTop: afterScroll,
                                scrollHeight: jobList.scrollHeight,
                                clientHeight: jobList.clientHeight,
                                canScroll: jobList.scrollHeight > jobList.clientHeight,
                                windowScroll: window.pageYOffset
                            }};
                        }}
                        return {{scrolled: false}};
                    }}
                ''')
                
                print(f"📜 Scroll {i+1}/2: Top={scroll_result.get('scrollTop', 0)}, Window={scroll_result.get('windowScroll', 0)}, CanScroll={scroll_result.get('canScroll', False)}")
                
                # Additional Playwright-native scrolling
                try:
                    if job_list_element:
                        await job_list_element.scroll_into_view_if_needed()
                        await page.mouse.wheel(0, 500)# Mouse wheel scroll
                        
                except:
                    pass
                
                await asyncio.sleep(0.5)  # Longer wait for content loading
        else:
            await debug_capture_page(page, "07_no_container_found")
            # Fallback to page scrolling
            print("⚠️ No job list container found, using page scroll")
            for i in range(3):
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await page.mouse.wheel(0, 500)
                print(f"📜 Page scroll {i+1}/3")
                await asyncio.sleep(0.5)
        
        print("✅ Enhanced scrolling completed")
        
        # Force additional job loading
        await page.evaluate('window.dispatchEvent(new Event("scroll"))')
        await debug_capture_page(page, "07_no_container_found")
        await asyncio.sleep(0.5)
        
    except Exception as e:
        print(f"❌ Enhanced scroll error: {e}")


async def force_layout_fix(page):
    """Force proper layout after zoom"""
    await page.evaluate('''
        () => {
            // Force layout recalculation
            document.body.offsetHeight;
            
            // Ensure job list container is properly sized
            const jobList = document.querySelector('.jobs-search-results-list');
            if (jobList) {
                jobList.style.height = '100%';
                jobList.style.overflowY = 'auto';
                
                // Force scroll container recognition
                jobList.scrollTop = 1;
                jobList.scrollTop = 0;
            }
            
            console.log('✅ Layout forced');
        }
    ''')


async def collect_jobs_from_current_page(page):
    """Collect all unique job URLs with lightweight card metadata from current page."""

    # Set standard viewport: 1920x1080
    await page.set_viewport_size({'width': 2562, 'height': 2000})
    
    # Scale content to 25% (shows 4x more content in same space)
    try:
        await page.evaluate('() => { document.body.style.zoom = "0.25"; }')
    except Exception as e:
        print(f"Zooming failed: {e}")
        
    # Scroll dynamically to force LinkedIn to fetch remaining lazy-loaded cards
    await scroll_current_page(page)
    await asyncio.sleep(1)
    
    # Extract all job URLs and card titles
    job_entries = await page.evaluate('''
        () => {
            const urlMap = new Map();
            // Find all links containing /jobs/view
            const links = document.querySelectorAll('a[href*="/jobs/view"]');
            
            links.forEach(link => {
                const href = link.getAttribute('href');
                if (href) {
                    // Remove query parameters
                    const cleanUrl = href.split('?')[0];

                    const card = link.closest('li') || link.closest('.job-card-container') || link.parentElement;
                    const titleNode =
                        card?.querySelector('.job-card-list__title') ||
                        card?.querySelector('.job-card-container__link') ||
                        card?.querySelector('strong') ||
                        link;

                    const cardTitle = (titleNode?.textContent || '').trim();
                    if (!urlMap.has(cleanUrl)) {
                        urlMap.set(cleanUrl, {
                            url: cleanUrl,
                            card_title: cardTitle
                        });
                    }
                }
            });
            
            return Array.from(urlMap.values());
        }
    ''')
    
    print(f"✅ Found {len(job_entries)} unique job URLs at 4x visibility in 1920x1080")
    return job_entries

async def click_next_page_and_wait(page):
    """FIXED: Click next page and wait for new jobs to load"""
    print("moving to next page, if available")
    
    # 1. First ensure 25% zoom to expose all lazy-loaded job cards without scroll bounding
    try:
        await page.evaluate("document.body.style.zoom='25%'")
        # Give a moment for the new zoom scale to take effect
        await asyncio.sleep(1)
    except Exception as e:
        print(f"Zoom out failed: {e}")

    try:
       
        
        # Priority selector based on your HTML: aria-label="View next page"
        next_selectors = [
            'button[aria-label="View next page"]',
            'button.jobs-search-pagination__button--next',
            'button:has-text("Next")',
            'button[aria-label*="next" i]',  # Case-insensitive partial match
            'button.artdeco-button.jobs-search-pagination__button',
            '.jobs-search-pagination__button--next',
        ]
        
        for selector in next_selectors:
            try:
                print(f"🔍 Trying selector: {selector}")
                
                # Don't wait, just check if exists
                buttons = await page.locator(selector).all()
                
                if len(buttons) == 0:
                    print(f"  ❌ No buttons found with selector: {selector}")
                    continue
                
                print(f"  ✅ Found {len(buttons)} button(s) with selector: {selector}")

                for idx, btn in enumerate(buttons):
                    try:
                        is_visible = await btn.is_visible()
                        is_enabled = await btn.is_enabled()
                        
                        if not is_visible or not is_enabled:
                            print(f"  ⚠️ Button {idx+1}: visible={is_visible}, enabled={is_enabled}")
                            continue

                        text = (await btn.text_content() or "").strip()
                        print(f"  ✅ Button {idx+1}: visible, enabled, text='{text}'")

                        # Get current job count before clicking
                        current_jobs = await page.query_selector_all('a[href*="/jobs/view"]')
                        prev_count = len(current_jobs)

                        # Multiple click strategies
                        click_success = False
                        
                        # Strategy 1: Standard click
                        try:
                            await btn.scroll_into_view_if_needed()
                            await asyncio.sleep(0.5)
                            await btn.click(timeout=5000)
                            click_success = True
                            print(f"  🎯 Clicked next button successfully")
                        except Exception as e1:
                            print(f"  ⚠️ Standard click failed: {e1}")
                        
                        # Strategy 2: JavaScript click
                        if not click_success:
                            try:
                                await page.evaluate("(element) => element.click()", btn)
                                click_success = True
                                print(f"  🎯 Clicked with JavaScript")
                            except Exception as e2:
                                print(f"  ⚠️ JS click failed: {e2}")
                        
                        # Strategy 3: Force click
                        if not click_success:
                            try:
                                await btn.click(force=True, timeout=5000)
                                click_success = True
                                print(f"  🎯 Clicked with force=True")
                            except Exception as e3:
                                print(f"  ⚠️ Force click failed: {e3}")

                        if click_success:
                            # Wait for new page to load
                            await wait_for_page_change(page, prev_count)
                            return True
                        else:
                            print(f"  ❌ All click strategies failed for button {idx+1}")
                            continue

                    except Exception as e:
                        print(f"  ❌ Error with button {idx+1}: {e}")
                        continue
                        
            except Exception as e:
                print(f"  ❌ Selector exception: {e}")
                continue
        
        print("🛑 No clickable next button found with any selector")
        return False
        
    except Exception as e:
        print(f"❌ Next page click error: {e}")
        return False

async def wait_for_page_change(page, prev_job_count):
    """Wait for page to change and new jobs to load"""
    print("⏳ Waiting for next page to load...")
    
    # Wait for page transition
    await asyncio.sleep(2)
    # Ensure viewport stays maximized for next page card exposure
    await page.evaluate("document.body.style.zoom='25%'")
    
    # Wait for job count to change (indicating new page loaded)
    for attempt in range(15):  # Max 7.5 seconds wait
        current_jobs = await page.query_selector_all('a[href*="/jobs/view"]')
        current_count = len(current_jobs)
        
        if current_count != prev_job_count:
            print(f"✅ Page changed! Jobs: {prev_job_count} → {current_count}")
            await asyncio.sleep(1)  # Extra wait for full load
            return True
        
        await asyncio.sleep(0.5)
    
    print("⚠️ Page may not have changed, continuing...")
    return True


def extract_first_text(soup: BeautifulSoup, selectors: list[str]) -> str:
    for selector in selectors:
        node = soup.select_one(selector)
        if node:
            value = normalize_text(node.get_text(" ", strip=True))
            if value:
                return value
    return ""


def detect_job_type_from_text(page_text: str) -> str:
    lower = (page_text or "").lower()
    if "hybrid" in lower:
        return "Hybrid"
    if "remote" in lower:
        return "Remote"
    if "on-site" in lower or "onsite" in lower or "on site" in lower:
        return "On-site"
    return ""


def extract_job_metadata_from_html(html_content: str, fallback_title: str = "") -> dict:
    soup = BeautifulSoup(html_content, 'lxml')

    description = ""
    for selector in [
        'div.show-more-less-html__markup',
        'section.show-more-less-html',
        'div.jobs-description__content',
        '#job-details',
    ]:
        node = soup.select_one(selector)
        if node:
            description = normalize_text(node.get_text(" ", strip=True))
            if description:
                break

    title = extract_first_text(soup, [
        'h1.t-24.t-bold.inline',
        'h1.top-card-layout__title',
        '.job-details-jobs-unified-top-card__job-title h1',
        'h1',
    ])
    if not title:
        title = normalize_text(fallback_title)

    company_name = extract_first_text(soup, [
        'a.topcard__org-name-link',
        '.topcard__flavor-row a',
        '.job-details-jobs-unified-top-card__company-name a',
        '.job-details-jobs-unified-top-card__company-name',
    ])

    location = extract_first_text(soup, [
        'span.topcard__flavor.topcard__flavor--bullet',
        '.job-details-jobs-unified-top-card__bullet',
        '.jobs-unified-top-card__bullet',
    ])

    posted_at = extract_first_text(soup, [
        'span.posted-time-ago__text',
        '.jobs-unified-top-card__posted-date',
        'span.tvm__text.tvm__text--low-emphasis',
    ])

    criteria_type = ""
    for item in soup.select('.description__job-criteria-item, .jobs-unified-top-card__job-insight, .job-details-jobs-unified-top-card__job-insight'):
        text = normalize_text(item.get_text(" ", strip=True))
        if not text:
            continue

        if "employment type" in text.lower():
            criteria_type = normalize_text(text.replace("Employment type", "").strip(" :|-"))
            if criteria_type:
                break

    page_text = normalize_text(soup.get_text(" ", strip=True))
    job_type = criteria_type or detect_job_type_from_text(page_text)

    return {
        "job_description": description,
        "title": title,
        "company_name": company_name,
        "location": location,
        "posted_at": posted_at,
        "job_type": job_type,
    }


async def extract_job_description_fixed(session: aiohttp.ClientSession, url, fallback_title="", max_retries=3):
    """
    Fetches the HTML of a URL and then parses it to extract
    the text content of the element with id='job-details'.
    Includes retry logic for failed requests.
    """
    print(f"🚀 Fetching: {url}")
    
    headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
    
    await asyncio.sleep(1.5)
    
    for attempt in range(max_retries):
        try:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    html_content = await response.text()
                    print(f"   ✅ HTML fetched successfully (attempt {attempt + 1})")

                    print("   🥣 Parsing HTML with Beautiful Soup...")
                    metadata = extract_job_metadata_from_html(html_content, fallback_title=fallback_title)

                    if metadata.get("job_description"):
                        print("   ✅ Extracted metadata and description successfully!")
                        return metadata

                    print(f"   ⚠️ Job description element not found (attempt {attempt + 1})")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2)  # Wait before retry
                        continue
                    return "Failed: Could not find the job description element in the HTML."
                else:
                    print(f"   ⚠️ HTTP {response.status} (attempt {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2)  # Wait before retry
                        continue
                    return f"Failed: HTTP status {response.status}"
                    
        except asyncio.TimeoutError:
            print(f"   ⏱️ Timeout (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                await asyncio.sleep(3)  # Longer wait after timeout
                continue
            return "Failed: Request timeout after retries"
            
        except Exception as e:
            print(f"   ❌ Error (attempt {attempt + 1}/{max_retries}): {str(e)[:100]}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2)
                continue
            return f"Failed: {str(e)[:100]}"
    
    return "Failed: Max retries exceeded"



# ---------------------------------------------------------------------------
# 4. OPTIMIZED JOB PROCESSING - INCREASED SPEED
# ---------------------------------------------------------------------------


async def scrape_platform_speed_optimized(context, platform_name, config, job_title, user_id):
    """SPEED OPTIMIZED: URL-deduped collection with raw metadata capture."""
    global PROCESSED_JOB_URLS
    
    page = await context.new_page()
    # page.set_viewport_size({'width': 2560, 'height': 2000})
    await page.evaluate('() => { document.body.style.zoom = "0.25"; }')
    # Optimized timeouts for speed
    page.set_default_navigation_timeout(20000)
    page.set_default_timeout(15000)
    
    job_dict = {}
    
    try:
        url = config["url_template"].format(role=job_title.replace(" ", "%20").lower())
        print(f"🔍 {Colors.BOLD}SPEED-OPTIMIZED search: '{job_title}'{Colors.END}")
        
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        print("✅ Navigation complete")
        
        # await apply_forced_zoom(page)
        # await asyncio.sleep(1)
        await debug_capture_page(page, "05_search_results", job_title)

        # Force layout fix
        await force_layout_fix(page)
        await asyncio.sleep(1)
        
        job_cards = await load_all_available_jobs_fixed(page)
        
        await debug_capture_page(page, "06_after_job_loading", job_title)

        if not job_cards:
            print(f"❌ No jobs found for '{job_title}'")
            return {}
        
        print(f"📊 Processing {len(job_cards)} unique job URLs")

        valid_job_links = []
        duplicate_count = 0

        for i, card in enumerate(job_cards, 1):
            try:
                raw_url = card.get("url", "") if isinstance(card, dict) else ""
                card_title = normalize_text(card.get("card_title", "")) if isinstance(card, dict) else ""

                full_url = raw_url if raw_url.startswith('http') else config["base_url"] + raw_url
                clean_url = normalize_job_url(full_url)
                if not clean_url:
                    continue

                if clean_url in PROCESSED_JOB_URLS:
                    duplicate_count += 1
                    print(f"   🔄 Job {i}: Duplicate URL, skipping")
                    continue

                PROCESSED_JOB_URLS.add(clean_url)
                valid_job_links.append({
                    "url": clean_url,
                    "card_title": card_title,
                })
                print(f"   ✅ Job {i}: Added to processing queue")

            except Exception as e:
                print(f"   ❌ Job {i}: Processing error: {e}")
                continue
        
        # Filtering summary
        print(f"\n📊 FILTERING SUMMARY:")
        print(f"   📁 Total URLs collected: {len(job_cards)}")
        print(f"   ✅ Valid jobs: {len(valid_job_links)}")
        print(f"   🔄 Duplicates skipped: {duplicate_count}")
        
        print(f"✅ {len(valid_job_links)} jobs ready for OPTIMIZED processing")
        
        # Continue with job processing...
        # results=[]
        if valid_job_links:
            print(f"✅ {len(valid_job_links)} jobs ready for OPTIMIZED processing with aiohttp...")
            
            # cookies = await context.cookies()
            
            # # Filter out cookies with invalid characters for aiohttp
            # valid_cookies = []
            # for cookie in cookies:
            #     cookie_name = cookie['name']
            #     # Skip cookies with brackets or other special chars that aiohttp doesn't like
            #     if '[' not in cookie_name and ']' not in cookie_name:
            #         valid_cookies.append(cookie)
            #     else:
            #         print(f"   ⚠️ Skipping invalid cookie: {cookie_name}")
            
            # print(f"   ✅ Using {len(valid_cookies)}/{len(cookies)} valid cookies for authentication")
            
            # Use aiohttp to fetch descriptions in controlled batches
            connector = aiohttp.TCPConnector(limit=3)  # Only 3 concurrent connections
            async with aiohttp.ClientSession(connector=connector) as session:
                # Add valid cookies to session
                # for cookie in valid_cookies:
                #     try:
                #         session.cookie_jar.update_cookies(
                #             {cookie['name']: cookie['value']},
                #             response_url=aiohttp.client.URL(config["base_url"])
                #         )
                #     except Exception as e:
                #         print(f"   ⚠️ Could not add cookie {cookie['name']}: {e}")
    
                # Process in small batches with delays to avoid rate limiting
                results = []
                batch_size = 20  # Only 5 jobs at a time
                
                for i in range(0, len(valid_job_links), batch_size):
                    batch_urls = valid_job_links[i:i + batch_size]
                    batch_num = (i // batch_size) + 1
                    total_batches = (len(valid_job_links) + batch_size - 1) // batch_size
                    
                    print(f"   📦 Processing batch {batch_num}/{total_batches} ({len(batch_urls)} jobs)...")
                    
                    batch_tasks = [
                        extract_job_description_fixed(
                            session,
                            job_entry.get("url", ""),
                            fallback_title=job_entry.get("card_title", ""),
                        )
                        for job_entry in batch_urls
                    ]
                    
                    batch_results = await asyncio.gather(*batch_tasks)
                    results.extend(batch_results)
                    
                    # Add delay between batches (except for the last batch)
                    if i + batch_size < len(valid_job_links):
                        delay = 2  # 5 second delay between batches
                        print(f"   ⏳ Waiting {delay}s before next batch to avoid rate limiting...")
                        await asyncio.sleep(delay)

            # with open(f"results_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}", "w", encoding="utf-8") as f:
            #     json.dump(results, f, indent=2, ensure_ascii=False)
            

            processed_count = 0
            failed_count = 0
            failed_urls = []
            
            # Pair job metadata with fetched raw payload
            for job_entry, raw_payload in zip(valid_job_links, results):
                url = job_entry.get("url", "")
                fallback_title = job_entry.get("card_title", "")

                if isinstance(raw_payload, dict) and raw_payload.get("job_description"):
                    job_dict[url] = {
                        "job_url": url,
                        "job_id": str(uuid.uuid4()),
                        "job_description": raw_payload.get("job_description", ""),
                        "title": raw_payload.get("title") or fallback_title,
                        "company_name": raw_payload.get("company_name", ""),
                        "location": raw_payload.get("location", ""),
                        "posted_at": raw_payload.get("posted_at", ""),
                        "job_type": raw_payload.get("job_type", ""),
                        "source": "linkedin",
                    }
                    processed_count += 1
                else:
                    failed_count += 1
                    failed_urls.append(url)
                    reason = raw_payload[:50] if isinstance(raw_payload, str) else "No response"
                    print(f"   ❌ Failed to fetch: {url[:80]}... - Reason: {reason}")

            print(f"\n📊 EXTRACTION SUMMARY:")
            print(f"   ✅ Successfully processed: {processed_count}/{len(valid_job_links)}")
            print(f"   ❌ Failed: {failed_count}/{len(valid_job_links)}")
            # Remove all failed URLs from processed set and valid list
            failed_set = set(failed_urls)
            PROCESSED_JOB_URLS.difference_update(failed_set)
            valid_job_links = [job for job in valid_job_links if job.get("url") not in failed_set]
            if failed_urls:
                print(f"   ⚠️ Failed URLs saved for debugging")
            # with open("scrapped_jobs", "w", encoding="utf-8") as f:
            #     f.write(str(job_dict))

        return job_dict
        
    except Exception as e:
        print(f"❌ Error in speed-optimized search: {e}")
        return {}
    finally:
        if page:
            await page.close()

# ---------------------------------------------------------------------------
# 5. GEMINI API PROCESSING FUNCTIONS (OPTIMIZED)
# ---------------------------------------------------------------------------
# genai.configure(api_key=GOOGLE_API)
# model = genai.GenerativeModel("gemini-2.5-flash")
# RULES=f"""Decision rules:
# 1. A job is **relevant** only if BOTH of the following are true:
#    a. The job's responsibilities or required skills clearly match at least one
#       of the candidate's core skills (synonyms and common variations count).
#    b. The job's role/title matches or is a close variant of at least one
#       target job title (e.g., “Software Engineer (Backend)” matches “Backend Developer”).
# 2. Ignore jobs that primarily require unrelated stacks or roles, even if they
#    mention one matching keyword casually.
# 3. Consider context in the description: if a skill appears only as an optional
#    “nice to have” but the core role is unrelated, treat it as NOT relevant.
# 4. Return only the required format dont provide any other format this is mandatory"""


# def build_prompt(original: list[str], jobs: dict) -> str:
#     out = f"""You are an expert job-matching assistant.

#     Goal:
#     From the list of jobs below, identify which positions are truly relevant to the
#     candidate based on their skill set and desired job titles.

#     Candidate skills:
#     - skills: {original}     
#     \n\n{RULES}\n\n"""
#     out += f"Input format must follow:\n\n"
#     for i, (job_link, job_description) in enumerate(jobs.items(), 1):
#         out += f"=== JOB {i} ===\nURL: {job_link}\nDESCRIPTION: {job_description}\n\n"
#     out+="""Your task:
#     Return **only** the jobs that meet the rules above as a valid JSON array,
#     with each element having exactly these keys and values every pair should seperated by new line:
#     - "job_url":"job_description"


#     here is the example:
#     {
#         "https:..........":"about the job..............",
#         "https:..........":"about the job..............",
#     }
    

#     Do not include any explanation, markdown, or additional text.
#     Your entire output must be a single complete valid JSON array.

#     Jobs to evaluate:
#     {json.dumps(job_batch, ensure_ascii=False)}
#     """
#     return out

# def parse_filtering(response_text, original_jobs:dict):
#     print("provided dictionary: ",original_jobs)
#     print("="*60)
#     print("responses from gemini: ",response_text)
#     print("="*60)
    
#     try:
#         clean = response_text.strip()
#         if clean.startswith("```json"):
#             clean = clean[7:].lstrip()
#         elif clean.startswith("```"):
#             clean = clean[3:].lstrip()
#         if clean.endswith("```"):
#             clean = clean[:-3].rstrip()

#         data = json.loads(clean)
#         print("data json:", data)
#         print("="*60)
#         extracted_jobs={}
#         if not isinstance(data, list):
#             extracted_jobs = [data]
#         print("extracted jobs list/ dict: ",extracted_jobs)
#         # job_urls = list(original_jobs.keys())
#         extracted_jobs = {
#             url: desc 
#             for url, desc in data.items()
#         }
#                 # keep the 'relavance' field if Gemini returned it
#                 # job["relavance"] = job.get("relavance", "unknown")
#         print("extracted jobs list after parsing: ", extracted_jobs)
#         return extracted_jobs

#     except Exception as e:
#         print(f"❌ Error parsing response: {e}")
#         return []


client = genai.Client(api_key=GOOGLE_API)


def normalize_raw_job_payload(url: str, raw_payload) -> dict:
    normalized = {
        "job_url": url,
        "job_id": str(uuid.uuid4()),
        "title": "",
        "company_name": "",
        "location": "",
        "posted_at": "",
        "job_type": "",
        "job_description": "",
        "source": "linkedin",
    }

    if isinstance(raw_payload, str):
        normalized["job_description"] = normalize_text(raw_payload)
    elif isinstance(raw_payload, dict):
        # Keep the generated UUID to guarantee uniqueness
        normalized["title"] = normalize_text(raw_payload.get("title"))
        normalized["company_name"] = normalize_text(raw_payload.get("company_name"))
        normalized["location"] = normalize_text(raw_payload.get("location"))
        normalized["posted_at"] = normalize_text(raw_payload.get("posted_at"))
        normalized["job_type"] = normalize_text(raw_payload.get("job_type"))
        normalized["job_description"] = normalize_text(
            raw_payload.get("job_description") or raw_payload.get("description") or ""
        )

    return normalized


def coerce_list(value) -> list:
    return value if isinstance(value, list) else []


def merge_gemini_with_raw(raw_job: dict, llm_job) -> dict:
    llm_job = llm_job if isinstance(llm_job, dict) else {}

    merged = {
        "title": raw_job.get("title") if has_meaningful_value(raw_job.get("title")) else normalize_text(llm_job.get("title")) or "Title not extracted",
        "job_id": raw_job.get("job_id") or str(uuid.uuid4()),
        "company_name": raw_job.get("company_name") if has_meaningful_value(raw_job.get("company_name")) else normalize_text(llm_job.get("company_name")) or "Company not extracted",
        "location": raw_job.get("location") if has_meaningful_value(raw_job.get("location")) else normalize_text(llm_job.get("location")) or "Not specified",
        "experience": normalize_text(llm_job.get("experience")) or "Not specified",
        "salary": normalize_text(llm_job.get("salary")) or "Not specified",
        "key_skills": coerce_list(llm_job.get("key_skills")),
        "job_url": raw_job.get("job_url"),
        "posted_at": raw_job.get("posted_at") if has_meaningful_value(raw_job.get("posted_at")) else normalize_text(llm_job.get("posted_at")) or "Not specified",
        "job_description": raw_job.get("job_description") or "Description not available",
        "source": "linkedin",
        "relevance_score": normalize_text(llm_job.get("relevance_score")) or "unknown",
        "job_type": raw_job.get("job_type") if has_meaningful_value(raw_job.get("job_type")) else normalize_text(llm_job.get("job_type")) or "",
    }

    if not merged["key_skills"] and isinstance(raw_job.get("key_skills"), list):
        merged["key_skills"] = raw_job.get("key_skills")

    return merged


def create_bulk_prompt(jobs_dict: dict) -> str:
    system_instruction = """
You are a professional job data extractor.

For each job entry provided:
- Extract and output all the following fields exactly as named: "title", "job_id", "company_name", "location", "experience", "salary", "key_skills", "job_url", "posted_at", "job_description", "source", "relevance_score", "job_type".
- You will receive known_metadata from Playwright scraping. Treat known_metadata as source of truth.
- If a known_metadata field has a value, DO NOT overwrite it. Keep it unchanged.
- Focus on filling missing fields from job_description, especially: experience, salary, key_skills, relevance_score.
- Extract the job_id from the URL after '/jobs/view/' if missing.
- Provide output only as a pure JSON array, with no explanations.

Example:
[
  {
    "title": "Software Engineer",
    "job_id": "123456",
    "company_name": "ABC Corp",
    "location": "India",
    "experience": "2 years",
    "salary": "₹4,00,000 - ₹6,00,000",
    "key_skills": ["JavaScript", "React", "Node.js"],
    "job_url": "https://linkedin.com/jobs/view/123456",
    "posted_at": "2 days ago",
    "job_description": "...",
    "source": "linkedin",
    "relevance_score": "98%" | null
  },
  ...
]

"""

    prompt = system_instruction + f"\nProcess {len(jobs_dict)} jobs:\n"
    for idx, (url, raw_payload) in enumerate(jobs_dict.items(), 1):
        raw_job = normalize_raw_job_payload(url, raw_payload)
        safe_desc = raw_job["job_description"].replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        known_metadata = {
            "title": raw_job.get("title", ""),
            "company_name": raw_job.get("company_name", ""),
            "location": raw_job.get("location", ""),
            "posted_at": raw_job.get("posted_at", ""),
            "job_type": raw_job.get("job_type", ""),
        }
        prompt += (
            f'\n--- JOB {idx} ---\n'
            f'job_url: "{url}"\n'
            f'known_metadata: {json.dumps(known_metadata, ensure_ascii=False)}\n'
            f'job_description: "{safe_desc}"\n'
        )
    # with open(f"prompt-{time.time()}.txt", "w", encoding="utf-8") as f:
    #     f.write(prompt)
    return prompt



def create_fallback_data_from_dict(url: str, raw_payload) -> dict:
    raw_job = normalize_raw_job_payload(url, raw_payload)
    return merge_gemini_with_raw(raw_job, {})

def parse_bulk_response(response_text: str, original_jobs: dict) -> list:
    try:
        raw = response_text.strip()
        # Remove markdown code fences if present
        if raw.startswith("```json"):
            raw = raw[7:].lstrip()
        elif raw.startswith("```"):
            raw = raw[3:].lstrip()
        if raw.endswith("```"):
            raw = raw[:-3].rstrip()

        # Remove invalid control characters except \n, \r, \t
        clean = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', raw)

        # Remove C-style comments (/* ... */) if present
        clean = re.sub(r'/\*.*?\*/', '', clean, flags=re.DOTALL)

        # Remove trailing commas before ] or }
        clean = re.sub(r',\s*([}\]])', r'\1', clean)

        # Replace single quotes with double quotes (if any)
        # Only do this if there are no double quotes at all (rare, but for LLMs that use single quotes)
        if clean.count('"') == 0 and clean.count("'") > 0:
            clean = clean.replace("'", '"')

        # Try direct parsing first
        try:
            extracted_jobs = json.loads(clean)
            if not isinstance(extracted_jobs, list):
                extracted_jobs = [extracted_jobs]
        except Exception as e:
            print(f"❌ Error parsing full batch, attempting partial recovery: {e}")
            print("--- RAW OUTPUT START ---")
            print(raw[:2000])
            print("--- RAW OUTPUT END ---")
            print("--- CLEANED OUTPUT START ---")
            print(clean[:2000])
            print("--- CLEANED OUTPUT END ---")
            # Try to extract individual objects from the array
            objects = re.findall(r'\{.*?\}', clean, re.DOTALL)
            extracted_jobs = []
            for idx, obj_str in enumerate(objects):
                try:
                    job = json.loads(obj_str)
                    extracted_jobs.append(job)
                except Exception as e2:
                    print(f"   ⚠️ Skipping malformed job object {idx+1}: {e2}")
                    # fallback for this job
                    job_urls = list(original_jobs.keys())
                    if idx < len(job_urls):
                        url = job_urls[idx]
                        extracted_jobs.append(create_fallback_data_from_dict(url, original_jobs[url]))

        job_urls = list(original_jobs.keys())
        merged_jobs = []

        for i, url in enumerate(job_urls):
            raw_job = normalize_raw_job_payload(url, original_jobs[url])
            llm_job = extracted_jobs[i] if i < len(extracted_jobs) else {}
            merged_jobs.append(merge_gemini_with_raw(raw_job, llm_job))

        return merged_jobs
    except Exception as e:
        print(f"❌ Error parsing response: {e}")
        return [create_fallback_data_from_dict(url, raw_payload) for url, raw_payload in original_jobs.items()]

async def extract_single_batch(batch_dict: dict) -> list:
    prompt = create_bulk_prompt(batch_dict)
    system_instruction = """
        You are a professional job-data extraction specialist. Extract precisely the requested job titles and keywords, ensuring accuracy and consistency. Follow these rules strictly:
        - Do not invent data not present.
        - Use formal, clear, structured format.
        - Prioritize ATS keywords and recruiter-friendly titles.
        - Avoid company names or sensitive project code names.
        - Following the prompt as it is and make sure data should align properly.
        - ** Return VALID JSON OBJECT make sure in the object shouldn't be any Invalid control characters in that JSON Object ** (MANDATORY)
        """
    model_idx = 0
    choose_model = MODELS[model_idx]

    for attempt, delay in zip(range(1, 6), (0, 5, 10, 5, 10)):
        try:
            print(f"Gemini - ({choose_model}) attempt {attempt}/5")
            res = client.models.generate_content(
                model=choose_model,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.2)
            ).text
            
            if res is None:
                print(f"❌ Gemini returned None response on attempt {attempt}")
                continue
            
            # Path(f"gemini_debug_{int(time.time())}.txt").write_text(res, encoding="utf-8")
            # Path(f"gemini_debug_{int(time.time())}.json").write_text(res, encoding="utf-8")

            return parse_bulk_response(res, batch_dict)
        except Exception as e:
            # log.error("Gemini error: %s", str(e))
            # Correctly detect specific HTTP/Status codes in the error text
            if any(code in str(e) for code in ("404", "429", "503")):
                # Move to next fallback model if available
                prev_model = choose_model
                if model_idx < len(MODELS) - 1:
                    model_idx += 1
                    choose_model = MODELS[model_idx]
                    print(f"Switching model due to error ({e}) → {choose_model}")
                else:
                    print(f"Already on last fallback model ({choose_model}); will retry")
            else:
                print(f"Gemini error: {str(e)}")
            # Wait, then retry next attempt (do not break)
            time.sleep(delay)
            continue
    
    # Return fallback data if all attempts fail
    return [create_fallback_data_from_dict(url, jd) for url, jd in batch_dict.items()]


async def extract_jobs_in_batches(jobs_dict: dict, batch_size: int = 25, log_callback=None, total_jobs_so_far=0) -> list:  # Increased batch size
    all_extracted = []
    items = list(jobs_dict.items())
    total_batches = (len(items) + batch_size - 1) // batch_size
    
    if log_callback:
        log_callback({"progress": 89, "status": "analyzing", "message": "Analyzing job descriptions..."})
    
    for i in range(0, len(items), batch_size):
        batch = dict(items[i : i + batch_size])
        batch_num = (i // batch_size) + 1
        print(f"🔄 Processing batch {batch_num}/{total_batches}: {len(batch)} jobs")
        
        try:
            result = await extract_single_batch(batch)
            all_extracted.extend(result)
            print(f"✅ Batch {batch_num} completed")

            gemini_progress = 89 + int((batch_num / total_batches) * 10)
            if log_callback:
                log_callback({
                    "progress": gemini_progress,
                    "status": "batch_ready",
                    "batch_num": batch_num,
                    "total_batches": total_batches,
                    "jobs": result
                })
        except Exception as e:
            print(f"❌ Batch {batch_num} error: {e}")
            result = [create_fallback_data_from_dict(url, jd) for url, jd in batch.items()]
            all_extracted.extend(result)
            if log_callback:
                log_callback({
                    "progress": 89 + int((batch_num / total_batches) * 10),
                    "status": "batch_ready",
                    "batch_num": batch_num,
                    "total_batches": total_batches,
                    "jobs": result
                })
        
        await asyncio.sleep(0.1)  # Minimal wait between batches
    
    if log_callback:
        log_callback({"progress": 99, "status": "analyzing", "message": f"Analyzed {len(all_extracted)} jobs"})
    
    return all_extracted

# ---------------------------------------------------------------------------
# 6. MAIN EXECUTION FUNCTIONS (SPEED OPTIMIZED)
# ---------------------------------------------------------------------------

async def search_by_job_titles_speed_optimized(job_titles, platforms=None, log_callback=None, user_id=None, linkedin_email=None, linkedin_password=None):
    """SPEED OPTIMIZED: All fixes applied - faster execution"""
    global PROCESSED_JOB_URLS, LOGGED_IN_CONTEXT
    
    if platforms is None:
        platforms = list(PLATFORMS.keys())

    sanitized_titles = []
    seen_titles = set()
    for title in job_titles or []:
        clean_title = normalize_text(title)
        if not clean_title:
            continue

        key = clean_title.lower()
        if key in seen_titles:
            continue

        seen_titles.add(key)
        sanitized_titles.append(clean_title)

    if not sanitized_titles:
        sanitized_titles = JOB_TITLES
        print("⚠️ No parsed titles available. Falling back to default title set.")
    
    all_jobs = {}
    PROCESSED_JOB_URLS.clear()
    
    print(f"🚀 Starting SPEED-OPTIMIZED job extraction with ALL FIXES...")
    
    async with async_playwright() as p:
        launch_kwargs = {
            "headless": True,
            "args": [
                '--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu', '--no-zygote', '--disable-extensions', '--disable-background-networking', '--disable-renderer-backgrounding', '--no-first-run', '--mute-audio', '--metrics-recording-only'
            ]
        }
        

        browser = await p.chromium.launch(**launch_kwargs)
        
        try:
            if log_callback:
                log_callback({"progress": 12, "status": "searching", "message": "Connecting to LinkedIn..."})
            print("Performing LinkedIn login...")
            login_context = await ensure_logged_in(browser, user_id, linkedin_email, linkedin_password)
            
            if login_context is None:
                print("Failed to login to LinkedIn. Exiting...")
                if log_callback:
                    log_callback({"progress": -1, "status": "error", "message": "LinkedIn login failed. Please review credentials."})
                return {}
            
            print("Successfully logged in to LinkedIn!")
            if log_callback:
                log_callback({"progress": 15, "status": "searching", "message": "LinkedIn session ready"})
            
            for i, job_title in enumerate(sanitized_titles, 1):
                print(f"\n{'='*70}")
                print(f"⚡ SPEED-OPTIMIZED SEARCH {i}/{len(sanitized_titles)}: '{job_title}'")
                print(f"🔢 Processed URLs so far: {len(PROCESSED_JOB_URLS)}")
                print(f"{'='*70}")
                
                title_result = {}
                for platform_name in platforms:
                    try:
                        result = await scrape_platform_speed_optimized(
                            login_context, platform_name, PLATFORMS[platform_name], job_title, user_id
                        )
                        title_result.update(result)
                        all_jobs.update(result)
                        print(f"📈 Jobs from '{job_title}': {len(result)}")
                    except Exception as e:
                        print(f"❌ Error searching '{job_title}' on {platform_name}: {e}")
                    
                    await asyncio.sleep(0.5)  # Minimal wait between searches
                
                current_percent = int(15 + (i / len(sanitized_titles)) * 70)  # range 15-85
                if log_callback:
                    log_callback({"progress": current_percent, "status": "searching", "message": f"Found {len(title_result)} {job_title} jobs"})
                if not title_result:
                    print(f"⚠️ No jobs retained after filters for '{job_title}'")
                print(f"📊 '{job_title}' complete. Total unique jobs: {len(all_jobs)}")


            
        finally:
            if LOGGED_IN_CONTEXT:
                try:
                    await LOGGED_IN_CONTEXT.close()
                    print("="*70)
                    print(f"context has been closed")
                    print("="*70)
                except Exception as e:
                    print(f"⚠️ Error closing context: {e}")
            await browser.close()
    
    print(f"\n{'='*70}")
    print(f"🏆 SPEED-OPTIMIZED EXTRACTION COMPLETE!")
    print(f"📊 Total unique jobs: {len(all_jobs)}")
    print(f"🔢 Total URLs processed: {len(PROCESSED_JOB_URLS)}")
    print(f"⚡ Speed optimization: MAXIMUM")
    print(f"🔧 All fixes applied: YES")
    print(f"🔐 Authentication: ENABLED")
    print(f"{'='*70}")
    
    return all_jobs

def run_scraper_pipeline(job_id: str, job_data: dict, log_callback):
    """
    Entry point for the fetch_jobs Worker.
    Implements idempotency and recovery using `scraper_raw` status.
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(_async_scraper_pipeline(job_id, job_data, log_callback))
        finally:
            loop.close()
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise e

async def _async_scraper_pipeline(job_id: str, job_data: dict, log_callback):
    from config import supabase
    from agents.parse_agent import main as parse_main

    user_id = job_data["user_id"]
    status_db = job_data["status"]
    input_data = job_data.get("input_data", {})
    output_data = job_data.get("output_data") or {}

    email = input_data.get("user_id") # frontend passes email as user_id usually

    raw_jobs = None

    # Phase 1: Recovery Check
    if status_db == "scraper_raw":
        if is_valid_raw_jobs_payload(output_data):
            log_callback({"progress": 50, "status": "in_progress", "message": "Recovering from scraper_raw state. Skipping Playwright."})
            raw_jobs = output_data
        else:
            log_callback({"progress": 45, "status": "in_progress", "message": "scraper_raw payload invalid. Re-running Playwright scrape."})

    if raw_jobs is None:
        # Phase 2: User Data / Parsing
        user_res = supabase.table("User").select("user_data, resume_url").eq("id", user_id).execute()
        if not user_res.data:
            raise Exception("User not found in DB")
            
        user_record = user_res.data[0]
        user_data_parsed = user_record.get("user_data")
        
        if not user_data_parsed:
            log_callback({"progress": 15, "status": "in_progress", "message": "Parsing resume using Gemini..."})
            
            # The active resume URL is passed from the frontend payload or DB fallback
            resume_url = input_data.get("resume_url") or user_record.get("resume_url")
            if not resume_url:
                raise Exception("No resume URL available for parsing")
                
            user_data_parsed = parse_main(resume_url)
            
            # Save fresh parse result and active URL back to DB
            supabase.table("User").update({
                "user_data": user_data_parsed,
                "resume_url": resume_url
            }).eq("id", user_id).execute()
        
        titles = user_data_parsed.get("titles", [])
        
        # Phase 3: Playwright Scraping
        log_callback({"progress": 20, "status": "in_progress", "message": "Searching LinkedIn for jobs..."})
        
        # Extract credentials from payload
        l_email = input_data.get("linkedin_id")
        l_pass = input_data.get("linkedin_password")
        
        raw_jobs = await search_by_job_titles_speed_optimized(titles, log_callback=log_callback, user_id=email, linkedin_email=l_email, linkedin_password=l_pass)
        
        if not raw_jobs:
            log_callback({"progress": -1, "status": "error", "message": "No jobs found or login failed. Need new session."})
            supabase.table("workflow_sessions").update({
                "status": "failed",
                "output_data": {"error": "Scraping yielded no results or login failed"}
            }).eq("id", job_id).execute()
            
            # Clear context if failed to force re-login next time
            clear_linkedin_context(email)
            raise Exception("No jobs scraped - clearing context")
            
        # Success pulling raw jobs. Save raw state for idempotency.
        log_callback({"progress": 50, "status": "in_progress", "message": f"Saved {len(raw_jobs)} raw descriptions. Triggering Gemini categorization."})
        
        supabase.table("workflow_sessions").update({
            "status": "scraper_raw",
            "output_data": raw_jobs
        }).eq("id", job_id).execute()

    # Phase 4: Gemini Batching
    if raw_jobs:
        # Exclude jobs the user has already applied to, so they never reach the
        # selection screen. Done here (not only in Phase 2) so the scraper_raw-resume
        # path is covered too, and pre-Gemini so we don't spend LLM quota on them.
        # raw_jobs keys and User.applied_jobs are both normalized URLs (split('?')[0]).
        try:
            applied_res = supabase.table("User").select("applied_jobs").eq("id", user_id).execute()
            applied_set = set(applied_res.data[0].get("applied_jobs") or []) if applied_res.data else set()
        except Exception as e:
            print(f"Could not load applied_jobs for filtering: {e}")
            applied_set = set()

        if applied_set:
            before = len(raw_jobs)
            raw_jobs = {url: jd for url, jd in raw_jobs.items() if normalize_job_url(url) not in applied_set}
            removed = before - len(raw_jobs)
            if removed:
                log_callback({"progress": 54, "status": "in_progress", "message": f"Skipping {removed} job(s) you've already applied to."})

        log_callback({"progress": 55, "status": "in_progress", "message": "Analyzing job matches..."})

        structured_jobs = await extract_jobs_in_batches(raw_jobs, batch_size=25, log_callback=log_callback)
        
        # Write final structured data to output_data and mark completed
        supabase.table("workflow_sessions").update({
            "status": "completed",
            "output_data": structured_jobs
        }).eq("id", job_id).execute()
        
        log_callback({"progress": 100, "status": "done", "message": f"Successfully processed {len(structured_jobs)} completely structured jobs!"})
    else:
        raise Exception("No raw jobs found to process")
