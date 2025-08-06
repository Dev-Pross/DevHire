import asyncio
import os
import sys
import re
import json
import time
from datetime import datetime
from playwright.async_api import async_playwright

# Color constants for debugging
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
    
    # Background colors
    BG_RED = '\033[101m'
    BG_GREEN = '\033[102m'
    BG_YELLOW = '\033[103m'
    BG_BLUE = '\033[104m'
    BG_MAGENTA = '\033[105m'
    BG_CYAN = '\033[106m'

def print_config(msg):
    print(f"{Colors.CYAN}[CONFIG]{Colors.END} {msg}")

def print_login(msg):
    print(f"{Colors.MAGENTA}[LOGIN]{Colors.END} {msg}")

def print_success(msg):
    print(f"{Colors.GREEN}✅ [SUCCESS]{Colors.END} {msg}")

def print_error(msg):
    print(f"{Colors.RED}❌ [ERROR]{Colors.END} {msg}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️ [WARNING]{Colors.END} {msg}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ️ [INFO]{Colors.END} {msg}")

def print_progress(msg):
    print(f"{Colors.YELLOW}🔄 [PROGRESS]{Colors.END} {msg}")

def print_scrape(msg):
    print(f"{Colors.CYAN}🔍 [SCRAPE]{Colors.END} {msg}")

def print_details(msg):
    print(f"{Colors.MAGENTA}📋 [DETAILS]{Colors.END} {msg}")

def print_filter(msg):
    print(f"{Colors.GREEN}🔧 [FILTER]{Colors.END} {msg}")

def print_main(msg):
    print(f"{Colors.BOLD}{Colors.BLUE}🚀 [MAIN]{Colors.END} {msg}")

def print_summary(msg):
    print(f"{Colors.BOLD}{Colors.GREEN}📊 [SUMMARY]{Colors.END} {msg}")

def print_script(msg):
    print(f"{Colors.BOLD}{Colors.CYAN}🎯 [SCRIPT]{Colors.END} {msg}")

def print_input(msg):
    print(f"{Colors.YELLOW}📝 [INPUT]{Colors.END} {msg}")

# Import config from correct location (backend_python/config.py)
sys.path.append(os.path.dirname(__file__))
try:
    from config import LINKEDIN_ID, LINKEDIN_PASSWORD
    print_config(f"{Colors.GREEN}Successfully imported config{Colors.END}")
    print_config(f"LINKEDIN_ID: {Colors.CYAN}{'***' if LINKEDIN_ID else 'None'}{Colors.END}")
    print_config(f"LINKEDIN_PASSWORD: {Colors.CYAN}{'***' if LINKEDIN_PASSWORD else 'None'}{Colors.END}")
except ImportError as e:
    print_error(f"Error importing config: {Colors.RED}{e}{Colors.END}")
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
    print_input(f"{Colors.CYAN}Processing job titles and keywords...{Colors.END}")
    
    # Use custom titles if provided, otherwise use defaults
    job_titles = custom_titles if custom_titles is not None else DEFAULT_JOB_TITLES
    filtering_keywords = custom_keywords if custom_keywords is not None else DEFAULT_FILTERING_KEYWORDS
    
    print_input(f"Using {Colors.GREEN}{len(job_titles)}{Colors.END} job titles: {Colors.YELLOW}{job_titles}{Colors.END}")
    print_input(f"Using {Colors.GREEN}{len(filtering_keywords)}{Colors.END} filtering keywords: {Colors.YELLOW}{filtering_keywords}{Colors.END}")
    
    return job_titles, filtering_keywords


async def linkedin_login(page, username, password):
    """Login to LinkedIn with comprehensive logging"""
    print_login(f"{Colors.BOLD}Starting LinkedIn login process...{Colors.END}")
    print_login(f"Username: {Colors.CYAN}{username}{Colors.END}")
    print_login(f"Password: {Colors.CYAN}{'***' if password else 'None'}{Colors.END}")
    
    if not username or not password:
        print_error(f"Missing credentials, cannot proceed")
        return False
    
    try:
        print_progress(f"Navigating to: {Colors.UNDERLINE}{LINKEDIN_LOGIN_URL}{Colors.END}")
        await page.goto(LINKEDIN_LOGIN_URL)
        print_success(f"Successfully navigated to login page")
        
        # Wait for page to load
        await page.wait_for_load_state('domcontentloaded')
        print_success(f"Page loaded successfully")
        
        # Fill username
        print_progress(f"Filling username field...")
        await page.fill('input#username', username)
        print_success(f"Username filled successfully")
        
        # Fill password
        print_progress(f"Filling password field...")
        await page.fill('input#password', password)
        print_success(f"Password filled successfully")
        
        # Click submit
        print_progress(f"Clicking submit button...")
        try:
            async with page.expect_navigation(timeout=60000):
                await page.click('button[type="submit"]')
            print_success(f"Submit button clicked, navigation completed")
        except Exception as e:
            print_warning(f"Navigation timeout, but continuing: {Colors.YELLOW}{e}{Colors.END}")
            await page.click('button[type="submit"]')
        
        # Wait for page to load
        print_progress(f"Waiting for page to load...")
        try:
            await page.wait_for_load_state('networkidle', timeout=60000)
            print_success(f"Page loaded to networkidle state")
        except Exception as e:
            print_warning(f"Networkidle timeout, trying domcontentloaded: {Colors.YELLOW}{e}{Colors.END}")
            try:
                await page.wait_for_load_state('domcontentloaded', timeout=30000)
                print_success(f"Page loaded to domcontentloaded state")
            except Exception as e2:
                print_error(f"Domcontentloaded timeout: {Colors.RED}{e2}{Colors.END}")
        
        # Check current URL
        try:
            current_url = page.url
            print_info(f"Current URL after login: {Colors.UNDERLINE}{current_url}{Colors.END}")
        except Exception as e:
            print_error(f"Error getting current URL: {Colors.RED}{e}{Colors.END}")
            return False
        
        # Check if login was successful
        if "feed" in current_url or "jobs" in current_url:
            print_success(f"{Colors.BOLD}Login successful - redirected to feed/jobs{Colors.END}")
            return True
        elif "login" in current_url:
            print_error(f"Login failed - still on login page")
            return False
        else:
            print_warning(f"Login status unclear - URL: {Colors.UNDERLINE}{current_url}{Colors.END}")
            return True
            
    except Exception as e:
        print_error(f"Error during login process: {Colors.RED}{e}{Colors.END}")
        return False


async def scrape_job_details_fast(page, job_url):
    """
    Fast version of job details scraping with optimized selectors and minimal waits.
    """
    try:
        print_scrape(f"🌐 Navigating to: {Colors.UNDERLINE}{job_url[:50]}...{Colors.END}")
        await page.goto(job_url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)  # Increased wait time for better loading
        
        # Wait for content to load
        try:
            await page.wait_for_selector('h1, .jobs-unified-top-card__job-title, .job-details-jobs-unified-top-card__job-title', timeout=10000)
            print_success(f"Page content loaded successfully")
        except Exception:
            print_warning(f"Specific elements not found, continuing anyway")
        
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
                    print_info(f"Extracted from page title - Title: {Colors.GREEN}{job_data['title']}{Colors.END}, Company: {Colors.CYAN}{job_data['company']}{Colors.END}")
        except Exception:
            print_warning(f"Could not extract from page title")
        
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
        
        print_progress(f"🔍 Trying {len(title_selectors)} title selectors...")
        for i, selector in enumerate(title_selectors):
            try:
                elements = await page.locator(selector).all()
                for element in elements:
                    title_text = await element.text_content()
                    if title_text and title_text.strip() and len(title_text.strip()) > 3:
                        job_data["title"] = title_text.strip()
                        print_success(f"Found title with selector #{i+1}: {Colors.GREEN}{title_text.strip()}{Colors.END}")
                        break
                if job_data["title"]:
                    break
            except Exception:
                continue
        
        if not job_data["title"]:
            print_warning(f"No title found with any selector")
        
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
        
        print_progress(f"🏢 Trying {len(company_selectors)} company selectors...")
        for i, selector in enumerate(company_selectors):
            try:
                elements = await page.locator(selector).all()
                for element in elements:
                    company_text = await element.text_content()
                    if company_text and company_text.strip() and len(company_text.strip()) > 2:
                        # Filter out location-like text
                        company_lower = company_text.lower()
                        if not any(word in company_lower for word in ["remote", "hybrid", "on-site", "india", "us", "uk", "bangalore", "mumbai", "delhi", "new york", "california"]):
                            job_data["company"] = company_text.strip()
                            print_success(f"Found company with selector #{i+1}: {Colors.CYAN}{company_text.strip()}{Colors.END}")
                            break
                if job_data["company"]:
                    break
            except Exception:
                continue
        
        if not job_data["company"]:
            print_warning(f"No company found with any selector")
        
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
        
        print_progress(f"📍 Trying {len(location_selectors)} location selectors...")
        for i, selector in enumerate(location_selectors):
            try:
                elements = await page.locator(selector).all()
                for element in elements:
                    location_text = await element.text_content()
                    if location_text and location_text.strip():
                        location_lower = location_text.lower()
                        # Check for location indicators
                        if any(word in location_lower for word in ["remote", "hybrid", "on-site", "india", "us", "uk", "bangalore", "mumbai", "delhi", "new york", "california", "texas", "florida", "pune", "chennai", "hyderabad"]):
                            job_data["location"] = location_text.strip()
                            print_success(f"Found location with selector #{i+1}: {Colors.YELLOW}{location_text.strip()}{Colors.END}")
                            break
                        # Also check for general location patterns
                        elif any(char in location_text for char in [",", "•", "|"]) and len(location_text.strip()) > 3:
                            job_data["location"] = location_text.strip()
                            print_success(f"Found location (pattern match) with selector #{i+1}: {Colors.YELLOW}{location_text.strip()}{Colors.END}")
                            break
                if job_data["location"]:
                    break
            except Exception:
                continue
        
        if not job_data["location"]:
            print_warning(f"No location found with any selector")
        
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
        
        print_progress(f"📄 Trying {len(description_selectors)} description selectors...")
        for i, selector in enumerate(description_selectors):
            try:
                elements = await page.locator(selector).all()
                for element in elements:
                    desc_text = await element.text_content()
                    if desc_text and desc_text.strip() and len(desc_text.strip()) > 100:
                        job_data["description"] = desc_text.strip()
                        if len(job_data["description"]) > 2000:  # Increased length
                            job_data["description"] = job_data["description"][:2000] + "..."
                        print_success(f"Found description with selector #{i+1}: {Colors.GREEN}{len(desc_text)} chars{Colors.END}")
                        break
                if job_data["description"]:
                    break
            except Exception:
                continue
        
        # If still no description, try getting any substantial text content
        if not job_data["description"]:
            print_warning(f"Primary description selectors failed, trying fallback...")
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
                
                for i, selector in enumerate(main_selectors):
                    try:
                        elements = await page.locator(selector).all()
                        for element in elements:
                            content_text = await element.text_content()
                            if content_text and content_text.strip() and len(content_text.strip()) > 200:
                                job_data["description"] = content_text.strip()
                                if len(job_data["description"]) > 2000:
                                    job_data["description"] = job_data["description"][:2000] + "..."
                                print_success(f"Found description with fallback selector #{i+1}: {Colors.GREEN}{len(content_text)} chars{Colors.END}")
                                break
                        if job_data["description"]:
                            break
                    except Exception:
                        continue
            except Exception:
                pass
        
        if not job_data["description"]:
            print_error(f"No description found with any selector")
        
        # Try to extract requirements if description is available
        if job_data["description"]:
            print_progress(f"🔍 Extracting requirements from description...")
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
                                print_success(f"Extracted requirements using keyword '{keyword}': {Colors.GREEN}{len(requirements_text)} chars{Colors.END}")
                                break
            except Exception:
                print_warning(f"Could not extract requirements")
        
        # Debug: Print what we found
        print_details(f"📋 {Colors.BOLD}EXTRACTION SUMMARY:{Colors.END}")
        print_details(f"URL: {Colors.UNDERLINE}{job_url}{Colors.END}")
        print_details(f"Title: {Colors.GREEN}{job_data['title'] if job_data['title'] else 'NOT FOUND'}{Colors.END}")
        print_details(f"Company: {Colors.CYAN}{job_data['company'] if job_data['company'] else 'NOT FOUND'}{Colors.END}")
        print_details(f"Location: {Colors.YELLOW}{job_data['location'] if job_data['location'] else 'NOT FOUND'}{Colors.END}")
        print_details(f"Description length: {Colors.MAGENTA}{len(job_data['description'])} chars{Colors.END}")
        print_details(f"Requirements length: {Colors.BLUE}{len(job_data.get('requirements', ''))} chars{Colors.END}")
        
        return job_data
        
    except Exception as e:
        print_error(f"Error scraping job details: {Colors.RED}{e}{Colors.END}")
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
    print_scrape(f"{Colors.BOLD}Starting comprehensive job scraping{Colors.END}")
    print_scrape(f"Titles: {Colors.CYAN}{titles}{Colors.END}")
    print_scrape(f"Max jobs per title: {Colors.YELLOW}{max_jobs_per_title}{Colors.END}")
    print_scrape(f"Expected total jobs: {Colors.GREEN}{len(titles) * max_jobs_per_title}{Colors.END}")
    
    all_jobs = {}
    
    # Process titles in parallel
    async def process_title(title):
        print_scrape(f"🎯 {Colors.BOLD}Processing title: {Colors.CYAN}{title}{Colors.END}")
        
        page = await context.new_page()
        try:
            # Encode title for URL
            encoded_title = title.replace(' ', '%20')
            search_url = f"https://www.linkedin.com/jobs/search/?f_AL=true&f_E=1%2C2&f_JT=F&f_TPR=r86400&f_WT=1%2C2%2C3&keywords={encoded_title}&location=India&origin=JOB_SEARCH_PAGE_JOB_FILTER&sortBy=DD"
            
            print_progress(f"🌐 Navigating to: {Colors.UNDERLINE}{search_url}{Colors.END}")
            await page.goto(search_url, wait_until="domcontentloaded")
            await asyncio.sleep(3)  # Increased wait time for better loading
            print_success(f"Page loaded successfully")
            
            # Multiple scrolls to load more content
            print_progress(f"📜 Scrolling to load more content...")
            for scroll in range(3):
                await page.mouse.wheel(0, 3000)
                await asyncio.sleep(1)
                print_info(f"Scroll {scroll + 1}/3 completed")
            
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
            
            print_progress(f"🔍 Trying {len(selectors)} different selectors to find job cards...")
            
            # Try multiple approaches to find ALL job links
            for i, selector in enumerate(selectors):
                try:
                    cards = await page.locator(selector).all()
                    if cards and len(cards) > 0:
                        print_success(f"Found {Colors.GREEN}{len(cards)}{Colors.END} elements with selector #{i+1}: {Colors.YELLOW}{selector}{Colors.END}")
                        for card_idx, card in enumerate(cards[:max_jobs_per_title * 2]):  # Get more to ensure we have enough
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
                                                    print_info(f"Found job link #{len(job_links)}: {Colors.UNDERLINE}{job_link[:50]}...{Colors.END}")
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
                    print_warning(f"Error with selector #{i+1} {selector}: {Colors.YELLOW}{e}{Colors.END}")
                    continue
            
            # If still not enough links, try direct link extraction
            if len(job_links) < max_jobs_per_title:
                print_warning(f"Only found {len(job_links)}/{max_jobs_per_title} jobs, trying direct link extraction...")
                try:
                    all_links = await page.locator('a[href*="/jobs/view/"]').all()
                    print_info(f"Found {Colors.CYAN}{len(all_links)}{Colors.END} direct job links")
                    for link in all_links[:max_jobs_per_title * 2]:
                        job_link = await link.get_attribute('href')
                        if job_link and '/jobs/view/' in job_link:
                            if job_link.startswith('/'):
                                job_link = f"https://www.linkedin.com{job_link}"
                            if job_link not in job_links:
                                job_links.append(job_link)
                                print_info(f"Added direct link #{len(job_links)}: {Colors.UNDERLINE}{job_link[:50]}...{Colors.END}")
                                if len(job_links) >= max_jobs_per_title:
                                    break
                except Exception as e:
                    print_error(f"Error in direct link extraction: {Colors.RED}{e}{Colors.END}")
            
            # Try one more approach - look for any job-related links
            if len(job_links) < max_jobs_per_title:
                print_warning(f"Still only {len(job_links)}/{max_jobs_per_title}, trying comprehensive link search...")
                try:
                    all_links = await page.locator('a').all()
                    for link in all_links:
                        try:
                            href = await link.get_attribute('href')
                            if href and '/jobs/view/' in href:
                                if href.startswith('/'):
                                    href = f"https://www.linkedin.com{href}"
                                if href not in job_links:
                                    job_links.append(href)
                                    print_info(f"Added comprehensive link #{len(job_links)}: {Colors.UNDERLINE}{href[:50]}...{Colors.END}")
                                    if len(job_links) >= max_jobs_per_title:
                                        break
                        except Exception:
                            continue
                except Exception as e:
                    print_error(f"Error in comprehensive link search: {Colors.RED}{e}{Colors.END}")
            
            # Try to get more jobs by clicking "See more jobs" or pagination
            if len(job_links) < max_jobs_per_title:
                print_warning(f"Still only {len(job_links)}/{max_jobs_per_title}, trying to load more jobs...")
                try:
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
                                print_success(f"Found 'more' button: {Colors.CYAN}{more_selector}{Colors.END}")
                                await more_button.click()
                                await asyncio.sleep(2)
                                print_success(f"Clicked 'more' button")
                                
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
                                            print_success(f"Added additional link #{len(job_links)}: {Colors.UNDERLINE}{job_link[:50]}...{Colors.END}")
                                            if len(job_links) >= max_jobs_per_title:
                                                break
                                break
                        except Exception as e:
                            print_warning(f"Error with 'more' button {more_selector}: {Colors.YELLOW}{e}{Colors.END}")
                            continue
                except Exception as e:
                    print_error(f"Error loading more jobs: {Colors.RED}{e}{Colors.END}")
            
            print_success(f"{Colors.BOLD}Found {Colors.GREEN}{len(job_links)}{Colors.END} job links for '{Colors.CYAN}{title}{Colors.END}'")
            return title, job_links
            
        except Exception as e:
            print_error(f"Error processing title '{title}': {Colors.RED}{e}{Colors.END}")
            return title, []
        finally:
            await page.close()
    
    # Process all titles in parallel
    print_progress(f"🚀 Processing all {len(titles)} titles in parallel...")
    tasks = [process_title(title) for title in titles]
    results = await asyncio.gather(*tasks)
    
    # Now scrape job details in parallel with retry mechanism
    async def scrape_job_details_parallel(job_url):
        page = await context.new_page()
        try:
            job_details = await scrape_job_details_fast(page, job_url)
            return job_details
        except Exception as e:
            print_error(f"Error scraping {job_url}: {Colors.RED}{e}{Colors.END}")
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
            print_progress(f"📋 Scraping details for {Colors.YELLOW}{len(job_links)}{Colors.END} jobs from '{Colors.CYAN}{title}{Colors.END}'...")
            
            # Scrape job details in parallel (with concurrency limit)
            semaphore = asyncio.Semaphore(3)  # Limit concurrent requests
            
            async def scrape_with_semaphore(job_url):
                async with semaphore:
                    return await scrape_job_details_parallel(job_url)
            
            tasks = [scrape_with_semaphore(job_url) for job_url in job_links]
            detailed_jobs = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions
            valid_jobs = []
            error_count = 0
            for job in detailed_jobs:
                if isinstance(job, dict) and not job.get('error'):
                    valid_jobs.append(job)
                else:
                    error_count += 1
            
            all_jobs[title] = valid_jobs
            print_success(f"✅ Completed '{Colors.CYAN}{title}{Colors.END}': {Colors.GREEN}{len(valid_jobs)}{Colors.END} jobs with details")
            if error_count > 0:
                print_warning(f"⚠️ {error_count} jobs had errors")
        else:
            all_jobs[title] = []
            print_warning(f"No jobs found for '{Colors.CYAN}{title}{Colors.END}'")
    
    return all_jobs


def filter_jobs_by_keywords(job_data, keywords):
    """
    Filter jobs based on keywords found in job description or requirements.
    """
    print_filter(f"🔧 Filtering jobs based on {Colors.YELLOW}{len(keywords)}{Colors.END} keywords")
    print_filter(f"Keywords: {Colors.CYAN}{keywords}{Colors.END}")
    
    filtered_jobs = {}
    total_jobs = 0
    filtered_count = 0
    
    for title, jobs in job_data.items():
        print_progress(f"🔍 Processing '{Colors.CYAN}{title}{Colors.END}': {len(jobs)} jobs...")
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
                found_keywords = []
                for keyword in keywords:
                    if keyword.lower() in search_text:
                        found_keywords.append(keyword)
                
                if found_keywords:
                    filtered_jobs[title].append(job)
                    filtered_count += 1
                    print_success(f"✅ Job matched keywords {Colors.GREEN}{found_keywords}{Colors.END}: {Colors.YELLOW}{job.get('title', 'No title')}{Colors.END}")
        
        print_info(f"📊 '{Colors.CYAN}{title}{Colors.END}': {Colors.GREEN}{len(filtered_jobs[title])}{Colors.END}/{len(jobs)} jobs matched keywords")
    
    print_filter(f"📊 {Colors.BOLD}FILTERING SUMMARY:{Colors.END}")
    print_filter(f"Total jobs processed: {Colors.YELLOW}{total_jobs}{Colors.END}")
    print_filter(f"Jobs matching keywords: {Colors.GREEN}{filtered_count}{Colors.END}")
    print_filter(f"Filter success rate: {Colors.CYAN}{(filtered_count/total_jobs*100):.1f}%{Colors.END}" if total_jobs > 0 else "No jobs to filter")
    
    return filtered_jobs


async def main(custom_titles=None, custom_keywords=None, max_jobs_per_title=15):
    """
    Main function to scrape LinkedIn jobs.
    
    Args:
        custom_titles (list, optional): Custom job titles to search. If None, uses defaults.
        custom_keywords (list, optional): Custom keywords for filtering. If None, uses defaults.
        max_jobs_per_title (int, optional): Maximum jobs to scrape per title. Default is 15.
    """
    print_main(f"{Colors.BOLD}🚀 Starting Fast LinkedIn job scraper...{Colors.END}")
    print_main(f"Timestamp: {Colors.CYAN}{datetime.now()}{Colors.END}")
    
    # Get job titles and keywords
    print_main(f"\n{Colors.BOLD}Step 1: Processing job titles and keywords{Colors.END}")
    titles, filtering_keywords = get_job_titles_and_keywords(custom_titles, custom_keywords)
    
    if not titles:
        print_error(f"No job titles provided. Exiting.")
        return {}
    
    print_main(f"Using {Colors.GREEN}{len(titles)}{Colors.END} titles: {Colors.YELLOW}{titles}{Colors.END}")
    print_main(f"Using {Colors.GREEN}{len(filtering_keywords)}{Colors.END} keywords: {Colors.YELLOW}{filtering_keywords}{Colors.END}")
    
    # Check credentials
    print_main(f"\n{Colors.BOLD}Step 2: Checking LinkedIn credentials{Colors.END}")
    if LINKEDIN_ID is None or LINKEDIN_PASSWORD is None:
        print_error(f"LinkedIn credentials not found in config. Exiting.")
        print_error(f"Please create a .env file in the backend_python directory with:")
        print_error(f"LINKEDIN_ID=your_linkedin_email@example.com")
        print_error(f"LINKEDIN_PASSWORD=your_linkedin_password")
        return {}
    
    print_success(f"Credentials found, proceeding with scraping")
    
    # Start Playwright
    print_main(f"\n{Colors.BOLD}Step 3: Starting Playwright browser{Colors.END}")
    try:
        playwright = await async_playwright().start()
        print_success(f"Playwright started successfully")
        
        browser = await playwright.chromium.launch(headless=True)  # Back to headless for speed
        print_success(f"Browser launched successfully")
        
        context = await browser.new_context()
        print_success(f"Browser context created")
        
    except Exception as e:
        print_error(f"Error starting Playwright: {Colors.RED}{e}{Colors.END}")
        return {}
    
    # Login to LinkedIn
    print_main(f"\n{Colors.BOLD}Step 4: Logging into LinkedIn{Colors.END}")
    page = await context.new_page()
    login_success = await linkedin_login(page, LINKEDIN_ID, LINKEDIN_PASSWORD)
    await page.close()
    
    if not login_success:
        print_error(f"LinkedIn login failed. Exiting.")
        await context.close()
        await browser.close()
        await playwright.stop()
        return {}
    
    print_success(f"{Colors.BOLD}LinkedIn login successful!{Colors.END}")
    
    # Scrape jobs with fast method
    print_main(f"\n{Colors.BOLD}Step 5: Fast scraping job URLs and details{Colors.END}")
    start_time = time.time()
    job_data = await scrape_job_urls_fast(context, titles, max_jobs_per_title=max_jobs_per_title)
    end_time = time.time()
    
    print_success(f"{Colors.BOLD}Scraping completed in {Colors.GREEN}{end_time - start_time:.2f}{Colors.END} seconds")
    
    # Filter jobs by keywords
    print_main(f"\n{Colors.BOLD}Step 6: Filtering jobs by keywords{Colors.END}")
    filtered_job_data = filter_jobs_by_keywords(job_data, filtering_keywords)
    
    # Cleanup
    print_main(f"\n{Colors.BOLD}Step 7: Cleaning up resources{Colors.END}")
    await context.close()
    await browser.close()
    await playwright.stop()
    print_success(f"Resources cleaned up")
    
    # Save results to file
    print_main(f"\n{Colors.BOLD}Step 8: Saving results{Colors.END}")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"linkedin_jobs_fast_{timestamp}.json"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(filtered_job_data, f, indent=2, ensure_ascii=False)
        print_success(f"Results saved to: {Colors.GREEN}{filename}{Colors.END}")
    except Exception as e:
        print_error(f"Error saving results: {Colors.RED}{e}{Colors.END}")
    
    return filtered_job_data


def print_job_summary(job_data):
    """
    Print a comprehensive summary of all jobs found.
    """
    print_summary(f"\n{Colors.BG_GREEN}{Colors.WHITE} JOB SCRAPING SUMMARY {Colors.END}")
    print_summary(f"{'='*50}")
    
    total_jobs = sum(len(jobs) for jobs in job_data.values())
    total_titles = len(job_data)
    
    print_summary(f"Total job titles searched: {Colors.CYAN}{total_titles}{Colors.END}")
    print_summary(f"Total jobs found: {Colors.GREEN}{total_jobs}{Colors.END}")
    print_summary(f"Average jobs per title: {Colors.YELLOW}{total_jobs/total_titles:.1f}{Colors.END}" if total_titles > 0 else f"{Colors.RED}No jobs found{Colors.END}")
    
    print_summary(f"\n{Colors.BOLD}Breakdown by job title:{Colors.END}")
    for title, jobs in job_data.items():
        print_summary(f"  📋 {Colors.CYAN}{title}{Colors.END}: {Colors.GREEN}{len(jobs)}{Colors.END} jobs")
        if jobs:
            companies = set()
            for job in jobs:
                if job.get('company'):
                    companies.add(job['company'])
            print_summary(f"     🏢 Companies: {Colors.YELLOW}{len(companies)}{Colors.END} unique companies")
    
    print_summary(f"{'='*50}")


if __name__ == "__main__":
    print_script(f"{Colors.BOLD}{Colors.BG_CYAN}{Colors.WHITE} FAST LINKEDIN JOB SCRAPER STARTED {Colors.END}")
    print_script(f"{'='*50}")
    
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
        
        print_script(f"\n{Colors.BG_BLUE}{Colors.WHITE} FINAL RESULTS {Colors.END}")
        
        if result:
            # Print comprehensive summary
            print_job_summary(result)
            
            total_jobs = sum(len(jobs) for jobs in result.values())
            print_script(f"Total jobs found: {Colors.GREEN}{total_jobs}{Colors.END}")
            
            for title, jobs in result.items():
                print_script(f"\n📋 Title: {Colors.CYAN}{title}{Colors.END}")
                print_script(f"Jobs found: {Colors.GREEN}{len(jobs)}{Colors.END}")
                if jobs:
                    for idx, job in enumerate(jobs, 1):
                        print_script(f"  {Colors.YELLOW}{idx}.{Colors.END} {Colors.WHITE}{job.get('title', 'No title')}{Colors.END} at {Colors.CYAN}{job.get('company', 'Unknown company')}{Colors.END}")
                        if job.get('location'):
                            print_script(f"     📍 Location: {Colors.YELLOW}{job['location']}{Colors.END}")
                        if job.get('description'):
                            desc_preview = job['description'][:100] + "..." if len(job['description']) > 100 else job['description']
                            print_script(f"     📄 Description: {Colors.WHITE}{desc_preview}{Colors.END}")
                else:
                    print_warning(f"   No jobs found for this title.")
        else:
            print_error(f"No job URLs found.")
            
    except KeyboardInterrupt:
        print_error(f"\n{Colors.RED}Exiting on user interrupt.{Colors.END}")
    except Exception as e:
        print_error(f"\nUnexpected error: {Colors.RED}{e}{Colors.END}")
        import traceback
        traceback.print_exc()
    
    print_script(f"{Colors.BOLD}{Colors.GREEN}Script completed.{Colors.END}")
