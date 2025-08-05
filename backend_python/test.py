import asyncio
import os
import sys
import re
import json
import time
from datetime import datetime
from playwright.async_api import async_playwright

# Import config from correct location (backend_python/config.py)
sys.path.append(os.path.dirname(__file__))
try:
    from config import LINKEDIN_ID, LINKEDIN_PASSWORD
    print(f"[CONFIG] Successfully imported config")
    print(f"[CONFIG] LINKEDIN_ID: {'***' if LINKEDIN_ID else 'None'}")
    print(f"[CONFIG] LINKEDIN_PASSWORD: {'***' if LINKEDIN_PASSWORD else 'None'}")
except ImportError as e:
    print(f"[CONFIG] Error importing config: {e}")
    LINKEDIN_ID = None
    LINKEDIN_PASSWORD = None

LINKEDIN_LOGIN_URL = "https://www.linkedin.com/login"

def extract_titles_from_resume(tex_path=None):
    """
    Extract job titles from resume0.tex.
    Titles are extracted from \resumeSubheading and section headers.
    """
    print(f"[RESUME] Starting resume title extraction...")
    
    possible_paths = []
    if tex_path is not None:
        possible_paths.append(tex_path)
    else:
        possible_paths = [
            os.path.join(os.path.dirname(__file__), "resume0.tex"),
            r"D:\DevHire\backend_python\resume0.tex",
            "backend_python/resume0.tex"
        ]
    
    print(f"[RESUME] Checking possible paths: {possible_paths}")
    
    for path in possible_paths:
        if os.path.exists(path):
            tex_path = path
            print(f"[RESUME] Found resume file at: {tex_path}")
            break
    else:
        print(f"[RESUME] No resume file found in any of the paths")
        return []
    
    try:
        with open(tex_path, "r", encoding="utf-8") as f:
            text = f.read()
        print(f"[RESUME] Successfully read resume file, size: {len(text)} characters")
    except Exception as e:
        print(f"[RESUME] Error reading resume file: {e}")
        return []
    
    text_nocomment = re.sub(r"%.*", "", text)
    titles = []
    
    # Extract from resumeSubheading
    for m in re.finditer(r"\\resumeSubheading\{([^\}]*)\}", text_nocomment):
        title = m.group(1).strip()
        if title and title.lower() not in ("", "education"):
            titles.append(title)
            print(f"[RESUME] Found title from resumeSubheading: {title}")
    
    # Extract from section headers
    for m in re.finditer(r"\\section\*?\{([^\}]*)\}", text_nocomment):
        sec = m.group(1).strip()
        if sec and sec.lower() not in ("summary", "education", "skills", "projects", "additional information"):
            titles.append(sec)
            print(f"[RESUME] Found title from section: {sec}")
    
    # Remove duplicates
    seen_titles = set()
    result_titles = []
    for t in titles:
        t_norm = t.lower()
        if t_norm not in seen_titles and t_norm not in ("", "education"):
            result_titles.append(t)
            seen_titles.add(t_norm)
    
    print(f"[RESUME] Final extracted titles: {result_titles}")
    return result_titles

async def linkedin_login(page, username, password):
    """Login to LinkedIn with comprehensive logging"""
    print(f"[LOGIN] Starting LinkedIn login process...")
    print(f"[LOGIN] Username: {username}")
    print(f"[LOGIN] Password: {'***' if password else 'None'}")
    
    if not username or not password:
        print(f"[LOGIN] Missing credentials, cannot proceed")
        return False
    
    try:
        print(f"[LOGIN] Navigating to: {LINKEDIN_LOGIN_URL}")
        await page.goto(LINKEDIN_LOGIN_URL)
        print(f"[LOGIN] Successfully navigated to login page")
        
        # Wait for page to load
        await page.wait_for_load_state('domcontentloaded')
        print(f"[LOGIN] Page loaded successfully")
        
        # Fill username
        print(f"[LOGIN] Filling username field...")
        await page.fill('input#username', username)
        print(f"[LOGIN] Username filled successfully")
        
        # Fill password
        print(f"[LOGIN] Filling password field...")
        await page.fill('input#password', password)
        print(f"[LOGIN] Password filled successfully")
        
        # Click submit
        print(f"[LOGIN] Clicking submit button...")
        try:
            async with page.expect_navigation(timeout=60000):
                await page.click('button[type="submit"]')
            print(f"[LOGIN] Submit button clicked, navigation completed")
        except Exception as e:
            print(f"[LOGIN] Navigation timeout, but continuing: {e}")
            await page.click('button[type="submit"]')
        
        # Wait for page to load
        print(f"[LOGIN] Waiting for page to load...")
        try:
            await page.wait_for_load_state('networkidle', timeout=60000)
            print(f"[LOGIN] Page loaded to networkidle state")
        except Exception as e:
            print(f"[LOGIN] Networkidle timeout, trying domcontentloaded: {e}")
            try:
                await page.wait_for_load_state('domcontentloaded', timeout=30000)
                print(f"[LOGIN] Page loaded to domcontentloaded state")
            except Exception as e2:
                print(f"[LOGIN] Domcontentloaded timeout: {e2}")
        
        # Check current URL
        try:
            current_url = page.url
            print(f"[LOGIN] Current URL after login: {current_url}")
        except Exception as e:
            print(f"[LOGIN] Error getting current URL: {e}")
            return False
        
        # Check if login was successful
        if "feed" in current_url or "jobs" in current_url:
            print(f"[LOGIN] Login successful - redirected to feed/jobs")
            return True
        elif "login" in current_url:
            print(f"[LOGIN] Login failed - still on login page")
            return False
        else:
            print(f"[LOGIN] Login status unclear - URL: {current_url}")
            return True
            
    except Exception as e:
        print(f"[LOGIN] Error during login process: {e}")
        return False

async def scrape_job_urls_by_titles(context, titles, max_jobs_per_title=10):
    """
    For each title, search LinkedIn jobs and return a list of job URLs.
    """
    print(f"[SCRAPE] Starting job scraping for titles: {titles}")
    print(f"[SCRAPE] Max jobs per title: {max_jobs_per_title}")
    
    job_urls = {}
    page = await context.new_page()
    print(f"[SCRAPE] Created new page for scraping")
    
    for title in titles:
        print(f"\n[SCRAPE] Processing title: {title}")
        
        # Encode title for URL
        encoded_title = title.replace(' ', '%20')
        search_url = f"https://www.linkedin.com/jobs/search/?keywords={encoded_title}"
        print(f"[SCRAPE] Search URL: {search_url}")
        
        try:
            await page.goto(search_url, wait_until="domcontentloaded")
            print(f"[SCRAPE] Successfully navigated to search page")
            
            # Wait for page to load completely
            await asyncio.sleep(3)
            print(f"[SCRAPE] Waited 3 seconds for page load")
            
            # Scroll to load more content
            print(f"[SCRAPE] Scrolling to load more jobs...")
            for i in range(5):
                await page.mouse.wheel(0, 1000)
                await asyncio.sleep(1)
                print(f"[SCRAPE] Scroll {i+1}/5 completed")
            
            # Wait a bit more for content to load
            await asyncio.sleep(2)
            
            # Try multiple selectors to find job cards
            selectors = [
                'ul.scaffold-layout__list-container > li',
                'div.jobs-search-results-list > ul > li',
                'li.jobs-search-results__list-item',
                'li.job-search-card',
                '[data-job-id]',
                '.job-search-card',
                '.job-card-container'
            ]
            
            job_links = []
            found = False
            
            print(f"[SCRAPE] Trying different selectors to find job cards...")
            
            for selector in selectors:
                try:
                    print(f"[SCRAPE] Trying selector: {selector}")
                    await page.wait_for_selector(selector, timeout=5000)
                    cards = await page.locator(selector).all()
                    print(f"[SCRAPE] Found {len(cards)} cards with selector: {selector}")
                    
                    if cards and len(cards) > 0:
                        for idx, card in enumerate(cards[:max_jobs_per_title]):
                            try:
                                # Try different ways to get the job link
                                link_selectors = ['a', '[href*="/jobs/view/"]', '.job-card-container__link']
                                
                                for link_selector in link_selectors:
                                    try:
                                        link_node = card.locator(link_selector)
                                        if await link_node.count() > 0:
                                            job_link = await link_node.nth(0).get_attribute('href')
                                            if job_link:
                                                if job_link.startswith('/'):
                                                    job_link = f"https://www.linkedin.com{job_link}"
                                                if job_link not in job_links:
                                                    job_links.append(job_link)
                                                    print(f"[SCRAPE] Found job link {idx+1}: {job_link}")
                                                break
                                    except Exception as e:
                                        continue
                                        
                            except Exception as e:
                                print(f"[SCRAPE] Error processing card {idx}: {e}")
                                continue
                        
                        found = True
                        print(f"[SCRAPE] Successfully extracted {len(job_links)} job links with selector: {selector}")
                        break
                        
                except Exception as e:
                    print(f"[SCRAPE] Selector {selector} failed: {e}")
                    continue
            
            if not found:
                print(f"[SCRAPE] No job cards found with any selector, trying alternative approach...")
                
                # Try to get all links on the page
                try:
                    all_links = await page.locator('a[href*="/jobs/view/"]').all()
                    print(f"[SCRAPE] Found {len(all_links)} job links with href pattern")
                    
                    for idx, link in enumerate(all_links[:max_jobs_per_title]):
                        try:
                            job_link = await link.get_attribute('href')
                            if job_link:
                                if job_link.startswith('/'):
                                    job_link = f"https://www.linkedin.com{job_link}"
                                if job_link not in job_links:
                                    job_links.append(job_link)
                                    print(f"[SCRAPE] Found job link {idx+1}: {job_link}")
                        except Exception as e:
                            print(f"[SCRAPE] Error getting link attribute: {e}")
                            continue
                            
                except Exception as e:
                    print(f"[SCRAPE] Alternative approach failed: {e}")
            
            job_urls[title] = job_links
            print(f"[SCRAPE] Final result for '{title}': {len(job_links)} jobs found")
            
        except Exception as e:
            print(f"[SCRAPE] Error processing title '{title}': {e}")
            job_urls[title] = []
    
    await page.close()
    print(f"[SCRAPE] Closed scraping page")
    return job_urls

async def main():
    print(f"[MAIN] Starting LinkedIn job scraper...")
    print(f"[MAIN] Timestamp: {datetime.now()}")
    
    # Extract titles from resume
    print(f"\n[MAIN] Step 1: Extracting job titles from resume")
    resume_tex_path = None
    titles = extract_titles_from_resume(resume_tex_path)
    
    if not titles:
        print(f"[MAIN] No job titles found in resume. Exiting.")
        return {}
    
    print(f"[MAIN] Extracted {len(titles)} titles: {titles}")
    
    # Check credentials
    print(f"\n[MAIN] Step 2: Checking LinkedIn credentials")
    if LINKEDIN_ID is None or LINKEDIN_PASSWORD is None:
        print(f"[MAIN] LinkedIn credentials not found in config. Exiting.")
        return {}
    
    print(f"[MAIN] Credentials found, proceeding with scraping")
    
    # Start Playwright
    print(f"\n[MAIN] Step 3: Starting Playwright browser")
    try:
        playwright = await async_playwright().start()
        print(f"[MAIN] Playwright started successfully")
        
        browser = await playwright.chromium.launch(headless=True)
        print(f"[MAIN] Browser launched successfully")
        
        context = await browser.new_context()
        print(f"[MAIN] Browser context created")
        
    except Exception as e:
        print(f"[MAIN] Error starting Playwright: {e}")
        return {}
    
    # Login to LinkedIn
    print(f"\n[MAIN] Step 4: Logging into LinkedIn")
    page = await context.new_page()
    login_success = await linkedin_login(page, LINKEDIN_ID, LINKEDIN_PASSWORD)
    await page.close()
    
    if not login_success:
        print(f"[MAIN] LinkedIn login failed. Exiting.")
        await context.close()
        await browser.close()
        await playwright.stop()
        return {}
    
    print(f"[MAIN] LinkedIn login successful")
    
    # Scrape jobs
    print(f"\n[MAIN] Step 5: Scraping job URLs")
    job_urls = await scrape_job_urls_by_titles(context, titles, max_jobs_per_title=10)
    
    # Cleanup
    print(f"\n[MAIN] Step 6: Cleaning up resources")
    await context.close()
    await browser.close()
    await playwright.stop()
    print(f"[MAIN] Resources cleaned up")
    
    # Save results to file
    print(f"\n[MAIN] Step 7: Saving results")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"linkedin_jobs_{timestamp}.json"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(job_urls, f, indent=2, ensure_ascii=False)
        print(f"[MAIN] Results saved to: {filename}")
    except Exception as e:
        print(f"[MAIN] Error saving results: {e}")
    
    return job_urls

if __name__ == "__main__":
    print(f"[SCRIPT] LinkedIn Job Scraper Started")
    print(f"[SCRIPT] =================================")
    
    try:
        result = asyncio.run(main())
        
        print(f"\n[SCRIPT] =================================")
        print(f"[SCRIPT] Final Results:")
        
        if result:
            total_jobs = sum(len(urls) for urls in result.values())
            print(f"[SCRIPT] Total jobs found: {total_jobs}")
            
            for title, urls in result.items():
                print(f"\n[SCRIPT] Title: {title}")
                print(f"[SCRIPT] Jobs found: {len(urls)}")
                if urls:
                    for idx, url in enumerate(urls, 1):
                        print(f"[SCRIPT]   {idx}. {url}")
                else:
                    print(f"[SCRIPT]   No jobs found for this title.")
        else:
            print(f"[SCRIPT] No job URLs found.")
            
    except KeyboardInterrupt:
        print(f"\n[SCRIPT] Exiting on user interrupt.")
    except Exception as e:
        print(f"\n[SCRIPT] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"[SCRIPT] Script completed.")
