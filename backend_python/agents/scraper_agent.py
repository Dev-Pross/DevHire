import asyncio
import sys
import tempfile
import os
from datetime import datetime
import aiohttp
from bs4 import BeautifulSoup

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
MODEL_NAME="gemini-2.5-flash"
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
    
    context = await browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1920, "height": 1080},
        # device_scale_factor=0.5,  # Keep this
        locale="en-US",
        timezone_id="Asia/Calcutta",
    )
    
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
            asyncio.sleep(10)
            return
        
        if "feed" not in current_url:
             print(f"{Colors.RED}❌ Login Failed!{Colors.END}")
             asyncio.sleep(10)
             return
        
        
        await debug_capture_page(page, "03_after_login_click")

        LOGGED_IN_CONTEXT = context
        await page.close()
        return context
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        await page.close()
        await context.close()
        return None

async def ensure_logged_in(browser):
    """Ensure we have a valid logged-in context"""
    global LOGGED_IN_CONTEXT
    
    if LOGGED_IN_CONTEXT is None:
        print("🔄 No active login session, logging in...")
        LOGGED_IN_CONTEXT = await linkedin_login(browser)
        
        if LOGGED_IN_CONTEXT is None:
            raise Exception("Failed to login to LinkedIn")
    
    return LOGGED_IN_CONTEXT

# ---------------------------------------------------------------------------
# 2. FIXED PAGINATION - WAIT FOR JOBS AFTER EACH PAGE CLICK
# ---------------------------------------------------------------------------

async def load_all_available_jobs_fixed(page):
    """FIXED: Proper pagination with page-by-page job loading"""
    try:
        print("🔄 Starting FIXED pagination job loading...")
        
        unique_job_urls = set()
        job_elements = []
        max_pages = 2  # Limit pages for speed
        
        for page_num in range(max_pages):
            print(f"📄 Processing page {page_num + 1}/{max_pages}")
            
            # First, load all jobs on current page by scrolling
            await scroll_current_page(page)
            
            # Collect jobs from current page
            current_page_jobs = await collect_jobs_from_current_page(page)
            
            # Add new unique jobs
            new_jobs_count = 0
            for element in current_page_jobs:
                try:
                    href = await element.get_attribute('href')
                    if href:
                        clean_href = href.split('?')[0].strip()
                        if clean_href not in unique_job_urls:
                            unique_job_urls.add(clean_href)
                            job_elements.append(element)
                            new_jobs_count += 1
                except:
                    continue
            
            print(f"✅ Page {page_num + 1}: Added {new_jobs_count} new jobs (Total: {len(unique_job_urls)})")
            
            # Try to navigate to next page
            next_clicked = await click_next_page_and_wait(page)
            # next_clicked = False
            if not next_clicked:
                print(f"🛑 No next page available, stopping at page {page_num + 1}")
                break
        
        print(f"✅ FIXED pagination complete: {len(job_elements)} unique jobs from multiple pages")
        return job_elements
        
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
    """Collect all job elements from current page"""
    selectors = [
        'a.job-card-container__link',
        'a[class*="job-card-container__link"]',
        '.job-card-container a[href*="/jobs/view"]',
        'li[data-job-id] a[href*="/jobs/view"]'
    ]
    
    all_elements = []
    for selector in selectors:
        try:
            elements = await page.query_selector_all(selector)
            all_elements.extend(elements)
        except:
            continue
    
    return all_elements

async def click_next_page_and_wait(page):
    """FIXED: Click next page and wait for new jobs to load"""
    try:
        # Your specific next button selectors
        next_selectors = [
            'button.jobs-search-pagination__button--next:not([disabled])',
            'button.artdeco-button.jobs-search-pagination__button--next:not([disabled])',
            '.jobs-search-pagination__button--next:not([disabled])',
            'button[aria-label*="Go to next page"]:not([disabled])'
        ]
        
        for selector in next_selectors:
            try:
                next_button = await page.wait_for_selector(selector, timeout=2000)
                if next_button and await next_button.is_visible() and await next_button.is_enabled():
                    # Get current job count before clicking
                    current_jobs = await page.query_selector_all('a[href*="/jobs/view"]')
                    prev_count = len(current_jobs)
                    
                    print(f"🔄 Clicking next page button: {selector}")
                    await next_button.scroll_into_view_if_needed()
                    await next_button.click()
                    
                    # FIXED: Wait for new page to load with new jobs
                    await wait_for_page_change(page, prev_count)
                    return True
            except:
                continue
        
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

# ---------------------------------------------------------------------------
# 3. FIXED JOB DESCRIPTION - HANDLE "SEE MORE" BUTTON
# ---------------------------------------------------------------------------

# async def extract_job_description_fixed(context, job_url):
#     """FIXED: Robust job description extraction with proper timeouts"""
#     detail_page = await context.new_page()
    
#     try:
#         # INCREASED timeouts for LinkedIn's slow responses
#         detail_page.set_default_navigation_timeout(45000)  # Increased to 45 seconds
#         detail_page.set_default_timeout(30000)  # Increased to 30 seconds
        
#         print(f"🔍 Navigating to job page...")
        
#         # Retry logic for navigation
#         max_retries = 2
#         for attempt in range(max_retries):
#             try:
#                 await detail_page.goto(
#                     job_url, 
#                     wait_until="domcontentloaded",  # Faster than "load"
#                     timeout=45000  # 45 second timeout
#                 )
#                 print(f"✅ Navigation successful on attempt {attempt + 1}")
#                 break
                
#             except Exception as nav_error:
#                 if attempt < max_retries - 1:
#                     print(f"⚠️ Navigation attempt {attempt + 1} failed, retrying...")
#                     await asyncio.sleep(2)  # Wait before retry
#                     continue
#                 else:
#                     # Final attempt failed
#                     await detail_page.close()
#                     return f"Navigation failed after {max_retries} attempts: {str(nav_error)[:100]}"
        
#         # Minimal wait after navigation
#         await asyncio.sleep(6)
        
#         # Click "See more" button to reveal full description
#         await click_see_more_button(detail_page)
        
#         # Try to get full description with updated selectors
#         description_selectors = [
#             'div.show-more-less-html__markup',          # Primary after "see more"
#             '.jobs-description__content',               # Full content container
#             '.job-details-jobs-unified-top-card__job-description',
#             '#job-details',                             
#             '.jobs-box__html-content',
#             '.jobs-description-content__text',
#             '.jobs-unified-top-card__content'           # Fallback selector
#         ]
        
#         for selector in description_selectors:
#             try:
#                 desc_elem = await detail_page.wait_for_selector(selector, timeout=10000)  # 10s for element
#                 if desc_elem:
#                     description = (await desc_elem.inner_text()).strip()
#                     if len(description) > 200:  # Ensure substantial content
#                         await detail_page.close()
#                         print(f"✅ Description extracted: {len(description)} chars")
#                         return description
#             except:
#                 continue
        
#         # Fallback to any job content area
#         try:
#             fallback_content = await detail_page.query_selector('.jobs-unified-top-card, .job-view-layout, .jobs-details')
#             if fallback_content:
#                 fallback_text = await fallback_content.inner_text()
#                 if len(fallback_text) > 100:
#                     await detail_page.close()
#                     return fallback_text[:2000]  # Limit for performance
#         except:
#             pass
        
#         await detail_page.close()
#         return "Description not found on page"
                
#     except Exception as e:
#         await detail_page.close()
#         return f"Error extracting description: {str(e)[:200]}"

async def extract_job_description_fixed(session: aiohttp.ClientSession, url):
    """
    Fetches the HTML of a URL and then parses it to extract
    the text content of the element with id='job-details'.
    """
    print(f"🚀 Fetching: {url}")
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        async with session.get(url, headers=headers, timeout=15) as response:
            if response.status == 200:
                html_content = await response.text()
                print("   ✅ HTML fetched successfully.")

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
                    return "Failed: Could not find the job description element in the HTML."
            else:
                return  f"Failed: HTTP status {response.status}"
    except Exception as e:
        return  f"Failed: An error occurred - {str(e)}"

# async def click_see_more_button(page):
#     """FIXED: Click 'See more' button to reveal full job description"""
#     try:
#         # Your specific "See more" button class and alternatives
#         see_more_selectors = [
#             'button.jobs-description__footer-button',
#             'button.jobs-description__footer-button.t-14.t-black--light.t-bold.artdeco-card__action.artdeco-button.artdeco-button--icon-right.artdeco-button--3.artdeco-button--fluid.artdeco-button--tertiary.ember-view',
#             # 'button[data-tracking-control-name*="see-more"]',
#             # 'button[aria-expanded="false"]',
#             # '.show-more-less-html__button--more',
#             # 'button:has-text("See more")',
#             # 'button:has-text("Show more")'
#         ]
        
#         for selector in see_more_selectors:
#             try:
#                 see_more_btn = await page.wait_for_selector(selector, timeout=2000)
#                 if see_more_btn and await see_more_btn.is_visible():
#                     print("🔍 Clicking 'See more' button for full description... using ",selector)
#                     await see_more_btn.scroll_into_view_if_needed()
#                     await see_more_btn.click()
#                     await asyncio.sleep(1.5)  # Wait for content to expand
#                     print("✅ 'See more' clicked - full description should be visible")
#                     return True
#             except:
#                 continue
        
#         print("⚠️ No 'See more' button found - using available description")
#         return False
        
#     except Exception as e:
#         print(f"❌ See more button error: {e}")
#         return False

# ---------------------------------------------------------------------------
# 4. OPTIMIZED JOB PROCESSING - INCREASED SPEED
# ---------------------------------------------------------------------------

# async def process_single_job_optimized(context, job_link, job_index, total_jobs):
#     """OPTIMIZED: Faster job processing with full descriptions"""
#     try:
#         print(f"⚡ Processing job {job_index + 1}/{total_jobs}")
        
#         job_description = await extract_job_description_fixed(context, job_link)
        
#         if job_description and len(job_description) > 50:
#             return job_link, job_description, "added"
#         else:
#             return job_link, job_description or "Minimal content", "added"
                    
#     except Exception as e:
#         print(f"❌ Error job {job_index + 1}: {e}")
#         return job_link, f"Processing error: {str(e)[:100]}", "added"

async def scrape_platform_speed_optimized(browser, platform_name, config, job_title):
    """SPEED OPTIMIZED: More lenient filtering to process more jobs"""
    global PROCESSED_JOB_URLS
    
    context = await ensure_logged_in(browser)
    page = await context.new_page()
    
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
        
        print(f"📊 Processing {len(job_cards)} job cards with RELAXED filtering")
        
        valid_job_links = []
        
        # RELAXED filtering with debugging
        keyword_filtered = 0
        link_failed = 0
        text_failed = 0
        
        for i, card in enumerate(job_cards):
            try:
                # Get text content
                text_content = (await card.inner_text()).strip()
                # if len(text_content) < 5:  # Very minimal requirement
                #     text_failed += 1
                #     print(f"   Card {i+1}: No text content")
                #     continue
                
                # print(f"   Card {i+1}: Text preview: '{text_content[:50]}...'")
                
                # # RELAXED keyword check - much more lenient
                # text_lower = text_content.lower()
                
                # # Check for job title match first (most important)
                # title_match = job_title.lower().split() 
                # has_title_keywords = any(word in text_lower for word in title_match if len(word) > 2)
                
                # # Check for any technical keywords
                # has_tech_keywords = any(keyword.lower() in text_lower for keyword in FILTERING_KEYWORDS)
                
                # # Check for common job-related words (very broad)
                # # common_job_words = ['developer', 'engineer', 'software', 'programming', 'coding', 'technical', 'technology', 'web', 'application', 'system']
                # # has_job_words = any(word in text_lower for word in common_job_words)
                
                # # MUCH MORE LENIENT: Accept if ANY of these conditions are met
                # if has_title_keywords or has_tech_keywords:
                #     print(f"   ✅ Card {i+1}: Passed keyword filter")
                # else:
                #     keyword_filtered += 1
                #     print(f"   ❌ Card {i+1}: No relevant keywords found")
                #     continue
                
                # Extract job link with enhanced debugging
                href = await card.get_attribute('href')
                if not href:
                    # Try multiple methods to find link
                    link_selectors = [
                        'a[href*="/jobs/view"]',
                        '[href*="/jobs/view"]'
                    ]
                    
                    for selector in link_selectors:
                        try:
                            link_elem = await card.query_selector(selector)
                            if link_elem:
                                href = await link_elem.get_attribute('href')
                                if href and '/jobs/' in href:
                                    print(f"   ✅ Card {i+1}: Link found using {selector}")
                                    break
                        except:
                            continue
                
                if href and '/jobs/view' in href:  # More lenient - not just '/jobs/view/'
                    full_url = href if href.startswith('http') else config["base_url"] + href
                    clean_url = full_url.split('?')[0]
                    
                    if clean_url not in PROCESSED_JOB_URLS:
                        PROCESSED_JOB_URLS.add(clean_url)
                        valid_job_links.append(clean_url)
                        print(f"   ✅ Card {i+1}: Added to processing queue")
                    else:
                        print(f"   🔄 Card {i+1}: Duplicate URL, skipping")
                else:
                    link_failed += 1
                    print(f"   ❌ Card {i+1}: No valid job link found")
                    continue
                        
            except Exception as e:
                print(f"   ❌ Card {i+1}: Processing error: {e}")
                continue
        
        # Filtering summary
        print(f"\n📊 FILTERING SUMMARY:")
        print(f"   📁 Total cards: {len(job_cards)}")
        print(f"   ❌ No text content: {text_failed}")
        print(f"   ❌ No keywords: {keyword_filtered}")
        print(f"   ❌ No valid links: {link_failed}")
        print(f"   ✅ Valid jobs: {len(valid_job_links)}")
        
        print(f"✅ {len(valid_job_links)} jobs ready for OPTIMIZED processing")
        
        # Continue with job processing...
        # results=[]
        if valid_job_links:
            print(f"✅ {len(valid_job_links)} jobs ready for OPTIMIZED processing with aiohttp...")
            
            # Use aiohttp to fetch all descriptions in parallel
            async with aiohttp.ClientSession() as session:
                tasks = [
                    extract_job_description_fixed(session, url) 
                    for url in valid_job_links
                ]
                
                results = await asyncio.gather(*tasks)

            # with open(f"results_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}", "w", encoding="utf-8") as f:
            #     json.dump(results, f, indent=2, ensure_ascii=False)
            

            processed_count = 0
            # Pair the URLs with their fetched descriptions
            for url, description in zip(valid_job_links, results):
                if description and not description.startswith("Failed"):
                    job_dict[url] = description
                    processed_count += 1

            print(f"✅ {processed_count} jobs processed with full descriptions")
            # with open("scrapped_jobs", "w", encoding="utf-8") as f:
            #     f.write(str(job_dict))

        return job_dict
        
    except Exception as e:
        print(f"❌ Error in speed-optimized search: {e}")
        return {}
    finally:
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
    max_tries=5
    delay=1
    for attempt in range(max_tries):
        try:

            system_instruction = """
                You are a professional job-data extraction specialist. Extract precisely the requested job titles and keywords, ensuring accuracy and consistency. Follow these rules strictly:
                - Do not invent data not present.
                - Use formal, clear, structured format.
                - Prioritize ATS keywords and recruiter-friendly titles.
                - Avoid company names or sensitive project code names.
                - Following the prompt as it is and make sure data should align properly.
                """
            response = client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.3,
                )
            )
            # from datetime import datetime
            # timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            # filename = f"gemini_scraper{timestamp}.txt"
            
            # with open(filename, "w", encoding="utf-8") as f:
            #     f.write(response.text)
            return parse_bulk_response(response.text, batch_dict)
        except Exception as e:
            print(f"❌ Attempt {attempt +1} failed with error: {e}")
            if attempt < 2 - 1:
                await asyncio.sleep(delay)
                delay *= 2  # exponential backoff
            else:
                print("Max retries reached, exiting batch.")


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
            login_context = await linkedin_login(browser)
            
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
                            browser, platform_name, PLATFORMS[platform_name], job_title
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


            # filtered_jobs = {}

            # if len(all_jobs)<=0:
            #     return {}
            # skills = FILTERING_KEYWORDS+JOB_TITLES
            # if len(all_jobs) > 50:
            #     batch_size = len(all_jobs)//3
            #     items = list(all_jobs.items())
            #     for j in range(0, len(all_jobs), batch_size):
            #         batch = dict(items[i : i + batch_size])
            #         batch_num = (i // batch_size) + 1
            #         print(f"🔄 Processing batch {batch_num}/{3}: {len(batch)} jobs")
            #         prompt = build_prompt(skills,jobs=batch)
                    
            #         delay=0.5
            #         for i in range(1,3):
            #             try:
            #                 print("gemini attempt for filteration: ",i)
            #                 response = client.models.generate_content(
            #                     model='gemini-2.5-flash-lite',
            #                     contents=prompt,
            #                     config=types.GenerateContentConfig(
            #                         temperature=0.3,
            #                     )
            #                 )
            #                 filename = f"gemini_scraper_filteration_batch_{j}.txt"
                            
            #                 with open(filename, "w", encoding="utf-8") as f:
            #                     f.write(response.text)
            #                 if(response.text):
            #                     filtered_jobs.update(parse_filtering(response.text, batch))
            #                     # return job_dict
                        
            #                 asyncio.sleep(delay)
            #             except Exception as e:
            #                 print("Gemini error: %s", str(e))
                    
                
        finally:
            if LOGGED_IN_CONTEXT:
                await LOGGED_IN_CONTEXT.close()
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

def run_scraper_in_new_loop(titles, keywords, job_progress, user_id, password):
    """Run scraper in a fresh event loop - Production Ready"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(main(titles, keywords,job_progress, user_id, password))
            return result
        finally:
            loop.close()
    except Exception as e:
        print(f"Scraper error: {e}")
        return []

async def main(parsed_titles=None, parsed_keywords=None, progress=None, user_id=None, password=None ):
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

    all_jobs = await search_by_job_titles_speed_optimized(JOB_TITLES,progress=progress, user_id=user_id)
    
    if len(all_jobs) == 0:
        print("❌ No jobs found to analyze...")
        progress[user_id] = 100
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
    
    if(progress[user_id] == 85):
        progress[user_id] += 15
    else:
        progress[user_id] += (100-progress[user_id])

    print(f"\n📊 FINAL SUMMARY:")
    print(f" 🏢 Companies: {len(companies)}")
    print(f" 🛠️ Unique skills found: {len(total_skills)}")
    print(f" 📄 Total jobs extracted: {len(extracted)}")
    print(f" ⚡ Speed optimized: YES")
    print(f" 🔧 All fixes applied: YES")
    print(f" 🔵 Easy Apply enabled: YES")
    print(f" 🔐 Authenticated scraping: YES")
    print(f" Progress: {progress[user_id]}%")

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
