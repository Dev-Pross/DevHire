import asyncio
from playwright.async_api import async_playwright
import json
import google.generativeai as genai
from urllib.parse import urlparse
from config import GOOGLE_API

PLATFORMS = {
    "linkedin": {
        "url_template": "https://www.linkedin.com/jobs/search/?f_AL=true&f_E=1%2C2&f_JT=F&f_TPR=r604800&f_WT=1%2C2%2C3&keywords={role}&location=India&origin=JOB_SEARCH_PAGE_JOB_FILTER&sortBy=DD",
        "base_url": "https://in.linkedin.com",
    },
}

# Job titles to search
JOB_TITLES = [
    "Full Stack Developer",
    "Frontend Developer", 
    "Backend Developer",
    "Software Engineer",
    "React Developer",
    "JavaScript Developer",
    "Node.js Developer",
    "Web Developer"
]

# Keywords for filtering
FILTERING_KEYWORDS = [
    "React.js", "JavaScript", "Node.js", "Express.js", "HTML", "CSS",
    "Bootstrap", "Java", "MySQL", "SQLite", "MongoDB", "JWT Token",
    "REST API", "Android Development", "Linux", "GitHub", "Git",
    "AI", "Machine Learning", "Data Structures", "Algorithms",
    "Python", "Spring Boot", "TypeScript"
]

# Global duplicate tracker
PROCESSED_JOB_URLS = set()

# ---------------------------------------------------------------------------
# 2. OPTIMIZED SCROLLING FUNCTIONS
# ---------------------------------------------------------------------------

async def close_signin_popups_efficiently(page):
    """Efficiently close popups with minimal time"""
    popup_selectors = [
        ".modal__dismiss",
        "button[aria-label='Dismiss']",
        ".contextual-sign-in-modal__modal-dismiss"
    ]
    
    for selector in popup_selectors:
        try:
            elements = await page.locator(selector).all()
            for element in elements:
                if await element.is_visible():
                    await element.click()
                    print(f"✅ Closed popup using selector: {selector}")
                    await asyncio.sleep(0.5)
                    return  # Exit after successful close
        except:
            continue
    
    # Fallback: ESC key
    try:
        await page.keyboard.press('Escape')
    except:
        pass

async def click_show_more_button(page):
    """Find and click the show more button efficiently"""
    selectors = [
        'button[aria-label*="Show more"]',
        'button:has-text("Show more")',
        '.infinite-scroller__show-more-button',
        'button[data-tracking-control-name="infinite-scroller_show-more"]'
    ]
    
    for selector in selectors:
        try:
            button = await page.wait_for_selector(selector, timeout=2000)
            if button and await button.is_visible() and await button.is_enabled():
                await button.scroll_into_view_if_needed()
                await button.click()
                return True
        except:
            continue
    return False

async def load_all_available_jobs(page):
    """Efficiently scroll the job results container to load all available jobs"""
    try:
        print("🔄 Loading more jobs by scrolling...")
        
        # Close popups once at the start
        await close_signin_popups_efficiently(page)
        
        # Get initial job count
        initial_jobs = await page.query_selector_all('.base-card__full-link')
        initial_count = len(initial_jobs)
        print(f"📊 Initial jobs found: {initial_count}")
        
        last_count = initial_count
        no_change_attempts = 0
        max_no_change = 3
        
        # Find the scrollable job results container
        job_container_selectors = [
            '.jobs-search-results-list',
            '.jobs-search__results-list', 
            '.scaffold-layout__list-container',
            '.jobs-search-results'
        ]
        
        job_container = None
        for selector in job_container_selectors:
            container = await page.query_selector(selector)
            if container:
                job_container = container
                print(f"✅ Found job container: {selector}")
                break
        
        if not job_container:
            print("⚠️ Job container not found, using aggressive scrolling")
        
        # Optimized scrolling loop
        for scroll_attempt in range(10):
            # Multi-level scrolling approach
            await page.evaluate("""
                () => {
                    // 1. Scroll main page
                    window.scrollTo(0, document.body.scrollHeight);
                    
                    // 2. Find and scroll job containers
                    const containers = [
                        '.jobs-search-results-list',
                        '.jobs-search__results-list',
                        '.scaffold-layout__list-container',
                        '.jobs-search-results'
                    ];
                    
                    containers.forEach(selector => {
                        const container = document.querySelector(selector);
                        if (container) {
                            container.scrollTop = container.scrollHeight;
                        }
                    });
                    
                    // 3. Scroll any element with job cards
                    const jobCards = document.querySelectorAll('.base-card__full-link');
                    if (jobCards.length > 0) {
                        const lastCard = jobCards[jobCards.length - 1];
                        lastCard.scrollIntoView({behavior: 'smooth', block: 'end'});
                    }
                }
            """)
            
            await asyncio.sleep(1.5)  # Reduced wait time
            
            # Try to click "Show more" button
            show_more_clicked = await click_show_more_button(page)
            if show_more_clicked:
                print(f"🔘 Clicked 'Show more' button (attempt {scroll_attempt + 1})")
                await asyncio.sleep(2)
            
            # Check current job count
            current_jobs = await page.query_selector_all('.base-card__full-link')
            current_count = len(current_jobs)
            
            if current_count > last_count:
                print(f"📈 Loaded more jobs: {current_count} (was {last_count})")
                last_count = current_count
                no_change_attempts = 0
            else:
                no_change_attempts += 1
                print(f"📊 No new jobs (attempt {no_change_attempts}/{max_no_change})")
                if no_change_attempts >= max_no_change:
                    break
        
        print(f"🎯 Final job count: {len(await page.query_selector_all('.base-card__full-link'))}")
        
    except Exception as e:
        print(f"⚠️ Error during scrolling: {e}")

# ---------------------------------------------------------------------------
# 3. ASYNC JOB PROCESSING
# ---------------------------------------------------------------------------

async def process_single_job(context, job_link, job_index, total_jobs):
    """Process a single job asynchronously"""
    try:
        print(f"📄 Processing job {job_index + 1}/{total_jobs}: {job_link[:70]}...")
        
        # Fetch job description
        job_description = await extract_job_description(context, job_link)
        
        if job_description and job_description != "Description not found":
                print(f"✅ Job {job_index + 1} added - keyword match confirmed")
                return job_link, job_description, "added"
        else:
            return job_link, None, "no_description"
            
    except Exception as e:
        print(f"❌ Error processing job {job_index + 1}: {e}")
        return job_link, None, "error"

async def scrape_platform(browser, platform_name, config, job_title):
    """Modified scrape_platform function with async job processing"""
    global PROCESSED_JOB_URLS
    
    context = await browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1280, "height": 768},
        locale="en-US",
        timezone_id="Asia/Calcutta",
    )
    
    page = await context.new_page()
    job_dict = {}
    
    try:
        url = config["url_template"].format(role=job_title.replace(" ", "%20").lower())
        print(f"🔍 Searching for '{job_title}' on {platform_name}")
        print(f"📄 URL: {url}")
        
        await page.goto(url)
        await asyncio.sleep(5)
        
        # Optimized job loading
        await load_all_available_jobs(page)
        
        # LinkedIn job card selectors
        selectors_to_try = [
            '.base-card__full-link',
            'div[data-entity-urn*="jobPosting"]',
            'div.job-search-card',
            'a[href*="/jobs/view"]',
            'div.base-card',
            'div[class*="job-card"]',
        ]
        
        job_cards = []
        for selector in selectors_to_try:
            cards = await page.query_selector_all(selector)
            if cards:
                print(f"✅ Found {len(cards)} job cards with selector: {selector}")
                job_cards = cards
                break
                
        if not job_cards:
            print(f"❌ No job cards found for '{job_title}'")
            return {}
        
        # STEP 1: Filter and extract job links
        valid_job_links = []
        filtered_out = 0
        duplicates_skipped = 0
        
        print(f"🔍 Pre-filtering {len(job_cards)} job cards...")
        
        for i, card in enumerate(job_cards):
            try:
                text_content = (await card.inner_text()).strip()
                if not text_content:
                    continue
                
                # Filter by keywords FIRST
                if not has_relevant_keywords(text_content,i):
                    filtered_out += 1
                    continue
                
                # Extract job link
                job_link = await extract_job_link(card, config)
                if not job_link or job_link == "Link not found":
                    continue
                
                # Check for duplicates
                if job_link in PROCESSED_JOB_URLS:
                    duplicates_skipped += 1
                    continue
                
                # Add to processed URLs and valid links
                PROCESSED_JOB_URLS.add(job_link)
                valid_job_links.append(job_link)
                
            except Exception as e:
                print(f"❌ Error processing job card {i}: {e}")
                continue
        
        print(f"✅ Pre-filtering complete: {len(valid_job_links)} valid jobs to process")
        
        # STEP 2: Process job descriptions concurrently
        if valid_job_links:
            print(f"🚀 Processing {len(valid_job_links)} jobs concurrently...")
            
            # Create tasks for concurrent processing
            tasks = [
                process_single_job(context, job_link, i, len(valid_job_links))
                for i, job_link in enumerate(valid_job_links)
            ]
            
            # Process jobs concurrently with semaphore
            semaphore = asyncio.Semaphore(10)  # Limit to 10 concurrent requests
            
            async def bounded_task(task):
                async with semaphore:
                    return await task
            
            # Execute all tasks concurrently
            results = await asyncio.gather(*[bounded_task(task) for task in tasks])
            
            # Process results
            processed_jobs = 0
            additional_filtered = 0
            
            for job_link, job_description, status in results:
                if status == "added":
                    job_dict[job_link] = job_description
                    processed_jobs += 1
                elif status == "filtered":
                    PROCESSED_JOB_URLS.discard(job_link)
                    additional_filtered += 1
                elif status in ["no_description", "error"]:
                    PROCESSED_JOB_URLS.discard(job_link)
            
            total_filtered = filtered_out + additional_filtered
            
            print(f"📊 Results for '{job_title}':")
            print(f" ✅ Jobs added: {processed_jobs}")
            print(f" 🔄 Duplicates skipped: {duplicates_skipped}")
            print(f" ⚠️ Jobs filtered out: {total_filtered}")
            print(f" 📁 Total cards processed: {len(job_cards)}")
            
        return job_dict
        
    except Exception as e:
        print(f"❌ Error searching '{job_title}' on {platform_name}: {e}")
        return {}
    finally:
        await context.close()

# ---------------------------------------------------------------------------
# 4. HELPER FUNCTIONS
# ---------------------------------------------------------------------------

def has_relevant_keywords(text_content: str,i:int, threshold: int = 1) -> bool:
    """Check if text contains relevant keywords"""
    text_lower = text_content.lower()
    keyword_matches = []
    main_keywords = FILTERING_KEYWORDS + JOB_TITLES
    # print(len(main_keywords))
    for keyword in main_keywords:
        if keyword.lower() in text_lower:
            print(f"{i}, job with {text_content[:20]}... is relavant to keywords")
            keyword_matches.append(keyword)
            break

    
    return len(keyword_matches) >= threshold

def normalize_job_url(url: str) -> str:
    """Normalize job URL to catch duplicates"""
    try:
        if "/jobs/view/" in url:
            base_url = url.split("?")[0].rstrip("/")
            return base_url
        return url
    except:
        return url

async def extract_job_link(card, config):
    """Extract job link from card element"""
    try:
        # Method 1: Direct job view link
        job_link_elem = await card.query_selector('a[href*="/jobs/view/"]')
        if job_link_elem:
            href = await job_link_elem.get_attribute('href')
            if href:
                full_url = href if href.startswith('http') else config["base_url"] + href
                return normalize_job_url(full_url)
        
        # Method 2: Check if card itself is a link
        tag_name = await card.evaluate("el => el.tagName.toLowerCase()")
        if tag_name == "a":
            href = await card.get_attribute("href")
            if href and "/jobs/view/" in href:
                full_url = href if href.startswith('http') else config["base_url"] + href
                return normalize_job_url(full_url)
        
        return "Link not found"
    except Exception:
        return "Link not found"

async def extract_job_description(context, job_url):
    """Extract job description from individual job page"""
    try:
        detail_page = await context.new_page()
        await detail_page.goto(job_url)
        await asyncio.sleep(3)
        
        # LinkedIn-specific selectors
        desc_selectors = [
            'div.show-more-less-html__markup',
            'div[class*="job-details-jobs-unified-top-card__job-description"]',
            'section[class*="description"]',
            'div[class*="description"]',
            '.jobs-box__html-content',
            'article',
        ]
        
        for selector in desc_selectors:
            desc_elem = await detail_page.query_selector(selector)
            if desc_elem:
                description = (await desc_elem.inner_text()).strip()
                if len(description) > 100:
                    await detail_page.close()
                    return description
        
        await detail_page.close()
        return "Description not found"
    except Exception:
        return "Description not found"

# ---------------------------------------------------------------------------
# 5. GEMINI PROCESSING
# ---------------------------------------------------------------------------

genai.configure(api_key=GOOGLE_API)
model = genai.GenerativeModel("gemini-2.0-flash-exp")

def create_bulk_prompt(jobs_dict: dict) -> str:
    SYSTEM_PROMPT = """
    You are a professional job-data extraction specialist. Extract structured information for ALL jobs and return a JSON array.
    
    EXTRACTION RULES:
    - Extract Job ID from URL (number after /jobs/view/)
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
      }
    ]
    
    Return ONLY the JSON array.
    """
    
    prompt = f"{SYSTEM_PROMPT}\n\nProcess {len(jobs_dict)} jobs:\n"
    for idx, (url, jd) in enumerate(jobs_dict.items(), 1):
        prompt += f"\n--- JOB {idx} ---\nURL: {url}\nDESCRIPTION:\n{jd[:1500]}...\n"
    
    return prompt

def create_fallback_data_from_dict(url: str, job_description: str) -> dict:
    return {
        "title": "Not extracted",
        "job_id": "Not extracted", 
        "company_name": "Not extracted",
        "location": "India",
        "experience": "Not specified",
        "salary": "Not specified",
        "key_skills": [],
        "job_url": url,
        "posted_at": "Not specified",
        "job_description": job_description,
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

async def extract_jobs_in_batches(jobs_dict: dict, batch_size: int = 15) -> list:
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
        
        await asyncio.sleep(2)
    
    return all_extracted

# ---------------------------------------------------------------------------
# 6. MAIN EXECUTION
# ---------------------------------------------------------------------------

async def search_by_job_titles_with_keyword_filtering(job_titles, platforms=None):
    """Main function to get maximum jobs"""
    global PROCESSED_JOB_URLS
    
    if platforms is None:
        platforms = list(PLATFORMS.keys())
    
    all_jobs = {}
    PROCESSED_JOB_URLS.clear()
    
    print(f"🚀 Starting job extraction with optimized scrolling...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        
        for i, job_title in enumerate(job_titles, 1):
            print(f"\n{'='*70}")
            print(f"🎯 SEARCHING TITLE {i}/{len(job_titles)}: '{job_title}'")
            print(f"🔢 Processed URLs so far: {len(PROCESSED_JOB_URLS)}")
            print(f"{'='*70}")
            
            for platform_name in platforms:
                try:
                    result = await scrape_platform(browser, platform_name, PLATFORMS[platform_name], job_title)
                    all_jobs.update(result)
                    print(f"📈 Jobs from '{job_title}': {len(result)}")
                except Exception as e:
                    print(f"❌ Error searching '{job_title}' on {platform_name}: {e}")
                
                await asyncio.sleep(3)
            
            print(f"📊 '{job_title}' complete. Total unique jobs: {len(all_jobs)}")
        
        await browser.close()
    
    print(f"\n{'='*70}")
    print(f"🏆 EXTRACTION COMPLETE!")
    print(f"📊 Total unique jobs: {len(all_jobs)}")
    print(f"🔢 Total URLs processed: {len(PROCESSED_JOB_URLS)}")
    print(f"🎯 Success rate: {(len(all_jobs)/len(PROCESSED_JOB_URLS)*100):.1f}%")
    print(f"{'='*70}")
    
    return all_jobs

async def main():
    print("🧠 Starting job extraction and processing...")
    
    # Get all jobs
    all_jobs = await search_by_job_titles_with_keyword_filtering(JOB_TITLES)
    
    if len(all_jobs) == 0:
        print("❌ No jobs found to analyze...")
        return
    
    print(f"🧠 Sending {len(all_jobs)} jobs to Gemini for extraction...")
    extracted = await extract_jobs_in_batches(all_jobs, batch_size=15)
    
    # Save results
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"linkedin_jobs_{timestamp}.json"
    
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
    print(f" 🔵 Easy Apply enabled: YES")

# ---------------------------------------------------------------------------
# 7. SCRIPT ENTRY POINT
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("🚀 Starting OPTIMIZED LinkedIn Job Scraper...")
    print(f"📋 Job Titles to search: {len(JOB_TITLES)}")
    print(f"🔍 Filtering keywords: {len(FILTERING_KEYWORDS)}")
    print(f"🔵 Easy Apply: ENABLED")
    print(f"⚡ Optimized scrolling: ENABLED")
    
    asyncio.run(main())
