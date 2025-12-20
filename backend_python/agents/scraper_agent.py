import asyncio
import sys
import tempfile
import os
from datetime import datetime
import time
import aiohttp
from bs4 import BeautifulSoup

import main.progress_dict as progress_module
from main.progress_dict import LINKEDIN_CONTEXT_OPTIONS
from database.linkedin_context import save_linkedin_context, get_linkedin_context, clear_linkedin_context

# Windows Playwright fix - MUST be at the top
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

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
model_1 = "gemini-3-flash-preview"
model_2 = 'gemini-2.5-flash-lite' # gemini-2.5-flash-lite gemini-2.5-flash-preview-09-2025
model_3 = 'gemini-2.5-flash'
model_4 = 'gemini-robotics-er-1.5-preview'

MODELS = [model_1, model_2, model_3, model_4]

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



async def linkedin_login(browser):
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
        email_input = await page.wait_for_selector('#username', timeout=10000)
        await email_input.fill(LINKEDIN_ID)
        
        print("🔑 Entering password...")
        password_input = await page.wait_for_selector('#password', timeout=5000)
        await password_input.fill(LINKEDIN_PASSWORD)
        
        await debug_capture_page(page, "02_credentials_filled")

        print("🚀 Clicking login button...")
        login_button = await page.wait_for_selector('button[type="submit"]', timeout=5000)
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

async def ensure_logged_in(browser, user_id):
    """Ensure we have a valid logged-in context"""
    global LOGGED_IN_CONTEXT
    
    db_context = get_linkedin_context(user_id)
    # print("context from db", db_context)
    print("HireHawk user", user_id)
    if db_context:
        print(f"♻️ FOUND STORAGE STATE IN DB!")
        print(f"✅ Creating new context with current browser using saved state!")
        
        # Create NEW context with the CURRENT browser using saved storage_state
        try:
            context = await browser.new_context(
                storage_state=db_context,
                **LINKEDIN_CONTEXT_OPTIONS,
            )
            print(f"✅ New context created successfully with saved state!")
            return context
        except Exception as e:
            print(f"⚠️ Failed to restore context: {e}, logging in again...")
            # clear_linkedin_context(user_id)
    
    # No saved state, perform login
    print(f"🔐 No storage state in progress_dict, logging in...")

    context = await linkedin_login(browser)
    
    if context:
        # ✅ SAVE STORAGE STATE (not the context itself!)
        storage_state = await context.storage_state()
        progress_module.linkedin_login_context = storage_state
        print(f"💾 Storage state saved to progress_dict for next request!")

        save_linkedin_context(user_id,storage_state)
        print(f"💾 Storage state saved to DB!")
    return context

# ---------------------------------------------------------------------------
# 2. FIXED PAGINATION - WAIT FOR JOBS AFTER EACH PAGE CLICK
# ---------------------------------------------------------------------------

async def load_all_available_jobs_fixed(page):
    """FIXED: Proper pagination with page-by-page job loading - returns unique URLs"""
    try:
        print("🔄 Starting FIXED pagination job loading...")
        
        unique_job_urls = set()
        max_pages = 3  # Limit pages for speed
        
        for page_num in range(max_pages):
            print(f"📄 Processing page {page_num + 1}/{max_pages}")
            
            # Collect job URLs from current page
            current_page_urls = await collect_jobs_from_current_page(page)
            
            # Add new unique jobs
            new_jobs_count = 0
            for url in current_page_urls:
                clean_url = url.split('?')[0].strip()
                if clean_url not in unique_job_urls:
                    unique_job_urls.add(clean_url)
                    new_jobs_count += 1
            
            print(f"✅ Page {page_num + 1}: Added {new_jobs_count} new jobs (Total: {len(unique_job_urls)})")
            
            # Try to navigate to next page
            next_clicked = await click_next_page_and_wait(page)
            if not next_clicked:
                print(f"🛑 No next page available, stopping at page {page_num + 1}")
                break
        
        print(f"✅ FIXED pagination complete: {len(unique_job_urls)} unique jobs from multiple pages")
        return list(unique_job_urls)
        
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
    """Collect all unique job URLs - 1920x1080 viewport with 4x content visibility"""

    # Set standard viewport: 1920x1080
    await page.set_viewport_size({'width': 2562, 'height': 2000})
    
    # Scale content to 25% (shows 4x more content in same space)
    await page.evaluate('() => { document.body.style.zoom = "0.25"; }')
    
    # Extract all job URLs - simple and direct
    unique_urls = await page.evaluate('''
        () => {
            const urls = new Set();
            // Find all links containing /jobs/view
            const links = document.querySelectorAll('a[href*="/jobs/view"]');
            
            links.forEach(link => {
                const href = link.getAttribute('href');
                if (href) {
                    // Remove query parameters
                    const cleanUrl = href.split('?')[0];
                    urls.add(cleanUrl);
                }
            });
            
            return Array.from(urls);
        }
    ''')
    
    print(f"✅ Found {len(unique_urls)} unique job URLs at 4x visibility in 1920x1080")
    return unique_urls

async def click_next_page_and_wait(page):
    """FIXED: Click next page and wait for new jobs to load"""
    print("moving to next page, if available")
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
    
    # Wait for job count to change (indicating new page loaded)
    for attempt in range(10):  # Max 5 seconds wait
        current_jobs = await page.query_selector_all('a[href*="/jobs/view"]')
        current_count = len(current_jobs)
        
        if current_count != prev_job_count:
            print(f"✅ Page changed! Jobs: {prev_job_count} → {current_count}")
            await asyncio.sleep(0.5)  # Extra wait for full load
            return True
        
        await asyncio.sleep(0.5)
    
    print("⚠️ Page may not have changed, continuing...")
    return True


async def extract_job_description_fixed(session: aiohttp.ClientSession, url, max_retries=3):
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

                    # --- PARSING STEP ---
                    print("   🥣 Parsing HTML with Beautiful Soup...")
                    soup = BeautifulSoup(html_content, 'lxml')

                    # Find the specific element by its ID
                    # On LinkedIn, the job description is in a div with a class, not an ID.
                    # Let's use the class from your previous scraper for a real example.
                    job_details_div = soup.find('div', class_='show-more-less-html__markup')

                    if job_details_div:
                        # Get all the text from the element, stripped of HTML tags
                        job_text = job_details_div.get_text(separator=' ', strip=True)
                        print("   ✅ Extracted content successfully!")
                        return job_text
                    else:
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


async def scrape_platform_speed_optimized(browser, platform_name, config, job_title, user_id):
    """SPEED OPTIMIZED: More lenient filtering to process more jobs"""
    global PROCESSED_JOB_URLS
    
    context = None
    page = None

    context = await ensure_logged_in(browser, user_id)
    if context is None:
        return {}

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
        
        # job_cards now contains URLs directly, not elements
        for i, url in enumerate(job_cards, 1):
            try:
                full_url = url if url.startswith('http') else config["base_url"] + url
                clean_url = full_url.split('?')[0]
                
                if clean_url not in PROCESSED_JOB_URLS:
                    PROCESSED_JOB_URLS.add(clean_url)
                    valid_job_links.append(clean_url)
                    print(f"   ✅ Job {i}: Added to processing queue")
                else:
                    print(f"   🔄 Job {i}: Duplicate URL, skipping")
                        
            except Exception as e:
                print(f"   ❌ Job {i}: Processing error: {e}")
                continue
        
        # Filtering summary
        print(f"\n📊 FILTERING SUMMARY:")
        print(f"   📁 Total URLs collected: {len(job_cards)}")
        print(f"   ✅ Valid jobs: {len(valid_job_links)}")
        print(f"   🔄 Duplicates skipped: {len(job_cards) - len(valid_job_links)}")
        
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
                        extract_job_description_fixed(session, url) 
                        for url in batch_urls
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
            
            # Pair the URLs with their fetched descriptions
            for url, description in zip(valid_job_links, results):
                if description and not description.startswith("Failed"):
                    job_dict[url] = description
                    processed_count += 1
                else:
                    failed_count += 1
                    failed_urls.append(url)
                    print(f"   ❌ Failed to fetch: {url[:80]}... - Reason: {description[:50] if description else 'No response'}")

            print(f"\n📊 EXTRACTION SUMMARY:")
            print(f"   ✅ Successfully processed: {processed_count}/{len(valid_job_links)}")
            print(f"   ❌ Failed: {failed_count}/{len(valid_job_links)}")
            # Remove all failed URLs from processed set and valid list
            failed_set = set(failed_urls)
            PROCESSED_JOB_URLS.difference_update(failed_set)
            valid_job_links = [url for url in valid_job_links if url not in failed_set]
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
        if context:
            try:
                progress_module.linkedin_login_context = await context.storage_state()
            except Exception as e:
                print(f"⚠️ Unable to persist storage state: {e}")
            await context.close()

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

def create_bulk_prompt(jobs_dict: dict) -> str:
    system_instruction = """
You are a professional job data extractor.

For each job entry provided:

- Extract and output all the following fields exactly as named: "title", "job_id", "company_name", "location", "experience", "salary", 
  "key_skills", "job_url", "posted_at", "job_description", "source", and "relevance_score".

- Extract the job_id from the URL after '/jobs/view/'.

- Use the job description text to find all other fields.

- Provide the output only as a pure JSON array, no explanations or extra text.

- Give full 200% attention and efforts to extract all fields properly. 

If any field is not present, use null object or empty list [] accordingly only for "salary", "location", "experience", "posted_date", "source" and "relevance_score" remaining "job_id", "job_description" (use provided description directly here), title exatract mandatory no option for not avaliable or null values here these 3 are mandatory things.
Make sure all fields should extracted properly don't give null or empty list without extrating data in rare cases use that null or empty list untill unless all fields are mandatory

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
    "relevance_score": "high"
  },
  ...
]

"""

    prompt = system_instruction + f"\nProcess {len(jobs_dict)} jobs:\n"
    for idx, (url, desc) in enumerate(jobs_dict.items(), 1):
        safe_desc = desc.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        prompt += f'\n--- JOB {idx} ---\njob_url: "{url}"\njob_description: "{safe_desc[:1500]}"\n'
    return prompt



def create_fallback_data_from_dict(url: str, job_description: str) -> dict:
    return {
        "title": "Title not extracted",
        "job_id": "ID not extracted", 
        "company_name": "Company not extracted",
        "location": "India",
        "experience": "Not specified",
        "salary": "Not specified",
        "key_skills": [],
        "job_url": url,
        "posted_at": "Not specified",
        "job_description": job_description or "Description not available",
        "source": "linkedin",
        "relevance_score": "unknown"
    }

def parse_bulk_response(response_text: str, original_jobs: dict) -> list:
    try:
        clean = response_text.strip()
        if clean.startswith("```json"):
            clean = clean[7:].lstrip()
        elif clean.startswith("```"):
            clean = clean[3:].lstrip()
        if clean.endswith("```"):
            clean = clean[:-3].rstrip()
        
        extracted_jobs = json.loads(clean)
        if not isinstance(extracted_jobs, list):
            extracted_jobs = [extracted_jobs]
        
        job_urls = list(original_jobs.keys())
        for i, job in enumerate(extracted_jobs):
            if i < len(job_urls):
                url = job_urls[i]
                job["job_url"] = url
                job["job_description"] = original_jobs[url]
                job["source"] = "linkedin"
        
        while len(extracted_jobs) < len(job_urls):
            idx = len(extracted_jobs)
            url = job_urls[idx]
            extracted_jobs.append(create_fallback_data_from_dict(url, original_jobs[url]))
        
        return extracted_jobs
    except Exception as e:
        print(f"❌ Error parsing response: {e}")
        return [create_fallback_data_from_dict(url, jd) for url, jd in original_jobs.items()]

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
                contents='system instruction: \n'+system_instruction+"\n"+prompt,
                config=types.GenerateContentConfig(temperature=0.2)
            ).text
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


async def extract_jobs_in_batches(jobs_dict: dict, batch_size: int = 25) -> list:  # Increased batch size
    all_extracted = []
    items = list(jobs_dict.items())
    total_batches = (len(items) + batch_size - 1) // batch_size
    
    for i in range(0, len(items), batch_size):
        batch = dict(items[i : i + batch_size])
        batch_num = (i // batch_size) + 1
        print(f"🔄 Processing batch {batch_num}/{total_batches}: {len(batch)} jobs")
        
        try:
            result = await extract_single_batch(batch)
            all_extracted.extend(result)
            print(f"✅ Batch {batch_num} completed")
        except Exception as e:
            print(f"❌ Batch {batch_num} error: {e}")
            result = [create_fallback_data_from_dict(url, jd) for url, jd in batch.items()]
            all_extracted.extend(result)
        
        await asyncio.sleep(0.1)  # Minimal wait between batches
    
    return all_extracted

# ---------------------------------------------------------------------------
# 6. MAIN EXECUTION FUNCTIONS (SPEED OPTIMIZED)
# ---------------------------------------------------------------------------

async def search_by_job_titles_speed_optimized(job_titles,platforms=None, progress=None,user_id=None):
    """SPEED OPTIMIZED: All fixes applied - faster execution"""
    global PROCESSED_JOB_URLS, LOGGED_IN_CONTEXT
    
    if platforms is None:
        platforms = list(PLATFORMS.keys())
    
    all_jobs = {}
    PROCESSED_JOB_URLS.clear()
    
    print(f"🚀 Starting SPEED-OPTIMIZED job extraction with ALL FIXES...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu', '--no-zygote', '--disable-extensions', '--disable-background-networking', '--disable-renderer-backgrounding', '--no-first-run', '--mute-audio', '--metrics-recording-only'
            ]
        )
        
        try:
            print("🔐 Performing LinkedIn login...")
            login_context = await ensure_logged_in(browser, user_id)
            
            if login_context is None:
                print("❌ Failed to login to LinkedIn. Exiting...")
                return {}
            
            print("✅ Successfully logged in to LinkedIn!")
            
            for i, job_title in enumerate(job_titles, 1):
                print(f"\n{'='*70}")
                print(f"⚡ SPEED-OPTIMIZED SEARCH {i}/{len(job_titles)}: '{job_title}'")
                print(f"🔢 Processed URLs so far: {len(PROCESSED_JOB_URLS)}")
                print(f"🔢 Progressed so far: {progress[user_id]}%")
                print(f"{'='*70}")
                
                
                for platform_name in platforms:
                    try:
                        result = await scrape_platform_speed_optimized(
                            browser, platform_name, PLATFORMS[platform_name], job_title, user_id
                        )
                        all_jobs.update(result)
                        print(f"📈 Jobs from '{job_title}': {len(result)}")
                    except Exception as e:
                        print(f"❌ Error searching '{job_title}' on {platform_name}: {e}")
                    
                    await asyncio.sleep(0.5)  # Minimal wait between searches
                
                if len(job_title) == 5:
                    progress[user_id] += 15
                else:
                    progress[user_id] += (75/len(job_titles))
                print(f"📊 '{job_title}' complete. Total unique jobs: {len(all_jobs)}")


            
        finally:
            if LOGGED_IN_CONTEXT:
                await LOGGED_IN_CONTEXT.close()
                print("="*70)
                print(f"context has been closed")
                print("="*70)
            await browser.close()
    
    print(f"\n{'='*70}")
    print(f"🏆 SPEED-OPTIMIZED EXTRACTION COMPLETE!")
    print(f"📊 Total unique jobs: {len(all_jobs)}")
    print(f"🔢 Total URLs processed: {len(PROCESSED_JOB_URLS)}")
    print(f"⚡ Speed optimization: MAXIMUM")
    print(f"🔧 All fixes applied: YES")
    print(f"🔐 Authentication: ENABLED")
    print(f" progress percentage: {progress[user_id]}%")
    print(f"{'='*70}")
    
    return all_jobs

def run_scraper_in_new_loop(titles, keywords, job_progress, user_id, password, progress_user):
    """Run scraper in a fresh event loop - Production Ready"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(main(titles, keywords,job_progress, user_id, password, progress_user))
            return result
        finally:
            loop.close()
    except Exception as e:
        print(f"Scraper error: {e}")
        return []

async def main(parsed_titles=None, parsed_keywords=None, progress=None, user_id=None, password=None, progress_user=None ):
    global JOB_TITLES, FILTERING_KEYWORDS, LINKEDIN_ID, LINKEDIN_PASSWORD
    if parsed_titles:
        JOB_TITLES = parsed_titles
    if parsed_keywords:
        FILTERING_KEYWORDS = parsed_keywords
    if user_id and password:
        LINKEDIN_ID = user_id
        LINKEDIN_PASSWORD = password
        print(f"login user id configured to {LINKEDIN_ID}")

    print("🧠 Starting SPEED-OPTIMIZED job extraction with ALL FIXES...")

    all_jobs = await search_by_job_titles_speed_optimized(JOB_TITLES,progress=progress, user_id=progress_user)
    
    if len(all_jobs) == 0:
        print("❌ No jobs found to analyze...")
        progress[progress_user] = 100
        return
    
    print(f"🧠 Sending {len(all_jobs)} jobs to Gemini for extraction...")
    extracted = await extract_jobs_in_batches(all_jobs, batch_size=25)  # Larger batches
    
    # Save results
    # from datetime import datetime
    # timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    # filename = f"linkedin_jobs_ALL_FIXES_{timestamp}.json"
    
    # with open(filename, "w", encoding="utf-8") as f:
    #     json.dump(extracted, f, indent=2, ensure_ascii=False)
    
    # print(f"✅ Successfully extracted data for {len(extracted)} jobs")
    # print(f"📁 Results saved to {filename}")
    
    # Print summary
    total_skills = set()
    companies = set()
    
    for job in extracted:
        if job.get("key_skills"):
            total_skills.update(job["key_skills"])
        if job.get("company_name") and job["company_name"] != "Not extracted":
            companies.add(job["company_name"])
    
    if(progress[progress_user] == 85):
        progress[progress_user] += 15
    else:
        progress[progress_user] += (100-progress[progress_user])

    print(f"\n📊 FINAL SUMMARY:")
    print(f" 🏢 Companies: {len(companies)}")
    print(f" 🛠️ Unique skills found: {len(total_skills)}")
    print(f" 📄 Total jobs extracted: {len(extracted)}")
    print(f" ⚡ Speed optimized: YES")
    print(f" 🔧 All fixes applied: YES")
    print(f" 🔵 Easy Apply enabled: YES")
    print(f" 🔐 Authenticated scraping: YES")
    print(f" Progress: {progress[progress_user]}%")

    return extracted

if __name__ == "__main__":
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    print(f"🚀 Starting SPEED-OPTIMIZED LinkedIn Job Scraper with ALL FIXES at {timestamp}...")
    print(f"📋 Job Titles to search: {len(JOB_TITLES)}")
    print(f"🔍 Filtering keywords: {len(FILTERING_KEYWORDS)}")
    print(f"🔵 Easy Apply: ENABLED")
    print(f"⚡ Speed optimization: MAXIMUM")
    print(f"🔧 All fixes applied: YES")
    print(f"🔐 LinkedIn Authentication: ENABLED")
    
    asyncio.run(main())
