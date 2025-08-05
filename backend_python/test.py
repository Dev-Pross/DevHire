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

# Default job titles to search
DEFAULT_JOB_TITLES = [
    "Full Stack Developer",
    "Frontend Developer", 
    "Backend Developer",
    "Software Engineer",
    "React Developer",
    "JavaScript Developer",
    "Node.js Developer",
    "Web Developer"
]

# Default keywords for filtering
DEFAULT_FILTERING_KEYWORDS = [
    "React.js", "JavaScript", "Node.js", "Express.js", "HTML", "CSS",
    "Bootstrap", "Java", "MySQL", "SQLite", "MongoDB", "JWT Token",
    "REST API", "Android Development", "Linux", "GitHub", "Git",
    "AI", "Machine Learning", "Data Structures", "Algorithms",
    "Python", "Spring Boot", "TypeScript"
]

def get_job_titles_and_keywords(custom_titles=None, custom_keywords=None):
    """
    Get job titles and keywords, using custom inputs if provided, otherwise using defaults.
    """
    print(f"[INPUT] Processing job titles and keywords...")
    
    # Use custom titles if provided, otherwise use defaults
    job_titles = custom_titles if custom_titles is not None else DEFAULT_JOB_TITLES
    filtering_keywords = custom_keywords if custom_keywords is not None else DEFAULT_FILTERING_KEYWORDS
    
    print(f"[INPUT] Using {len(job_titles)} job titles: {job_titles}")
    print(f"[INPUT] Using {len(filtering_keywords)} filtering keywords: {filtering_keywords}")
    
    return job_titles, filtering_keywords

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

async def scrape_job_details_fast(page, job_url):
    """
    Fast version of job details scraping with optimized selectors and minimal waits.
    """
    try:
        await page.goto(job_url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)  # Increased wait time for better loading
        
        # Wait for content to load
        try:
            await page.wait_for_selector('h1, .jobs-unified-top-card__job-title, .job-details-jobs-unified-top-card__job-title', timeout=10000)
        except Exception:
            pass  # Continue even if specific elements don't load
        
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
        
        # Get page title first as fallback
        try:
            page_title = await page.title()
            if page_title and " - " in page_title:
                # LinkedIn job titles often appear as "Job Title - Company - LinkedIn"
                title_parts = page_title.split(" - ")
                if len(title_parts) >= 2:
                    job_data["title"] = title_parts[0].strip()
                    if not job_data["company"] and len(title_parts) >= 2:
                        job_data["company"] = title_parts[1].strip()
        except Exception:
            pass
        
        # Comprehensive title extraction with multiple strategies
        title_selectors = [
            'h1.job-details-jobs-unified-top-card__job-title',
            '.jobs-unified-top-card__job-title',
            'h1[data-test-id="job-details-jobs-unified-top-card__job-title"]',
            '.job-details-jobs-unified-top-card__job-title',
            'h1',
            '.jobs-unified-top-card__job-title-text',
            '[data-test-id="job-details-jobs-unified-top-card__job-title"]',
            '.job-details-jobs-unified-top-card__job-title h1',
            '.jobs-unified-top-card__job-title h1',
            'h1.jobs-unified-top-card__job-title',
            '.job-details-jobs-unified-top-card__job-title-text',
            '.jobs-unified-top-card__job-title-text'
        ]
        
        for selector in title_selectors:
            try:
                elements = await page.locator(selector).all()
                for element in elements:
                    title_text = await element.text_content()
                    if title_text and title_text.strip() and len(title_text.strip()) > 3:
                        job_data["title"] = title_text.strip()
                        break
                if job_data["title"]:
                    break
            except Exception:
                continue
        
        # Comprehensive company extraction
        company_selectors = [
            '.job-details-jobs-unified-top-card__company-name',
            '.jobs-unified-top-card__company-name',
            '[data-test-id="job-details-jobs-unified-top-card__company-name"]',
            '.job-details-jobs-unified-top-card__subtitle-primary-grouping',
            '.jobs-unified-top-card__subtitle-primary-grouping',
            '.job-details-jobs-unified-top-card__company-name a',
            '.jobs-unified-top-card__company-name a',
            '.job-details-jobs-unified-top-card__subtitle-primary-grouping a',
            '.job-details-jobs-unified-top-card__subtitle-primary-grouping a',
            '.job-details-jobs-unified-top-card__subtitle-secondary-grouping',
            '.jobs-unified-top-card__subtitle-secondary-grouping'
        ]
        
        for selector in company_selectors:
            try:
                elements = await page.locator(selector).all()
                for element in elements:
                    company_text = await element.text_content()
                    if company_text and company_text.strip() and len(company_text.strip()) > 2:
                        # Filter out location-like text
                        company_lower = company_text.lower()
                        if not any(word in company_lower for word in ["remote", "hybrid", "on-site", "india", "us", "uk", "bangalore", "mumbai", "delhi", "new york", "california"]):
                            job_data["company"] = company_text.strip()
                            break
                if job_data["company"]:
                    break
            except Exception:
                continue
        
        # Comprehensive location extraction
        location_selectors = [
            '.job-details-jobs-unified-top-card__bullet',
            '.jobs-unified-top-card__bullet',
            '[data-test-id="job-details-jobs-unified-top-card__bullet"]',
            '.job-details-jobs-unified-top-card__subtitle-primary-grouping',
            '.jobs-unified-top-card__subtitle-primary-grouping',
            '.job-details-jobs-unified-top-card__bullet span',
            '.job-details-jobs-unified-top-card__bullet span',
            '.job-details-jobs-unified-top-card__subtitle-primary-grouping span',
            '.job-details-jobs-unified-top-card__subtitle-primary-grouping span',
            '.job-details-jobs-unified-top-card__subtitle-secondary-grouping',
            '.job-details-jobs-unified-top-card__subtitle-secondary-grouping'
        ]
        
        for selector in location_selectors:
            try:
                elements = await page.locator(selector).all()
                for element in elements:
                    location_text = await element.text_content()
                    if location_text and location_text.strip():
                        location_lower = location_text.lower()
                        # Check for location indicators
                        if any(word in location_lower for word in ["remote", "hybrid", "on-site", "india", "us", "uk", "bangalore", "mumbai", "delhi", "new york", "california", "texas", "florida", "pune", "chennai", "hyderabad"]):
                            job_data["location"] = location_text.strip()
                            break
                        # Also check for general location patterns
                        elif any(char in location_text for char in [",", "•", "|"]) and len(location_text.strip()) > 3:
                            job_data["location"] = location_text.strip()
                            break
                if job_data["location"]:
                    break
            except Exception:
                continue
        
        # Comprehensive description extraction with multiple strategies
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
            '.jobs-description__content .jobs-description__content .jobs-description__content'
        ]
        
        for selector in description_selectors:
            try:
                elements = await page.locator(selector).all()
                for element in elements:
                    desc_text = await element.text_content()
                    if desc_text and desc_text.strip() and len(desc_text.strip()) > 100:
                        job_data["description"] = desc_text.strip()
                        if len(job_data["description"]) > 2000:  # Increased length
                            job_data["description"] = job_data["description"][:2000] + "..."
                        break
                if job_data["description"]:
                    break
            except Exception:
                continue
        
        # If still no description, try getting any substantial text content
        if not job_data["description"]:
            try:
                # Try to get content from main areas
                main_selectors = [
                    'main',
                    '.jobs-description__content',
                    '.jobs-box__html-content',
                    '.jobs-description',
                    '.job-details-jobs-unified-top-card__job-description',
                    '[data-test-id="job-details-jobs-unified-top-card__job-description"]',
                    '.jobs-description__content .jobs-box__html-content',
                    '.jobs-description__content .jobs-description__content'
                ]
                
                for selector in main_selectors:
                    try:
                        elements = await page.locator(selector).all()
                        for element in elements:
                            content_text = await element.text_content()
                            if content_text and content_text.strip() and len(content_text.strip()) > 200:
                                job_data["description"] = content_text.strip()
                                if len(job_data["description"]) > 2000:
                                    job_data["description"] = job_data["description"][:2000] + "..."
                                break
                        if job_data["description"]:
                            break
                    except Exception:
                        continue
            except Exception:
                pass
        
        # Try to extract requirements if description is available
        if job_data["description"]:
            try:
                # Look for requirements sections in the description
                desc_lower = job_data["description"].lower()
                requirements_keywords = ["requirements:", "qualifications:", "skills:", "requirements", "qualifications", "skills"]
                
                for keyword in requirements_keywords:
                    if keyword in desc_lower:
                        # Try to extract the section after the keyword
                        start_idx = desc_lower.find(keyword)
                        if start_idx != -1:
                            # Get text after the keyword
                            requirements_text = job_data["description"][start_idx:start_idx + 500]
                            if requirements_text:
                                job_data["requirements"] = requirements_text.strip()
                                if len(job_data["requirements"]) > 1000:
                                    job_data["requirements"] = job_data["requirements"][:1000] + "..."
                                break
            except Exception:
                pass
        
        # Debug: Print what we found
        print(f"[DETAILS] URL: {job_url}")
        print(f"[DETAILS] Title: {job_data['title']}")
        print(f"[DETAILS] Company: {job_data['company']}")
        print(f"[DETAILS] Location: {job_data['location']}")
        print(f"[DETAILS] Description length: {len(job_data['description'])}")
        
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

async def scrape_job_urls_fast(context, titles, max_jobs_per_title=15):
    """
    Enhanced job URL scraping with comprehensive search to find ALL available jobs.
    Increased default to 15 jobs per title to ensure we capture everything.
    """
    print(f"[SCRAPE] Starting comprehensive job scraping for titles: {titles}")
    print(f"[SCRAPE] Max jobs per title: {max_jobs_per_title}")
    print(f"[SCRAPE] Expected total jobs: {len(titles) * max_jobs_per_title}")
    
    all_jobs = {}
    
    # Process titles in parallel
    async def process_title(title):
        print(f"[SCRAPE] Processing title: {title}")
        
        page = await context.new_page()
        try:
            # Encode title for URL
            encoded_title = title.replace(' ', '%20')
            search_url = f"https://www.linkedin.com/jobs/search/?keywords={encoded_title}"
            
            await page.goto(search_url, wait_until="domcontentloaded")
            await asyncio.sleep(3)  # Increased wait time for better loading
            
            # Multiple scrolls to load more content
            for scroll in range(3):
                await page.mouse.wheel(0, 3000)
                await asyncio.sleep(1)
            
            # Try to get job links with comprehensive approach
            job_links = []
            
            # Comprehensive selectors to find ALL job cards
            selectors = [
                'ul.scaffold-layout__list-container > li',
                'li.jobs-search-results__list-item',
                '[data-job-id]',
                '.jobs-search-results__list-item',
                '.scaffold-layout__list-container li',
                '.jobs-search-results__list-item',
                '.jobs-search-results__list-item a',
                'a[href*="/jobs/view/"]',
                '.job-search-card',
                '.job-search-card a',
                '.job-card-container',
                '.job-card-container a'
            ]
            
            # Try multiple approaches to find ALL job links
            for selector in selectors:
                try:
                    cards = await page.locator(selector).all()
                    if cards and len(cards) > 0:
                        print(f"[SCRAPE] Found {len(cards)} elements with selector: {selector}")
                        for card in cards[:max_jobs_per_title * 2]:  # Get more to ensure we have enough
                            try:
                                # Try to find links within the card
                                link_selectors = ['a', 'a[href*="/jobs/view/"]', 'a[href*="/jobs/"]']
                                for link_selector in link_selectors:
                                    try:
                                        link_nodes = card.locator(link_selector).all()
                                        for link_node in link_nodes:
                                            job_link = await link_node.get_attribute('href')
                                            if job_link and '/jobs/view/' in job_link:
                                                if job_link.startswith('/'):
                                                    job_link = f"https://www.linkedin.com{job_link}"
                                                if job_link not in job_links:
                                                    job_links.append(job_link)
                                                    if len(job_links) >= max_jobs_per_title:
                                                        break
                                        if len(job_links) >= max_jobs_per_title:
                                            break
                                    except Exception:
                                        continue
                                if len(job_links) >= max_jobs_per_title:
                                    break
                            except Exception:
                                continue
                        if len(job_links) >= max_jobs_per_title:
                            break
                except Exception as e:
                    print(f"[SCRAPE] Error with selector {selector}: {e}")
                    continue
            
            # If still not enough links, try direct link extraction
            if len(job_links) < max_jobs_per_title:
                try:
                    print(f"[SCRAPE] Trying direct link extraction...")
                    all_links = await page.locator('a[href*="/jobs/view/"]').all()
                    print(f"[SCRAPE] Found {len(all_links)} direct job links")
                    for link in all_links[:max_jobs_per_title * 2]:
                        job_link = await link.get_attribute('href')
                        if job_link and '/jobs/view/' in job_link:
                            if job_link.startswith('/'):
                                job_link = f"https://www.linkedin.com{job_link}"
                            if job_link not in job_links:
                                job_links.append(job_link)
                                if len(job_links) >= max_jobs_per_title:
                                    break
                except Exception as e:
                    print(f"[SCRAPE] Error in direct link extraction: {e}")
            
            # Try one more approach - look for any job-related links
            if len(job_links) < max_jobs_per_title:
                try:
                    print(f"[SCRAPE] Trying comprehensive link search...")
                    all_links = await page.locator('a').all()
                    for link in all_links:
                        try:
                            href = await link.get_attribute('href')
                            if href and '/jobs/view/' in href:
                                if href.startswith('/'):
                                    href = f"https://www.linkedin.com{href}"
                                if href not in job_links:
                                    job_links.append(href)
                                    if len(job_links) >= max_jobs_per_title:
                                        break
                        except Exception:
                            continue
                except Exception as e:
                    print(f"[SCRAPE] Error in comprehensive link search: {e}")
            
            # Try to get more jobs by clicking "See more jobs" or pagination
            if len(job_links) < max_jobs_per_title:
                try:
                    print(f"[SCRAPE] Trying to load more jobs...")
                    # Look for "See more jobs" button or pagination
                    more_selectors = [
                        'button[aria-label*="See more jobs"]',
                        'button[aria-label*="Load more"]',
                        '.infinite-scroller__show-more-button',
                        'button:has-text("See more jobs")',
                        'button:has-text("Load more")',
                        '.artdeco-pagination__button--next',
                        'button[aria-label="Next"]'
                    ]
                    
                    for more_selector in more_selectors:
                        try:
                            more_button = page.locator(more_selector).first
                            if await more_button.count() > 0:
                                print(f"[SCRAPE] Found more button: {more_selector}")
                                await more_button.click()
                                await asyncio.sleep(2)
                                
                                # Scroll again to load new content
                                for scroll in range(2):
                                    await page.mouse.wheel(0, 2000)
                                    await asyncio.sleep(1)
                                
                                # Try to get more links
                                additional_links = await page.locator('a[href*="/jobs/view/"]').all()
                                for link in additional_links:
                                    job_link = await link.get_attribute('href')
                                    if job_link and '/jobs/view/' in job_link:
                                        if job_link.startswith('/'):
                                            job_link = f"https://www.linkedin.com{job_link}"
                                        if job_link not in job_links:
                                            job_links.append(job_link)
                                            if len(job_links) >= max_jobs_per_title:
                                                break
                                break
                        except Exception as e:
                            print(f"[SCRAPE] Error with more button {more_selector}: {e}")
                            continue
                except Exception as e:
                    print(f"[SCRAPE] Error loading more jobs: {e}")
            
            print(f"[SCRAPE] Found {len(job_links)} job links for '{title}'")
            return title, job_links
            
        except Exception as e:
            print(f"[SCRAPE] Error processing title '{title}': {e}")
            return title, []
        finally:
            await page.close()
    
    # Process all titles in parallel
    tasks = [process_title(title) for title in titles]
    results = await asyncio.gather(*tasks)
    
    # Now scrape job details in parallel with retry mechanism
    async def scrape_job_details_parallel(job_url):
        page = await context.new_page()
        try:
            job_details = await scrape_job_details_fast(page, job_url)
            return job_details
        except Exception as e:
            print(f"[SCRAPE] Error scraping {job_url}: {e}")
            # Return a basic job structure with error
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
        finally:
            await page.close()
    
    # Process each title's jobs
    for title, job_links in results:
        if job_links:
            print(f"[SCRAPE] Scraping details for {len(job_links)} jobs from '{title}'...")
            
            # Scrape job details in parallel (with concurrency limit)
            semaphore = asyncio.Semaphore(3)  # Limit concurrent requests
            
            async def scrape_with_semaphore(job_url):
                async with semaphore:
                    return await scrape_job_details_parallel(job_url)
            
            tasks = [scrape_with_semaphore(job_url) for job_url in job_links]
            detailed_jobs = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions
            valid_jobs = []
            for job in detailed_jobs:
                if isinstance(job, dict) and not job.get('error'):
                    valid_jobs.append(job)
            
            all_jobs[title] = valid_jobs
            print(f"[SCRAPE] Completed '{title}': {len(valid_jobs)} jobs with details")
        else:
            all_jobs[title] = []
    
    return all_jobs

def filter_jobs_by_keywords(job_data, keywords):
    """
    Filter jobs based on keywords found in job description or requirements.
    """
    print(f"[FILTER] Filtering jobs based on {len(keywords)} keywords: {keywords}")
    
    filtered_jobs = {}
    total_jobs = 0
    filtered_count = 0
    
    for title, jobs in job_data.items():
        filtered_jobs[title] = []
        total_jobs += len(jobs)
        
        for job in jobs:
            # Combine description and requirements for keyword search
            search_text = ""
            if job.get('description'):
                search_text += job['description'].lower()
            if job.get('requirements'):
                search_text += job['requirements'].lower()
            
            # Check if any keyword is present
            if search_text:
                for keyword in keywords:
                    if keyword.lower() in search_text:
                        filtered_jobs[title].append(job)
                        filtered_count += 1
                        break
    
    print(f"[FILTER] Total jobs: {total_jobs}")
    print(f"[FILTER] Jobs matching keywords: {filtered_count}")
    
    return filtered_jobs

async def main(custom_titles=None, custom_keywords=None, max_jobs_per_title=15):
    """
    Main function to scrape LinkedIn jobs.
    
    Args:
        custom_titles (list, optional): Custom job titles to search. If None, uses defaults.
        custom_keywords (list, optional): Custom keywords for filtering. If None, uses defaults.
        max_jobs_per_title (int, optional): Maximum jobs to scrape per title. Default is 15.
    """
    print(f"[MAIN] Starting Fast LinkedIn job scraper...")
    print(f"[MAIN] Timestamp: {datetime.now()}")
    
    # Get job titles and keywords
    print(f"\n[MAIN] Step 1: Processing job titles and keywords")
    titles, filtering_keywords = get_job_titles_and_keywords(custom_titles, custom_keywords)
    
    if not titles:
        print(f"[MAIN] No job titles provided. Exiting.")
        return {}
    
    print(f"[MAIN] Using {len(titles)} titles: {titles}")
    print(f"[MAIN] Using {len(filtering_keywords)} keywords: {filtering_keywords}")
    
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
        
        browser = await playwright.chromium.launch(headless=True)  # Back to headless for speed
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
    
    # Scrape jobs with fast method
    print(f"\n[MAIN] Step 5: Fast scraping job URLs and details")
    start_time = time.time()
    job_data = await scrape_job_urls_fast(context, titles, max_jobs_per_title=max_jobs_per_title)
    end_time = time.time()
    
    print(f"[MAIN] Scraping completed in {end_time - start_time:.2f} seconds")
    
    # Filter jobs by keywords
    print(f"\n[MAIN] Step 6: Filtering jobs by keywords")
    filtered_job_data = filter_jobs_by_keywords(job_data, filtering_keywords)
    
    # Cleanup
    print(f"\n[MAIN] Step 7: Cleaning up resources")
    await context.close()
    await browser.close()
    await playwright.stop()
    print(f"[MAIN] Resources cleaned up")
    
    # Save results to file
    print(f"\n[MAIN] Step 8: Saving results")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"linkedin_jobs_fast_{timestamp}.json"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(filtered_job_data, f, indent=2, ensure_ascii=False)
        print(f"[MAIN] Results saved to: {filename}")
    except Exception as e:
        print(f"[MAIN] Error saving results: {e}")
    
    return filtered_job_data

def print_job_summary(job_data):
    """
    Print a comprehensive summary of all jobs found.
    """
    print(f"\n[SUMMARY] =================================")
    print(f"[SUMMARY] JOB SCRAPING SUMMARY")
    print(f"[SUMMARY] =================================")
    
    total_jobs = sum(len(jobs) for jobs in job_data.values())
    total_titles = len(job_data)
    
    print(f"[SUMMARY] Total job titles searched: {total_titles}")
    print(f"[SUMMARY] Total jobs found: {total_jobs}")
    print(f"[SUMMARY] Average jobs per title: {total_jobs/total_titles:.1f}" if total_titles > 0 else "[SUMMARY] No jobs found")
    
    print(f"\n[SUMMARY] Breakdown by job title:")
    for title, jobs in job_data.items():
        print(f"[SUMMARY]   {title}: {len(jobs)} jobs")
        if jobs:
            companies = set()
            for job in jobs:
                if job.get('company'):
                    companies.add(job['company'])
            print(f"[SUMMARY]     Companies: {len(companies)} unique companies")
    
    print(f"[SUMMARY] =================================")

if __name__ == "__main__":
    print(f"[SCRIPT] Fast LinkedIn Job Scraper Started")
    print(f"[SCRIPT] =================================")
    
    # Example usage:
    # 1. Use default titles and keywords
    # result = asyncio.run(main())
    
    # 2. Use custom titles and default keywords
    # custom_titles = ["Python Developer", "Data Scientist", "DevOps Engineer"]
    # result = asyncio.run(main(custom_titles=custom_titles))
    
    # 3. Use custom titles and custom keywords
    # custom_titles = ["Python Developer", "Data Scientist"]
    # custom_keywords = ["Python", "Django", "Flask", "Machine Learning"]
    # result = asyncio.run(main(custom_titles=custom_titles, custom_keywords=custom_keywords))
    
    # 4. Use custom titles, keywords, and job count
    # result = asyncio.run(main(custom_titles=custom_titles, custom_keywords=custom_keywords, max_jobs_per_title=10))
    
    try:
        # Using default values for demonstration
        result = asyncio.run(main())
        
        print(f"\n[SCRIPT] =================================")
        print(f"[SCRIPT] Final Results:")
        
        if result:
            # Print comprehensive summary
            print_job_summary(result)
            
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

