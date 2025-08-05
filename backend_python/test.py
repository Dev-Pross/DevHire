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
    Titles are extracted from \resumeSubheading sections (the first parameter).
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
    
    # Extract from resumeSubheading - this is the job title (first parameter)
    for m in re.finditer(r"\\resumeSubheading\s*\{([^\}]*)\}", text_nocomment):
        title = m.group(1).strip()
        if title and title.lower() not in ("", "education", "mvgr college of engineering", "government polytechnic college"):
            # Clean up the title
            title = re.sub(r'\{[^}]*\}', '', title)  # Remove any nested braces
            title = title.strip()
            if title and len(title) > 3:  # Only add if it's a meaningful title
                titles.append(title)
                print(f"[RESUME] Found job title from resumeSubheading: {title}")
    
    # Remove duplicates and filter out non-job titles
    seen_titles = set()
    result_titles = []
    for t in titles:
        t_norm = t.lower()
        # Filter out education and other non-job titles
        if (t_norm not in seen_titles and 
            t_norm not in ("", "education", "mvgr college of engineering", "government polytechnic college") and
            not any(edu_word in t_norm for edu_word in ["college", "university", "school", "diploma", "b.tech", "degree"])):
            result_titles.append(t)
            seen_titles.add(t_norm)
    
    print(f"[RESUME] Final extracted job titles: {result_titles}")
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

async def debug_single_job(context, job_url):
    """
    Debug function to test scraping a single job URL.
    """
    print(f"[DEBUG] Testing single job URL: {job_url}")
    
    page = await context.new_page()
    try:
        await page.goto(job_url, wait_until="domcontentloaded")
        await asyncio.sleep(5)
        
        # Take a screenshot for debugging
        screenshot_path = "debug_job_page.png"
        await page.screenshot(path=screenshot_path)
        print(f"[DEBUG] Screenshot saved to: {screenshot_path}")
        
        # Get page title and URL
        page_title = await page.title()
        current_url = page.url
        print(f"[DEBUG] Page title: {page_title}")
        print(f"[DEBUG] Current URL: {current_url}")
        
        # Try to get any text content
        try:
            body_text = await page.locator('body').text_content()
            print(f"[DEBUG] Body text length: {len(body_text) if body_text else 0}")
            if body_text:
                print(f"[DEBUG] First 500 chars of body: {body_text[:500]}")
        except Exception as e:
            print(f"[DEBUG] Error getting body text: {e}")
        
        # Try to find any h1 elements
        try:
            h1_elements = await page.locator('h1').all()
            print(f"[DEBUG] Found {len(h1_elements)} h1 elements")
            for i, h1 in enumerate(h1_elements):
                h1_text = await h1.text_content()
                print(f"[DEBUG] H1 {i+1}: {h1_text}")
        except Exception as e:
            print(f"[DEBUG] Error getting h1 elements: {e}")
        
        # Try to find any elements with "job" in the class name
        try:
            job_elements = await page.locator('[class*="job"]').all()
            print(f"[DEBUG] Found {len(job_elements)} elements with 'job' in class name")
            for i, elem in enumerate(job_elements[:5]):  # Only first 5
                elem_text = await elem.text_content()
                elem_class = await elem.get_attribute('class')
                print(f"[DEBUG] Job element {i+1} class: {elem_class}")
                print(f"[DEBUG] Job element {i+1} text: {elem_text[:100] if elem_text else 'None'}")
        except Exception as e:
            print(f"[DEBUG] Error getting job elements: {e}")
        
    except Exception as e:
        print(f"[DEBUG] Error in debug function: {e}")
    finally:
        await page.close()

async def scrape_job_details(page, job_url):
    """
    Scrape detailed information from a single job posting page.
    """
    print(f"[DETAILS] Scraping details from: {job_url}")
    
    try:
        await page.goto(job_url, wait_until="domcontentloaded")
        await asyncio.sleep(3)  # Increased wait time
        
        job_data = {
            "url": job_url,
            "title": "",
            "company": "",
            "location": "",
            "description": "",
            "requirements": "",
            "posted_date": "",
            "job_type": "",
            "experience_level": ""
        }
        
        # Extract job title - Updated selectors
        try:
            title_selectors = [
                'h1.job-details-jobs-unified-top-card__job-title',
                '.job-details-jobs-unified-top-card__job-title',
                'h1[data-test-id="job-details-jobs-unified-top-card__job-title"]',
                '.jobs-unified-top-card__job-title',
                'h1.jobs-unified-top-card__job-title',
                '.job-details-jobs-unified-top-card__job-title h1',
                'h1',
                '.jobs-unified-top-card__job-title-text',
                '[data-test-id="job-details-jobs-unified-top-card__job-title"]'
            ]
            
            for selector in title_selectors:
                try:
                    title_elements = await page.locator(selector).all()
                    for element in title_elements:
                        title_text = await element.text_content()
                        if title_text and title_text.strip():
                            job_data["title"] = title_text.strip()
                            print(f"[DETAILS] Found title: {job_data['title']}")
                            break
                    if job_data["title"]:
                        break
                except Exception as e:
                    print(f"[DETAILS] Title selector {selector} failed: {e}")
                    continue
        except Exception as e:
            print(f"[DETAILS] Error extracting title: {e}")
        
        # Extract company name - Updated selectors
        try:
            company_selectors = [
                '.job-details-jobs-unified-top-card__company-name',
                '.jobs-unified-top-card__company-name',
                '[data-test-id="job-details-jobs-unified-top-card__company-name"]',
                '.job-details-jobs-unified-top-card__subtitle-primary-grouping',
                '.jobs-unified-top-card__subtitle-primary-grouping',
                '.job-details-jobs-unified-top-card__company-name a',
                '.jobs-unified-top-card__company-name a',
                '.job-details-jobs-unified-top-card__subtitle-primary-grouping a',
                '.jobs-unified-top-card__subtitle-primary-grouping a'
            ]
            
            for selector in company_selectors:
                try:
                    company_elements = await page.locator(selector).all()
                    for element in company_elements:
                        company_text = await element.text_content()
                        if company_text and company_text.strip():
                            job_data["company"] = company_text.strip()
                            print(f"[DETAILS] Found company: {job_data['company']}")
                            break
                    if job_data["company"]:
                        break
                except Exception as e:
                    print(f"[DETAILS] Company selector {selector} failed: {e}")
                    continue
        except Exception as e:
            print(f"[DETAILS] Error extracting company: {e}")
        
        # Extract location - Updated selectors
        try:
            location_selectors = [
                '.job-details-jobs-unified-top-card__bullet',
                '.jobs-unified-top-card__bullet',
                '[data-test-id="job-details-jobs-unified-top-card__bullet"]',
                '.job-details-jobs-unified-top-card__subtitle-primary-grouping',
                '.jobs-unified-top-card__subtitle-primary-grouping',
                '.job-details-jobs-unified-top-card__bullet span',
                '.jobs-unified-top-card__bullet span',
                '.job-details-jobs-unified-top-card__subtitle-primary-grouping span',
                '.jobs-unified-top-card__subtitle-primary-grouping span',
                '.job-details-jobs-unified-top-card__subtitle-secondary-grouping',
                '.jobs-unified-top-card__subtitle-secondary-grouping'
            ]
            
            for selector in location_selectors:
                try:
                    location_elements = await page.locator(selector).all()
                    for element in location_elements:
                        location_text = await element.text_content()
                        if location_text and location_text.strip():
                            # Check if it looks like a location
                            location_lower = location_text.lower()
                            if any(word in location_lower for word in ["remote", "hybrid", "on-site", "location", "india", "us", "uk", "new york", "california", "texas", "florida", "bangalore", "mumbai", "delhi", "pune", "chennai", "hyderabad"]):
                                job_data["location"] = location_text.strip()
                                print(f"[DETAILS] Found location: {job_data['location']}")
                                break
                            # Also check for general location patterns
                            elif any(char in location_text for char in [",", "•", "|"]) and len(location_text.strip()) > 3:
                                job_data["location"] = location_text.strip()
                                print(f"[DETAILS] Found location (pattern): {job_data['location']}")
                                break
                    if job_data["location"]:
                        break
                except Exception as e:
                    print(f"[DETAILS] Location selector {selector} failed: {e}")
                    continue
        except Exception as e:
            print(f"[DETAILS] Error extracting location: {e}")
        
        # Extract job description - Updated selectors
        try:
            description_selectors = [
                '.jobs-description__content',
                '.job-details-jobs-unified-top-card__job-description',
                '.jobs-box__html-content',
                '[data-test-id="job-details-jobs-unified-top-card__job-description"]',
                '.jobs-description',
                '.jobs-description__content .jobs-box__html-content',
                '.jobs-description__content .jobs-description__content',
                '.jobs-description__content .jobs-box__html-content .jobs-box__html-content',
                '.jobs-description__content .jobs-box__html-content .jobs-description__content',
                '.jobs-description__content .jobs-description__content .jobs-box__html-content',
                '.jobs-description__content .jobs-description__content .jobs-description__content',
                '.jobs-description__content .jobs-box__html-content .jobs-description__content .jobs-box__html-content',
                '.jobs-description__content .jobs-box__html-content .jobs-description__content .jobs-description__content',
                '.jobs-description__content .jobs-box__html-content .jobs-box__html-content',
                '.jobs-description__content .jobs-description__content .jobs-box__html-content .jobs-description__content',
                '.jobs-description__content .jobs-description__content .jobs-description__content .jobs-box__html-content',
                '.jobs-description__content .jobs-description__content .jobs-description__content .jobs-description__content'
            ]
            
            for selector in description_selectors:
                try:
                    desc_elements = await page.locator(selector).all()
                    for element in desc_elements:
                        desc_text = await element.text_content()
                        if desc_text and desc_text.strip():
                            job_data["description"] = desc_text.strip()
                            # Truncate description if too long
                            if len(job_data["description"]) > 2000:
                                job_data["description"] = job_data["description"][:2000] + "..."
                            print(f"[DETAILS] Found description (length: {len(job_data['description'])})")
                            break
                    if job_data["description"]:
                        break
                except Exception as e:
                    print(f"[DETAILS] Description selector {selector} failed: {e}")
                    continue
        except Exception as e:
            print(f"[DETAILS] Error extracting description: {e}")
        
        # Extract requirements - Updated selectors
        try:
            requirements_selectors = [
                '.jobs-description__content h3:has-text("Requirements") + ul',
                '.jobs-description__content h3:has-text("Qualifications") + ul',
                '.jobs-description__content h3:has-text("Skills") + ul',
                '.jobs-description__content h3:has-text("Requirements") + ol',
                '.jobs-description__content h3:has-text("Qualifications") + ol',
                '.jobs-description__content h3:has-text("Skills") + ol',
                '.jobs-description__content ul',
                '.jobs-description__content ol',
                '.jobs-box__html-content ul',
                '.jobs-box__html-content ol',
                '.jobs-description__content .jobs-box__html-content ul',
                '.jobs-description__content .jobs-box__html-content ol',
                '.jobs-description__content .jobs-description__content ul',
                '.jobs-description__content .jobs-description__content ol',
                '.jobs-description__content .jobs-box__html-content .jobs-box__html-content ul',
                '.jobs-description__content .jobs-box__html-content .jobs-box__html-content ol',
                '.jobs-description__content .jobs-description__content .jobs-box__html-content ul',
                '.jobs-description__content .jobs-description__content .jobs-box__html-content ol',
                '.jobs-description__content .jobs-description__content .jobs-description__content ul',
                '.jobs-description__content .jobs-description__content .jobs-description__content ol'
            ]
            
            for selector in requirements_selectors:
                try:
                    req_elements = await page.locator(selector).all()
                    for element in req_elements:
                        req_text = await element.text_content()
                        if req_text and req_text.strip():
                            job_data["requirements"] = req_text.strip()
                            if len(job_data["requirements"]) > 1000:
                                job_data["requirements"] = job_data["requirements"][:1000] + "..."
                            print(f"[DETAILS] Found requirements (length: {len(job_data['requirements'])})")
                            break
                    if job_data["requirements"]:
                        break
                except Exception as e:
                    print(f"[DETAILS] Requirements selector {selector} failed: {e}")
                    continue
        except Exception as e:
            print(f"[DETAILS] Error extracting requirements: {e}")
        
        # Try to get any text content if we haven't found description yet
        if not job_data["description"]:
            try:
                print(f"[DETAILS] Trying to get any text content from the page...")
                # Get all text content from the main content area
                main_content_selectors = [
                    'main',
                    '.jobs-description__content',
                    '.jobs-box__html-content',
                    '.jobs-description',
                    '.job-details-jobs-unified-top-card__job-description',
                    '[data-test-id="job-details-jobs-unified-top-card__job-description"]'
                ]
                
                for selector in main_content_selectors:
                    try:
                        content_elements = await page.locator(selector).all()
                        for element in content_elements:
                            content_text = await element.text_content()
                            if content_text and content_text.strip() and len(content_text.strip()) > 100:
                                job_data["description"] = content_text.strip()
                                if len(job_data["description"]) > 2000:
                                    job_data["description"] = job_data["description"][:2000] + "..."
                                print(f"[DETAILS] Found content from {selector} (length: {len(job_data['description'])})")
                                break
                        if job_data["description"]:
                            break
                    except Exception as e:
                        print(f"[DETAILS] Content selector {selector} failed: {e}")
                        continue
            except Exception as e:
                print(f"[DETAILS] Error getting general content: {e}")
        
        # Debug: Print page title and URL to see what we're actually on
        try:
            page_title = await page.title()
            current_url = page.url
            print(f"[DETAILS] Page title: {page_title}")
            print(f"[DETAILS] Current URL: {current_url}")
        except Exception as e:
            print(f"[DETAILS] Error getting page info: {e}")
        
        return job_data
        
    except Exception as e:
        print(f"[DETAILS] Error scraping job details: {e}")
        return {
            "url": job_url,
            "title": "",
            "company": "",
            "location": "",
            "description": "",
            "requirements": "",
            "posted_date": "",
            "job_type": "",
            "experience_level": "",
            "error": str(e)
        }

async def scrape_job_urls_by_titles(context, titles, max_jobs_per_title=10):
    """
    For each title, search LinkedIn jobs and return detailed job information.
    """
    print(f"[SCRAPE] Starting job scraping for titles: {titles}")
    print(f"[SCRAPE] Max jobs per title: {max_jobs_per_title}")
    
    all_jobs = {}
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
            
            # Now scrape detailed information for each job
            print(f"[SCRAPE] Scraping detailed information for {len(job_links)} jobs...")
            detailed_jobs = []
            
            for idx, job_url in enumerate(job_links):
                print(f"[SCRAPE] Scraping job {idx+1}/{len(job_links)}: {job_url}")
                job_details = await scrape_job_details(page, job_url)
                detailed_jobs.append(job_details)
                
                # Add a small delay between requests
                await asyncio.sleep(1)
            
            all_jobs[title] = detailed_jobs
            print(f"[SCRAPE] Final result for '{title}': {len(detailed_jobs)} jobs with details")
            
        except Exception as e:
            print(f"[SCRAPE] Error processing title '{title}': {e}")
            all_jobs[title] = []
    
    await page.close()
    print(f"[SCRAPE] Closed scraping page")
    return all_jobs

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
        print(f"[MAIN] Please create a .env file in the backend_python directory with:")
        print(f"[MAIN] LINKEDIN_ID=your_linkedin_email@example.com")
        print(f"[MAIN] LINKEDIN_PASSWORD=your_linkedin_password")
        return {}
    
    print(f"[MAIN] Credentials found, proceeding with scraping")
    
    # Start Playwright
    print(f"\n[MAIN] Step 3: Starting Playwright browser")
    try:
        playwright = await async_playwright().start()
        print(f"[MAIN] Playwright started successfully")
        
        browser = await playwright.chromium.launch(headless=False)  # Set to False for debugging
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
    
    # DEBUG: Test a single job URL first
    print(f"\n[MAIN] Step 5: DEBUG - Testing single job URL")
    test_job_url = "https://www.linkedin.com/jobs/view/4238704831/"
    await debug_single_job(context, test_job_url)
    
    # Scrape jobs
    print(f"\n[MAIN] Step 6: Scraping job URLs and details")
    job_data = await scrape_job_urls_by_titles(context, titles, max_jobs_per_title=3)  # Reduced to 3 for faster processing
    
    # Cleanup
    print(f"\n[MAIN] Step 7: Cleaning up resources")
    await context.close()
    await browser.close()
    await playwright.stop()
    print(f"[MAIN] Resources cleaned up")
    
    # Save results to file
    print(f"\n[MAIN] Step 8: Saving results")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"linkedin_jobs_detailed_{timestamp}.json"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(job_data, f, indent=2, ensure_ascii=False)
        print(f"[MAIN] Results saved to: {filename}")
    except Exception as e:
        print(f"[MAIN] Error saving results: {e}")
    
    return job_data

if __name__ == "__main__":
    print(f"[SCRIPT] LinkedIn Job Scraper Started")
    print(f"[SCRIPT] =================================")
    
    try:
        result = asyncio.run(main())
        
        print(f"\n[SCRIPT] =================================")
        print(f"[SCRIPT] Final Results:")
        
        if result:
            total_jobs = sum(len(jobs) for jobs in result.values())
            print(f"[SCRIPT] Total jobs found: {total_jobs}")
            
            for title, jobs in result.items():
                print(f"\n[SCRIPT] Title: {title}")
                print(f"[SCRIPT] Jobs found: {len(jobs)}")
                if jobs:
                    for idx, job in enumerate(jobs, 1):
                        print(f"[SCRIPT]   {idx}. {job.get('title', 'No title')} at {job.get('company', 'Unknown company')}")
                        if job.get('location'):
                            print(f"[SCRIPT]      Location: {job['location']}")
                        if job.get('description'):
                            desc_preview = job['description'][:100] + "..." if len(job['description']) > 100 else job['description']
                            print(f"[SCRIPT]      Description: {desc_preview}")
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

