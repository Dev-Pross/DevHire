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
        "url_template": "https://www.linkedin.com/jobs/search-results/?keywords={role}&geoId=102713980&f_TPR=r86400&f_AL=true&f_SAL=f_SA_id_225001%3A272001%24f_SA_id_226001%3A274001%2C275001%2C272015&sortBy=DD",
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


def normalize_job_url(url: str) -> str:
    clean_url = (url or "").split('?')[0].strip()
    return clean_url.replace("://in.linkedin.com", "://www.linkedin.com")


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
    
    print("🔐 Starting Professional Network login...")
    
    context = await browser.new_context(**LINKEDIN_CONTEXT_OPTIONS)
    
    page = await context.new_page()
    
    try:
        await page.goto(PLATFORMS["linkedin"]["login_url"])
        await asyncio.sleep(2)

        await debug_capture_page(page, "01_login_page_loaded")
        
        # FORCE zoom that LinkedIn cannot override
        # await apply_forced_zoom(page)
        # await asyncio.sleep(3)  # Wait for zoom to apply
        
        print("✅ FORCED 50% zoom applied - Professional Network should now be zoomed out")
        
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

        await safe_close(page)
        return context
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        await safe_close(page)
        await safe_close(context)
        return None

async def ensure_logged_in(browser, user_id, linkedin_email=None, linkedin_password=None, is_connected=True):
    """Ensure we have a valid logged-in context"""
    from config import redis_client
    import json
    
    global LOGGED_IN_CONTEXT
    
    if not is_connected:
        print("🆓 FREE User detected. Using dummy global context pool.")
        from config import LINKEDIN_ID
        if not LINKEDIN_ID:
            raise Exception("LINKEDIN_ID not set in .env for dummy context.")
            
        db_context = get_linkedin_context(LINKEDIN_ID)
        if db_context:
            try:
                context = await browser.new_context(
                    storage_state=db_context,
                    **LINKEDIN_CONTEXT_OPTIONS
                )
                LOGGED_IN_CONTEXT = context
                print("✅ Dummy context loaded successfully from DB")
                return context
            except Exception as e:
                print(f"⚠️ Failed to load dummy context: {e}")
                raise Exception(f"Failed to load dummy context: {e}")
        else:
            print(f"⚠️ Dummy context for {LINKEDIN_ID} not found. Auto-initializing...")
            from config import LINKEDIN_PASSWORD, supabase
            import uuid
            
            # Ensure the user exists in the database
            user_check = supabase.table("User").select("id").eq("email", LINKEDIN_ID).execute()
            if not user_check.data:
                supabase.table("User").insert({
                    "id": str(uuid.uuid4()),
                    "email": LINKEDIN_ID,
                    "name": "Shared Pool Dummy",
                    "tier": "FREE",
                    "isConnected": True
                }).execute()
                print(f"✅ Created missing dummy user record for {LINKEDIN_ID}")
            
            if not LINKEDIN_PASSWORD:
                raise Exception("LINKEDIN_PASSWORD not set in .env! Cannot auto-initialize.")
                
            context = await linkedin_login(browser, LINKEDIN_ID, LINKEDIN_PASSWORD)
            if context:
                storage_state = await context.storage_state()
                from database.linkedin_context import save_linkedin_context
                save_linkedin_context(LINKEDIN_ID, storage_state)
                print("✅ Successfully auto-initialized and saved dummy context!")
                LOGGED_IN_CONTEXT = context
                return context
            else:
                raise Exception(f"Failed to auto-initialize dummy context. Login failed.")
    
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
                **LINKEDIN_CONTEXT_OPTIONS
            )
            print(f"✅ New context created successfully with saved state!")
            LOGGED_IN_CONTEXT = context
            return context
        except Exception as e:
            print(f"⚠️ Failed to restore context: {e}, logging in again...")
            # clear_linkedin_context(user_id)
    
    # No saved state, perform login
    if not linkedin_email or not linkedin_password:
        raise Exception("MISSING CREDENTIALS: No saved session found and no Professional Network credentials provided in the payload.")

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
    """Hybrid (Infinite Scroll + Pagination) job loading using leftmost scroll container."""
    try:
        print("🔄 Starting Hybrid (Infinite Scroll + Pagination) job loading...")
        unique_job_map = {}
        max_attempts = 5
        
        for attempt in range(max_attempts):
            print(f"📜 Processing batch/page {attempt + 1}/{max_attempts}")
            
            # 1. Scroll container to bottom to expose all items/footer
            await scroll_current_page(page)
            await asyncio.sleep(1.5)
            
            # 2. Collect current jobs from container
            current_page_jobs = await collect_jobs_from_current_page(page)
            new_jobs = 0
            for job in current_page_jobs:
                raw_url = job.get("url", "") if isinstance(job, dict) else ""
                clean_url = normalize_job_url(raw_url)
                if clean_url and clean_url not in unique_job_map:
                    unique_job_map[clean_url] = {
                        "url": clean_url,
                        "card_title": normalize_text(job.get("card_title", "")),
                    }
                    new_jobs += 1
            
            print(f"   📊 Added {new_jobs} new jobs (Total unique: {len(unique_job_map)})")
            
            # 3. Check if a visible "Next" page button exists (Account B)
            clicked_next = await page.evaluate('''
                () => {
                    const selectors = [
                        'button[aria-label*="next" i]',
                        'button.jobs-search-pagination__button--next',
                        'button:has-text("Next")',
                        'a:has-text("Next")',
                        '.artdeco-pagination__button--next'
                    ];
                    
                    for (const sel of selectors) {
                        try {
                            const btn = document.querySelector(sel);
                            if (btn && btn.offsetParent !== null && !btn.disabled && !btn.classList.contains('artdeco-button--disabled')) {
                                btn.click();
                                return true;
                            }
                        } catch(e) {}
                    }
                    
                    // Fallback text check
                    const allButtons = Array.from(document.querySelectorAll('button, a'));
                    const nextBtn = allButtons.find(el => {
                        const txt = (el.innerText || '').trim().toLowerCase();
                        return (txt === 'next' || txt.includes('next >')) && el.offsetParent !== null && !el.disabled;
                    });
                    
                    if (nextBtn) {
                        nextBtn.click();
                        return true;
                    }
                    
                    return false;
                }
            ''')
            
            if clicked_next:
                print("   🎯 Found and clicked 'Next' page button (Paginated UI detected)")
                await asyncio.sleep(2.5)  # Wait for page navigation/turn
            else:
                print("   📜 No 'Next' button found (Infinite Scroll UI detected)")
                await asyncio.sleep(1.5)  # Wait for lazy load
                
        print(f"✅ Hybrid job loading complete: {len(unique_job_map)} unique jobs collected")
        return list(unique_job_map.values())
        
    except Exception as e:
        print(f"❌ Hybrid job loading error: {e}")
        return []


async def scroll_current_page(page):
    """Scroll the leftmost scroll container to trigger lazy loading with retry for React rendering."""
    try:
        scrolled = False
        for wait_attempt in range(5):
            scrolled = await page.evaluate(r'''
                () => {
                    const scrollContainers = Array.from(document.querySelectorAll('*')).filter(el => {
                        const style = window.getComputedStyle(el);
                        const hasScrollbar = style.overflowY === 'auto' || style.overflowY === 'scroll';
                        const hasOverflowingContent = el.scrollHeight > el.clientHeight;
                        const isLargeEnough = el.clientHeight > 300;
                        return hasScrollbar && hasOverflowingContent && isLargeEnough;
                    });

                    if (scrollContainers.length > 0) {
                        scrollContainers.sort((a, b) => a.getBoundingClientRect().left - b.getBoundingClientRect().left);
                        const container = scrollContainers[0];
                        container.scrollTop = container.scrollHeight;
                        return true;
                    }
                    return false;
                }
            ''')
            if scrolled:
                print("📜 Scrolled leftmost job container to bottom")
                break
            
            # Wait 1s for React to mount container on subsequent searches
            await asyncio.sleep(1)

        if not scrolled:
            print("⚠️ No job list container found after retries, using window scroll fallback")
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
    except Exception as e:
        print(f"❌ Scroll error: {e}")


async def collect_jobs_from_current_page(page):
    """Collect all unique job URLs from the leftmost scroll container by scanning for Job IDs."""
    try:
        await page.set_viewport_size({'width': 2562, 'height': 2000})
        
        job_entries = await page.evaluate(r'''
            () => {
                const urlMap = new Map();

                const scrollContainers = Array.from(document.querySelectorAll('*')).filter(el => {
                    const style = window.getComputedStyle(el);
                    const hasScrollbar = style.overflowY === 'auto' || style.overflowY === 'scroll';
                    const hasOverflowingContent = el.scrollHeight > el.clientHeight;
                    const isLargeEnough = el.clientHeight > 300;
                    return hasScrollbar && hasOverflowingContent && isLargeEnough;
                });

                let container = document.body;
                if (scrollContainers.length > 0) {
                    scrollContainers.sort((a, b) => a.getBoundingClientRect().left - b.getBoundingClientRect().left);
                    container = scrollContainers[0];
                }

                // 1. Primary Extractor (Account B / New UI): componentkey="job-card-component-ref-<id>"
                const compCards = container.querySelectorAll('[componentkey*="job-card-component-ref-"]');
                compCards.forEach(card => {
                    const key = card.getAttribute('componentkey') || '';
                    const match = key.match(/\d{9,10}/);
                    if (match) {
                        const jobId = match[0];
                        const cleanUrl = `https://www.linkedin.com/jobs/view/${jobId}`;
                        if (!urlMap.has(cleanUrl)) {
                            const titleNode = card.querySelector('p, span, strong, h3, h4') || card;
                            const cardTitle = (titleNode.textContent || '').trim();
                            urlMap.set(cleanUrl, {
                                url: cleanUrl,
                                card_title: cardTitle || "Title not extracted"
                            });
                        }
                    }
                });

                // 2. Fallback Extractor: data-job-id, data-entity-urn, href containing currentJobId or /jobs/view/
                const fallbackNodes = container.querySelectorAll('[data-job-id], [data-occludable-job-id], [data-entity-urn], a[href]');
                fallbackNodes.forEach(node => {
                    let jobId = null;
                    const attrs = ['data-job-id', 'data-occludable-job-id', 'data-entity-urn', 'href'];
                    for (const attr of attrs) {
                        const val = node.getAttribute(attr) || '';
                        if (val && !val.includes('geoId') && !val.includes('f_SAL')) {
                            const match = val.match(/currentJobId=(\d+)/) || val.match(/\/jobs\/view\/(\d+)/) || val.match(/\b\d{9,10}\b/);
                            if (match) {
                                const found = match[1] || match[0];
                                if (found !== '102713980') {
                                    jobId = found;
                                    break;
                                }
                            }
                        }
                    }
                    if (jobId) {
                        const cleanUrl = `https://www.linkedin.com/jobs/view/${jobId}`;
                        if (!urlMap.has(cleanUrl)) {
                            const titleNode = node.querySelector('strong, h3, h4, span') || node;
                            const cardTitle = (titleNode.textContent || '').trim();
                            urlMap.set(cleanUrl, {
                                url: cleanUrl,
                                card_title: cardTitle || "Title not extracted"
                            });
                        }
                    }
                });

                return Array.from(urlMap.values());
            }
        ''')
        
        print(f"✅ Extracted {len(job_entries)} job URLs from container")
        return job_entries
    except Exception as e:
        print(f"❌ Error collecting jobs from page: {e}")
        return []


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

    # 1. Classname-based Selector Extraction
    description = ""
    for selector in [
        'div.show-more-less-html__markup',
        'section.show-more-less-html',
        'div.jobs-description__content',
        '#job-details',
        'div.description__text',
        'div.decorated-job-posting__details',
        '.jobs-box__html-content',
        '.core-section-container__content',
        '.description__text--rich',
        'article',
    ]:
        node = soup.select_one(selector)
        if node:
            text_val = normalize_text(node.get_text(" ", strip=True))
            if text_val and len(text_val) > 30:
                description = text_val
                break

    # 2. Text-Based Evidence Extraction (Header Anchor Search: "About the job", "Responsibilities", etc.)
    if not description:
        keywords = ["about the job", "job description", "about the role", "role description", "responsibilities", "what you'll do", "summary"]
        for tag in soup.find_all(['h2', 'h3', 'h4', 'h5', 'strong', 'b', 'span', 'header']):
            h_text = tag.get_text(" ", strip=True).lower()
            if any(k in h_text for k in keywords):
                parent = tag.parent
                if parent:
                    p_text = normalize_text(parent.get_text(" ", strip=True))
                    if len(p_text) > 60:
                        description = p_text
                        break
                sibling = tag.find_next_sibling()
                if sibling:
                    s_text = normalize_text(sibling.get_text(" ", strip=True))
                    if len(s_text) > 60:
                        description = s_text
                        break

    # 3. Semantic Text-Block Fallback (Looking for Job Requirement Clues)
    if not description:
        for block in soup.find_all(['div', 'section', 'article']):
            b_text = normalize_text(block.get_text(" ", strip=True))
            lower_b = b_text.lower()
            if len(b_text) > 150 and any(k in lower_b for k in ['responsibilities', 'qualifications', 'requirements', 'about the role', 'experience with', 'we are looking for']):
                description = b_text
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
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
    }
    
    await asyncio.sleep(0.5)
    
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
                    if response.status == 400:
                        try:
                            async with aiohttp.ClientSession() as clean_session:
                                async with clean_session.get(url, headers={"User-Agent": headers["User-Agent"]}, timeout=aiohttp.ClientTimeout(total=15)) as fallback_resp:
                                    if fallback_resp.status == 200:
                                        fallback_html = await fallback_resp.text()
                                        meta = extract_job_metadata_from_html(fallback_html, fallback_title=fallback_title)
                                        if meta.get("job_description"):
                                            print("   ✅ Extracted metadata via fallback clean session!")
                                            return meta
                        except Exception:
                            pass

                    if attempt < max_retries - 1:
                        sleep_time = 5 if response.status == 429 else 2
                        if response.status == 429:
                            print(f"   ⏳ HTTP 429 Rate Limit hit! Cooling down for {sleep_time}s...")
                        await asyncio.sleep(sleep_time)
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


async def scrape_platform_speed_optimized(context, platform_name, config, job_title, user_id, is_connected=True):
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
        
        # Retry loop for navigation to handle transient HTTP 429 blocks
        for nav_attempt in range(2):
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                break
            except Exception as nav_err:
                if nav_attempt == 0:
                    print(f"⚠️ Page navigation hit rate limit ({nav_err}). Retrying after 5s cooldown...")
                    await asyncio.sleep(5)
                else:
                    raise nav_err

        print("✅ Navigation complete. Waiting for React SPA container mounting...")
        await asyncio.sleep(2.5)  # Give React SPA time to mount search results container

        current_url = page.url
        if "login" in current_url or "signup" in current_url or "authwall" in current_url:
            print("🚨 AUTHENTICATION WALL DETECTED!")
            if not is_connected:
                from config import redis_client
                import requests
                if redis_client:
                    redis_client.set("free_queue_status", "paused")
                
                # Admin webhook notification (example)
                admin_webhook = os.getenv("ADMIN_WEBHOOK_URL")
                if admin_webhook:
                    try:
                        requests.post(admin_webhook, json={"alert": "Professional Network Dummy Account Logged Out!"})
                    except:
                        pass
                print("⚠️ Queue paused. Admin intervention required to update dummy context.")
            raise Exception("Auth wall detected - scraping aborted")
        
        # await apply_forced_zoom(page)
        # await asyncio.sleep(1)
        await debug_capture_page(page, "05_search_results", job_title)

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
        
        print(f"\n📊 FILTERING SUMMARY:")
        print(f"   📁 Total URLs collected: {len(job_cards)}")
        print(f"   ✅ Valid jobs: {len(valid_job_links)}")
        print(f"   🔄 Duplicates skipped: {duplicate_count}")
        
        # Fetch descriptions for current job title immediately
        if valid_job_links:
            print(f"✅ {len(valid_job_links)} jobs ready for OPTIMIZED processing with aiohttp...")
            
            connector = aiohttp.TCPConnector(limit=3)  # Polite 3 concurrent connections
            async with aiohttp.ClientSession(connector=connector) as session:
                batch_size = 10
                
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
                    
                    for job_entry, raw_payload in zip(batch_urls, batch_results):
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
                                "source": "web",
                            }

                    if i + batch_size < len(valid_job_links):
                        print(f"   ⏳ Cooldown delay (2s) before next batch...")
                        await asyncio.sleep(2.0)

            successful_urls = set(job_dict.keys())
            failed_urls = [job['url'] for job in valid_job_links if job['url'] not in successful_urls]
            if failed_urls:
                PROCESSED_JOB_URLS.difference_update(set(failed_urls))
                print(f"   ⚠️ Removed {len(failed_urls)} failed URLs from processed set")

        return job_dict
        
    except Exception as e:
        print(f"❌ Error in speed-optimized search: {e}")
        return {}
    finally:
        if page:
            await safe_close(page)

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
        "source": "web",
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
        "job_id": str(uuid.uuid4()),
        "company_name": raw_job.get("company_name") if has_meaningful_value(raw_job.get("company_name")) else normalize_text(llm_job.get("company_name")) or "Company not extracted",
        "location": raw_job.get("location") if has_meaningful_value(raw_job.get("location")) else normalize_text(llm_job.get("location")) or "Not specified",
        "experience": normalize_text(llm_job.get("experience")) or "Not specified",
        "salary": normalize_text(llm_job.get("salary")) or "Not specified",
        "key_skills": coerce_list(llm_job.get("key_skills")),
        "job_url": raw_job.get("job_url"),
        "posted_at": raw_job.get("posted_at") if has_meaningful_value(raw_job.get("posted_at")) else normalize_text(llm_job.get("posted_at")) or "Not specified",
        "job_description": raw_job.get("job_description") or "Description not available",
        "source": "web",
        "relevance_score": normalize_text(llm_job.get("relevance_score")) or "unknown",
        "job_type": raw_job.get("job_type") if has_meaningful_value(raw_job.get("job_type")) else normalize_text(llm_job.get("job_type")) or "",
    }

    if not merged["key_skills"] and isinstance(raw_job.get("key_skills"), list):
        merged["key_skills"] = raw_job.get("key_skills")

    return merged


def create_bulk_prompt(jobs_dict: dict) -> str:
    system_instruction = """
You are a professional job-data extraction specialist. Extract precisely the requested job titles and keywords.
- Extract and output all the following fields exactly as named: "title", "company_name", "location", "experience", "salary", "key_skills", "job_url", "posted_at", "job_description", "source", "relevance_score", "job_type".
- Do NOT extract or return a job_id. It will be generated automatically.
- If a field is not found in the raw text, output null or an empty string, do not hallucinate data.
- You will receive known_metadata from Playwright scraping. Treat known_metadata as source of truth.
- If a known_metadata field has a value, DO NOT overwrite it. Keep it unchanged.
- Focus on filling missing fields from job_description, especially: experience, salary, key_skills, relevance_score.
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
    "source": "web",
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
            print(f"AI - ({choose_model}) attempt {attempt}/5")
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

async def search_by_job_titles_speed_optimized(job_titles, platforms=None, log_callback=None, user_id=None, linkedin_email=None, linkedin_password=None, is_connected=True):
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
    
    print(f"🚀 Starting SPEED-OPTIMIZED job extraction with PER-TITLE PROGRESS UPDATES...")
    
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
                log_callback({"progress": 12, "status": "searching", "message": "Connecting to job servers..."})
            print("Performing server login...")
            login_context = await ensure_logged_in(browser, user_id, linkedin_email, linkedin_password, is_connected)
            
            if login_context is None:
                print("Failed to login to server. Exiting...")
                if log_callback:
                    log_callback({"progress": -1, "status": "error", "message": "Server login failed. Please review credentials."})
                return {}
            
            print("Successfully logged in to server!")
            if log_callback:
                log_callback({"progress": 15, "status": "searching", "message": "Server session ready"})
            
            # PER-TITLE PIPELINE: Search Title -> Fetch Descriptions -> Progress Update -> Next Title
            for i, job_title in enumerate(sanitized_titles, 1):
                print(f"\n{'='*70}")
                print(f"⚡ SPEED-OPTIMIZED SEARCH {i}/{len(sanitized_titles)}: '{job_title}'")
                print(f"🔢 Processed URLs so far: {len(PROCESSED_JOB_URLS)}")
                print(f"{'='*70}")
                
                title_result = {}
                for platform_name in platforms:
                    try:
                        result = await scrape_platform_speed_optimized(
                            login_context, platform_name, PLATFORMS[platform_name], job_title, user_id, is_connected
                        )
                        if isinstance(result, dict):
                            title_result.update(result)
                            all_jobs.update(result)
                        print(f"📈 Jobs from '{job_title}': {len(result)}")
                    except Exception as e:
                        print(f"❌ Error searching '{job_title}' on {platform_name}: {e}")
                    
                    await asyncio.sleep(1.0)
                
                current_percent = int(15 + (i / len(sanitized_titles)) * 70)  # range 15-85
                if log_callback:
                    log_callback({"progress": current_percent, "status": "searching", "message": f"Found {len(title_result)} {job_title} jobs"})
                if not title_result:
                    print(f"⚠️ No jobs retained after filters for '{job_title}'")
                print(f"📊 '{job_title}' complete. Total unique jobs extracted so far: {len(all_jobs)}")

                # Cooldown pause between job title searches to prevent Playwright goto ERR_HTTP_RESPONSE_CODE_FAILURE
                if i < len(sanitized_titles):
                    print("⏳ Cooling down 3.0s before next job title search...")
                    await asyncio.sleep(3.0)

        finally:
            if LOGGED_IN_CONTEXT:
                try:
                    await safe_close(LOGGED_IN_CONTEXT)
                    print("="*70)
                    print(f"context has been closed")
                    print("="*70)
                except Exception as e:
                    print(f"⚠️ Error closing context: {e}")
            await safe_close(browser)

    print(f"\n{'='*70}")
    print(f"🏆 SPEED-OPTIMIZED EXTRACTION COMPLETE!")
    print(f"📊 Total unique jobs extracted: {len(all_jobs)}")
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
        
        state = {"lock_released": False}
        try:
            loop.run_until_complete(_async_scraper_pipeline(job_id, job_data, log_callback, state))
        finally:
            loop.close()
            
            # Queue webhook trigger in the finally block only if not already released early
            if not state.get("lock_released"):
                user_id = job_data.get("user_id")
                if user_id:
                    from config import supabase, redis_client
                    import requests, threading
                    try:
                        user_res = supabase.table("User").select("\"isConnected\"").eq("id", user_id).execute()
                        if user_res.data and not user_res.data[0].get("isConnected"):
                            if redis_client:
                                redis_client.delete("dummy_account_lock")
                                
                                qstash_token = os.getenv("QSTASH_TOKEN")
                                qstash_base_url = os.getenv("QSTASH_URL", "https://qstash.upstash.io")
                                qstash_url = qstash_base_url if "/v2/publish" in qstash_base_url else f"{qstash_base_url.rstrip('/')}/v2/publish"
                                backend_url = os.getenv("BACKEND_PUBLIC_URL", "http://localhost:8000")
                                trigger_url = f"{backend_url}/api/jobs/trigger-next-queue"
                                
                                if qstash_token and backend_url:
                                    import random
                                    delay_s = random.randint(25, 45)
                                    headers = {
                                        "Authorization": f"Bearer {qstash_token}",
                                        "Upstash-Delay": f"{delay_s}s",
                                        "Content-Type": "application/json"
                                    }
                                    try:
                                        res = requests.post(f"{qstash_url}/{trigger_url}", headers=headers, json={}, timeout=5)
                                        res.raise_for_status()
                                        print(f"✅ Scheduled next queue trigger via QStash in finally block ({delay_s}s). MessageId: {res.json().get('messageId')}")
                                    except Exception as e:
                                        print(f"⚠️ QStash scheduling failed in finally block: {e}. Falling back to local timer.")
                                        def _trigger():
                                            try: requests.post(trigger_url, timeout=5)
                                            except: pass
                                        threading.Timer(float(delay_s), _trigger).start()
                                else:
                                    import random
                                    delay_s = random.randint(25, 45)
                                    print(f"No QStash token; using local {delay_s}s timer for queue.")
                                    def _trigger():
                                        try: requests.post(trigger_url, timeout=5)
                                        except: pass
                                    threading.Timer(float(delay_s), _trigger).start()
                    except Exception as e:
                        print(f"Error in finally block queue trigger: {e}")

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise e

async def safe_close(object, timeout=3.0):
    if not object:
        return
    try:
        await asyncio.wait_for(object.close(), timeout=timeout)
    except asyncio.TimeoutError:
        print("⚠️ Timeout while closing Playwright object. Forcefully bypassing.")
    except Exception as e:
        print(f"⚠️ Error while closing Playwright object: {e}")


async def _async_scraper_pipeline(job_id: str, job_data: dict, log_callback, state: dict):
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
        user_res = supabase.table("User").select("user_data, resume_url, \"isConnected\"").eq("id", user_id).execute()
        if not user_res.data:
            raise Exception("User not found in DB")
            
        user_record = user_res.data[0]
        user_data_parsed = user_record.get("user_data")
        is_connected = bool(user_record.get("isConnected", False))
        
        if not user_data_parsed:
            log_callback({"progress": 15, "status": "in_progress", "message": "Parsing resume using AI..."})
            
            # The active resume URL is passed from the frontend payload or DB fallback
            resume_url = input_data.get("resume_url") or user_record.get("resume_url")
            if not resume_url:
                raise Exception("No resume URL available for parsing")
                
            user_data_parsed = parse_main(resume_url)
            
            # Preserve old cached_answers if they exist so the Applier Agent remains smart
            if user_record and user_record.get("user_data") and isinstance(user_record.get("user_data"), dict):
                old_cache = user_record["user_data"].get("cached_answers", {})
                if old_cache:
                    user_data_parsed["cached_answers"] = old_cache
            
            # Save fresh parse result and active URL back to DB
            supabase.table("User").update({
                "user_data": user_data_parsed,
                "resume_url": resume_url
            }).eq("id", user_id).execute()
        
        titles = user_data_parsed.get("titles", [])
        
        # Phase 3: Playwright Scraping
        log_callback({"progress": 20, "status": "in_progress", "message": "Connecting to server and searching for jobs..."})
        
        # Extract credentials from payload
        l_email = input_data.get("linkedin_id")
        l_pass = input_data.get("linkedin_password")
        
        raw_jobs = await search_by_job_titles_speed_optimized(titles, log_callback=log_callback, user_id=email, linkedin_email=l_email, linkedin_password=l_pass, is_connected=is_connected)
        
        # Playwright phase complete. Release the lock and trigger the next job early so they can scrape in parallel.
        if not is_connected:
            from config import redis_client
            import requests, threading
            try:
                if redis_client:
                    redis_client.delete("dummy_account_lock")
                    state["lock_released"] = True
                    print("🔓 Released dummy lock early after Playwright phase")
                    
                    qstash_token = os.getenv("QSTASH_TOKEN")
                    qstash_base_url = os.getenv("QSTASH_URL", "https://qstash.upstash.io")
                    qstash_url = qstash_base_url if "/v2/publish" in qstash_base_url else f"{qstash_base_url.rstrip('/')}/v2/publish"
                    backend_url = os.getenv("BACKEND_PUBLIC_URL", "http://localhost:8000")
                    trigger_url = f"{backend_url}/api/jobs/trigger-next-queue"
                    
                    if qstash_token and backend_url:
                        import random
                        delay_s = random.randint(25, 45)
                        headers = {
                            "Authorization": f"Bearer {qstash_token}",
                            "Upstash-Delay": f"{delay_s}s",
                            "Content-Type": "application/json"
                        }
                        try:
                            res = requests.post(f"{qstash_url}/{trigger_url}", headers=headers, json={}, timeout=5)
                            res.raise_for_status()
                            print(f"✅ Scheduled next queue trigger via QStash ({delay_s}s). MessageId: {res.json().get('messageId')}")
                        except Exception as e:
                            print(f"⚠️ QStash scheduling failed: {e}. Falling back to local {delay_s}s timer.")
                            def _trigger():
                                try: requests.post(trigger_url, timeout=5)
                                except: pass
                            threading.Timer(float(delay_s), _trigger).start()
                    else:
                        import random
                        delay_s = random.randint(25, 45)
                        print(f"No QStash token; using local {delay_s}s timer for queue.")
                        def _trigger():
                            try: requests.post(trigger_url, timeout=5)
                            except: pass
                        threading.Timer(float(delay_s), _trigger).start()
            except Exception as e:
                print(f"Error releasing lock early: {e}")
        
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
        log_callback({"progress": 50, "status": "in_progress", "message": f"Saved {len(raw_jobs)} raw descriptions. Triggering AI categorization."})
        
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
