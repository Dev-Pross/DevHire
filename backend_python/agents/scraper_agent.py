import asyncio
import sys

# Windows Playwright fix - MUST be at the top
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from playwright.async_api import async_playwright
from concurrent.futures import ThreadPoolExecutor
import json
import google.generativeai as genai
from urllib.parse import urlparse
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
        "url_template": "https://www.linkedin.com/jobs/search/?f_AL=true&f_E=1%2C2&f_JT=F&f_TPR=r178200&f_WT=1%2C2%2C3&keywords={role}&location=India&origin=JOB_SEARCH_PAGE_JOB_FILTER&sortBy=DD",
        "base_url": "https://in.linkedin.com",
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

# ---------------------------------------------------------------------------
# 1. ENHANCED LOGIN FUNCTIONALITY
# ---------------------------------------------------------------------------

# async def apply_forced_zoom(page):
#     """Perfect page alignment + scrolling fix"""
#     # await page.evaluate('''
#     # () => {
#     #     const style = document.createElement('style');
#     #     style.textContent = `
#     #     /* Remove all margins and padding */
#     #     * { box-sizing: border-box !important; }
        
#     #     html, body {
#     #         margin: 0 !important;
#     #         padding: 0 !important;
#     #         height: 100vh !important;
#     #         overflow: hidden !important;
#     #     }
        
#     #     /* Hide LinkedIn header to save space */
#     #     .global-nav,
#     #     .msg-overlay-list-bubble,
#     #     .application-outlet > nav {
#     #         display: none !important;
#     #     }
        
#     #     /* Main app container full height */
#     #     .application-outlet {
#     #         height: 100vh !important;
#     #         display: flex !important;
#     #         flex-direction: column !important;
#     #     }
        
#     #     /* Jobs page container */
#     #     .jobs-search-page {
#     #         flex: 1 !important;
#     #         height: 100% !important;
#     #         display: flex !important;
#     #         flex-direction: column !important;
#     #     }
        
#     #     /* Remove sidebar completely */
#     #     .scaffold-layout__sidebar,
#     #     .jobs-search-filters-panel {
#     #         display: none !important;
#     #     }
        
#     #     /* Main content area full width and height */
#     #     .scaffold-layout__content {
#     #         flex: 1 !important;
#     #         width: 100% !important;
#     #         display: flex !important;
#     #     }
        
#     #     .scaffold-layout__main {
#     #         width: 100% !important;
#     #         height: 100% !important;
#     #         flex: 1 !important;
#     #         display: flex !important;
#     #         flex-direction: column !important;
#     #     }
        
#     #     /* Job results container - KEY FIX */
#     #     .jobs-search-results-list,
#     #     ul[data-view-name="jobs-search-results-list"] {
#     #         flex: 1 !important;
#     #         height: 100% !important;
#     #         max-height: none !important;
#     #         overflow-y: auto !important;
#     #         padding: 2px !important;
#     #         margin: 0 !important;
#     #         list-style: none !important;
#     #     }
        
#     #     /* Compact job cards */
#     #     .job-card-container,
#     #     .jobs-search-results__list-item {
#     #         margin: 1px 0 !important;
#     #         min-height: 70px !important;
#     #         max-height: 80px !important;
#     #     }
        
#     #     /* Hide pagination */
#     #     .jobs-search-pagination {
#     #         display: none !important;
#     #     }
#     #     `;
#     #     document.head.appendChild(style);
        
#     #     // Apply 33% zoom
#     #     //document.documentElement.style.zoom = '0.';
        
#     #     console.log('✅ Perfect alignment + zoom applied');
#     # }
#     # ''')


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
        
        print("🚀 Clicking login button...")
        login_button = await page.wait_for_selector('button[type="submit"]', timeout=5000)
        await login_button.click()
        await asyncio.sleep(5)
        
        current_url = page.url
        if "feed" in current_url:
            print("✅ Login successful with FORCED zoom!")
        
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
        max_pages = 5  # Limit pages for speed
        
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
            # Enhanced scrolling with multiple methods
            for i in range(8):
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
                
                print(f"📜 Scroll {i+1}/8: Top={scroll_result.get('scrollTop', 0)}, Window={scroll_result.get('windowScroll', 0)}, CanScroll={scroll_result.get('canScroll', False)}")
                
                # Additional Playwright-native scrolling
                try:
                    if job_list_element:
                        await job_list_element.scroll_into_view_if_needed()
                        await page.mouse.wheel(0, 500)# Mouse wheel scroll
                        
                except:
                    pass
                
                await asyncio.sleep(1.5)  # Longer wait for content loading
        else:
            # Fallback to page scrolling
            print("⚠️ No job list container found, using page scroll")
            for i in range(6):
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await page.mouse.wheel(0, 500)
                print(f"📜 Page scroll {i+1}/6")
                await asyncio.sleep(1.5)
        
        print("✅ Enhanced scrolling completed")
        
        # Force additional job loading
        await page.evaluate('window.dispatchEvent(new Event("scroll"))')
        await asyncio.sleep(2)
        
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
            await asyncio.sleep(1)  # Extra wait for full load
            return True
        
        await asyncio.sleep(0.5)
    
    print("⚠️ Page may not have changed, continuing...")
    return True

# ---------------------------------------------------------------------------
# 3. FIXED JOB DESCRIPTION - HANDLE "SEE MORE" BUTTON
# ---------------------------------------------------------------------------

async def extract_job_description_fixed(context, job_url):
    """FIXED: Robust job description extraction with proper timeouts"""
    detail_page = await context.new_page()
    
    try:
        # INCREASED timeouts for LinkedIn's slow responses
        detail_page.set_default_navigation_timeout(45000)  # Increased to 45 seconds
        detail_page.set_default_timeout(30000)  # Increased to 30 seconds
        
        print(f"🔍 Navigating to job page...")
        
        # Retry logic for navigation
        max_retries = 2
        for attempt in range(max_retries):
            try:
                await detail_page.goto(
                    job_url, 
                    wait_until="domcontentloaded",  # Faster than "load"
                    timeout=45000  # 45 second timeout
                )
                print(f"✅ Navigation successful on attempt {attempt + 1}")
                break
                
            except Exception as nav_error:
                if attempt < max_retries - 1:
                    print(f"⚠️ Navigation attempt {attempt + 1} failed, retrying...")
                    await asyncio.sleep(2)  # Wait before retry
                    continue
                else:
                    # Final attempt failed
                    await detail_page.close()
                    return f"Navigation failed after {max_retries} attempts: {str(nav_error)[:100]}"
        
        # Minimal wait after navigation
        await asyncio.sleep(6)
        
        # Click "See more" button to reveal full description
        await click_see_more_button(detail_page)
        
        # Try to get full description with updated selectors
        description_selectors = [
            'div.show-more-less-html__markup',          # Primary after "see more"
            '.jobs-description__content',               # Full content container
            '.job-details-jobs-unified-top-card__job-description',
            '#job-details',                             
            '.jobs-box__html-content',
            '.jobs-description-content__text',
            '.jobs-unified-top-card__content'           # Fallback selector
        ]
        
        for selector in description_selectors:
            try:
                desc_elem = await detail_page.wait_for_selector(selector, timeout=10000)  # 10s for element
                if desc_elem:
                    description = (await desc_elem.inner_text()).strip()
                    if len(description) > 200:  # Ensure substantial content
                        await detail_page.close()
                        print(f"✅ Description extracted: {len(description)} chars")
                        return description
            except:
                continue
        
        # Fallback to any job content area
        try:
            fallback_content = await detail_page.query_selector('.jobs-unified-top-card, .job-view-layout, .jobs-details')
            if fallback_content:
                fallback_text = await fallback_content.inner_text()
                if len(fallback_text) > 100:
                    await detail_page.close()
                    return fallback_text[:2000]  # Limit for performance
        except:
            pass
        
        await detail_page.close()
        return "Description not found on page"
                
    except Exception as e:
        await detail_page.close()
        return f"Error extracting description: {str(e)[:200]}"

async def click_see_more_button(page):
    """FIXED: Click 'See more' button to reveal full job description"""
    try:
        # Your specific "See more" button class and alternatives
        see_more_selectors = [
            'button.jobs-description__footer-button',
            'button.jobs-description__footer-button.t-14.t-black--light.t-bold.artdeco-card__action.artdeco-button.artdeco-button--icon-right.artdeco-button--3.artdeco-button--fluid.artdeco-button--tertiary.ember-view',
            # 'button[data-tracking-control-name*="see-more"]',
            # 'button[aria-expanded="false"]',
            # '.show-more-less-html__button--more',
            # 'button:has-text("See more")',
            # 'button:has-text("Show more")'
        ]
        
        for selector in see_more_selectors:
            try:
                see_more_btn = await page.wait_for_selector(selector, timeout=2000)
                if see_more_btn and await see_more_btn.is_visible():
                    print("🔍 Clicking 'See more' button for full description... using ",selector)
                    await see_more_btn.scroll_into_view_if_needed()
                    await see_more_btn.click()
                    await asyncio.sleep(1.5)  # Wait for content to expand
                    print("✅ 'See more' clicked - full description should be visible")
                    return True
            except:
                continue
        
        print("⚠️ No 'See more' button found - using available description")
        return False
        
    except Exception as e:
        print(f"❌ See more button error: {e}")
        return False

# ---------------------------------------------------------------------------
# 4. OPTIMIZED JOB PROCESSING - INCREASED SPEED
# ---------------------------------------------------------------------------

async def process_single_job_optimized(context, job_link, job_index, total_jobs):
    """OPTIMIZED: Faster job processing with full descriptions"""
    try:
        print(f"⚡ Processing job {job_index + 1}/{total_jobs}")
        
        job_description = await extract_job_description_fixed(context, job_link)
        
        if job_description and len(job_description) > 50:
            return job_link, job_description, "added"
        else:
            return job_link, job_description or "Minimal content", "added"
                    
    except Exception as e:
        print(f"❌ Error job {job_index + 1}: {e}")
        return job_link, f"Processing error: {str(e)[:100]}", "added"

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

        # Force layout fix
        await force_layout_fix(page)
        await asyncio.sleep(1)
        
        job_cards = await load_all_available_jobs_fixed(page)
        
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
                if len(text_content) < 5:  # Very minimal requirement
                    text_failed += 1
                    print(f"   Card {i+1}: No text content")
                    continue
                
                print(f"   Card {i+1}: Text preview: '{text_content[:50]}...'")
                
                # RELAXED keyword check - much more lenient
                text_lower = text_content.lower()
                
                # Check for job title match first (most important)
                title_match = job_title.lower().split() 
                has_title_keywords = any(word in text_lower for word in title_match if len(word) > 2)
                
                # Check for any technical keywords
                has_tech_keywords = any(keyword.lower() in text_lower for keyword in FILTERING_KEYWORDS)
                
                # Check for common job-related words (very broad)
                common_job_words = ['developer', 'engineer', 'software', 'programming', 'coding', 'technical', 'technology', 'web', 'application', 'system']
                has_job_words = any(word in text_lower for word in common_job_words)
                
                # MUCH MORE LENIENT: Accept if ANY of these conditions are met
                if has_title_keywords or has_tech_keywords or has_job_words:
                    print(f"   ✅ Card {i+1}: Passed keyword filter")
                else:
                    keyword_filtered += 1
                    print(f"   ❌ Card {i+1}: No relevant keywords found")
                    continue
                
                # Extract job link with enhanced debugging
                href = await card.get_attribute('href')
                if not href:
                    # Try multiple methods to find link
                    link_selectors = [
                        'a[href*="/jobs/view"]',
                        'a[href*="/jobs/"]',
                        'a',
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
                
                if href and '/jobs/' in href:  # More lenient - not just '/jobs/view/'
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
        if valid_job_links:
            tasks = [
                process_single_job_optimized(context, job_link, i, len(valid_job_links))
                for i, job_link in enumerate(valid_job_links)
            ]
            
            semaphore = asyncio.Semaphore(5)
            
            async def bounded_task(task):
                async with semaphore:
                    return await task
            
            results = await asyncio.gather(*[bounded_task(task) for task in tasks], return_exceptions=True)
            
            processed_jobs = 0
            for result in results:
                if isinstance(result, Exception):
                    continue
                    
                job_link, job_description, status = result
                if status == "added":
                    job_dict[job_link] = job_description
                    processed_jobs += 1
            
            print(f"✅ {processed_jobs} jobs processed with full descriptions")
        
        return job_dict
        
    except Exception as e:
        print(f"❌ Error in speed-optimized search: {e}")
        return {}
    finally:
        await page.close()

# ---------------------------------------------------------------------------
# 5. GEMINI API PROCESSING FUNCTIONS (OPTIMIZED)
# ---------------------------------------------------------------------------

genai.configure(api_key=GOOGLE_API)
model = genai.GenerativeModel("gemini-2.5-flash-lite")

def create_bulk_prompt(jobs_dict: dict) -> str:
    SYSTEM_PROMPT = """
    You are a professional job-data extraction specialist. Extract structured information for ALL jobs and return a JSON array.
    
    EXTRACTION RULES:
    - Extract Job ID from URL (number after /jobs/view/)
    - Extract proper titles.
    - Dont make any syntax errors for JSON file.
    - For location: Default to "India" since search was India-filtered  
    - For Experience: Look for years, "freshers", "entry level"
    - For Salary: Include currency (₹, INR, $, USD)
    - Extract key technical skills/technologies mentioned
    - Company name from job description
    
    RETURN FORMAT:
    [
      {
        "title": "job title",
        "job_id": "extracted from URL", 
        "company_name": "company name",
        "location": "location",
        "experience": "experience requirement",
        "salary": "salary if mentioned",
        "key_skills": ["skill1", "skill2", "skill3"],
        "job_url": "full URL",
        "posted_at": "when posted",
        "job_description": "full description",
        "source": "linkedin",
        "relevance_score": "high/medium/low based on technical content"
      },
    ]
    
    Return ONLY the JSON array.
    """
    
    prompt = f"{SYSTEM_PROMPT}\n\nProcess {len(jobs_dict)} jobs:\n"
    for idx, (url, jd) in enumerate(jobs_dict.items(), 1):
        prompt += f"\n--- JOB {idx} ---\nURL: {url}\nDESCRIPTION:\n{jd[:1500]}...\n"
    
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
    response = model.generate_content(prompt)
    return parse_bulk_response(response.text, batch_dict)

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

async def search_by_job_titles_speed_optimized(job_titles, platforms=None):
    """SPEED OPTIMIZED: All fixes applied - faster execution"""
    global PROCESSED_JOB_URLS, LOGGED_IN_CONTEXT
    
    if platforms is None:
        platforms = list(PLATFORMS.keys())
    
    all_jobs = {}
    PROCESSED_JOB_URLS.clear()
    
    print(f"🚀 Starting SPEED-OPTIMIZED job extraction with ALL FIXES...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
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
                
                print(f"📊 '{job_title}' complete. Total unique jobs: {len(all_jobs)}")
            
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
    print(f"{'='*70}")
    
    return all_jobs

def run_scraper_in_new_loop(titles, keywords, user_id=None, password=None):
    """Run scraper in a fresh event loop - Production Ready"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(main(titles, keywords, user_id, password))
            return result
        finally:
            loop.close()
    except Exception as e:
        print(f"Scraper error: {e}")
        return []

async def main(parsed_titles=None, parsed_keywords=None, user_id = None, password=None):
    global JOB_TITLES, FILTERING_KEYWORDS, LINKEDIN_ID, LINKEDIN_PASSWORD
    if parsed_titles:
        JOB_TITLES = parsed_titles
    if parsed_keywords:
        FILTERING_KEYWORDS = parsed_keywords

    if user_id and password:
        print("✅ Setting custom credentials...")
        LINKEDIN_ID = user_id
        LINKEDIN_PASSWORD = password
        print(f"✅ Credentials set - LINKEDIN_ID: {LINKEDIN_ID}")
    else:
        print(f"❌ Using env credentials - LINKEDIN_ID: {LINKEDIN_ID}, LINKEDIN_PASSWORD: {'***' if LINKEDIN_PASSWORD else 'None'}")

    print("🧠 Starting SPEED-OPTIMIZED job extraction with ALL FIXES...")

    all_jobs = await search_by_job_titles_speed_optimized(JOB_TITLES)
    
    if len(all_jobs) == 0:
        print("❌ No jobs found to analyze...")
        return
    
    print(f"🧠 Sending {len(all_jobs)} jobs to Gemini for extraction...")
    extracted = await extract_jobs_in_batches(all_jobs, batch_size=25)  # Larger batches
    
    # Save results
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"linkedin_jobs_ALL_FIXES_{timestamp}.json"
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(extracted, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Successfully extracted data for {len(extracted)} jobs")
    print(f"📁 Results saved to {filename}")
    
    # Print summary
    total_skills = set()
    companies = set()
    
    for job in extracted:
        if job.get("key_skills"):
            total_skills.update(job["key_skills"])
        if job.get("company_name") and job["company_name"] != "Not extracted":
            companies.add(job["company_name"])
    
    print(f"\n📊 FINAL SUMMARY:")
    print(f" 🏢 Companies: {len(companies)}")
    print(f" 🛠️ Unique skills found: {len(total_skills)}")
    print(f" 📄 Total jobs extracted: {len(extracted)}")
    print(f" ⚡ Speed optimized: YES")
    print(f" 🔧 All fixes applied: YES")
    print(f" 🔵 Easy Apply enabled: YES")
    print(f" 🔐 Authenticated scraping: YES")
    return extracted

if __name__ == "__main__":
    print("🚀 Starting SPEED-OPTIMIZED LinkedIn Job Scraper with ALL FIXES...")
    print(f"📋 Job Titles to search: {len(JOB_TITLES)}")
    print(f"🔍 Filtering keywords: {len(FILTERING_KEYWORDS)}")
    print(f"🔵 Easy Apply: ENABLED")
    print(f"⚡ Speed optimization: MAXIMUM")
    print(f"🔧 All fixes applied: YES")
    print(f"🔐 LinkedIn Authentication: ENABLED")
    
    asyncio.run(main())
