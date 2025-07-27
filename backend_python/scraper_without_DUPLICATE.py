import asyncio
from playwright.async_api import async_playwright
import json
import google.generativeai as genai
from urllib.parse import urlparse
from config import GOOGLE_API

# ---------------------------------------------------------------------------
# 1. CONFIGURATION - Job Titles for URL, Keywords for Filtering
# ---------------------------------------------------------------------------
PLATFORMS = {
    "linkedin": {
        "url_template": "https://www.linkedin.com/jobs/search/?f_AL=true&f_E=1%2C2&f_JT=F&f_TPR=r86400&f_WT=1%2C2%2C3&keywords={role}&location=India&origin=JOB_SEARCH_PAGE_JOB_FILTER&sortBy=DD",
        "base_url": "https://in.linkedin.com",
    },
}

# Job titles to search in URL (these replace {role} in URL)
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

# Keywords to filter relevant jobs from search results
FILTERING_KEYWORDS = [
    "React.js", "JavaScript", "Node.js", "Express.js", "HTML", "CSS", 
    "Bootstrap", "Java", "MySQL", "SQLite", "MongoDB", "JWT Token", 
    "REST API", "Android Development", "Linux", "GitHub", "Git", 
    "AI", "Machine Learning", "Data Structures", "Algorithms",
    "Python", "Spring Boot", "Angular", "Vue.js", "TypeScript"
]

# ---------------------------------------------------------------------------
# GLOBAL DUPLICATE TRACKER
# ---------------------------------------------------------------------------
PROCESSED_JOB_URLS = set()

# ---------------------------------------------------------------------------
# 2. MAXIMIZED SCRAPING - NO ARTIFICIAL LIMITS
# ---------------------------------------------------------------------------
async def scrape_platform(browser, platform_name, config, job_title):
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

        # Try to load more jobs by scrolling
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

        processed_jobs = 0
        filtered_out = 0
        duplicates_skipped = 0
        
        # REMOVED LIMIT: Process ALL job cards found
        print(f"🚀 Processing ALL {len(job_cards)} job cards for maximum results...")
        
        for i, card in enumerate(job_cards):  # NO LIMIT - process all cards
            try:
                text_content = (await card.inner_text()).strip()
                if not text_content:
                    continue

                # STEP 1: Filter by keywords FIRST
                if not has_relevant_keywords(text_content):
                    filtered_out += 1
                    continue

                # STEP 2: Extract job link
                job_link = await extract_job_link(card, config)
                if not job_link or job_link == "Link not found":
                    continue

                # STEP 3: Check for duplicates
                if job_link in PROCESSED_JOB_URLS:
                    duplicates_skipped += 1
                    print(f"🔄 Duplicate skipped: {job_link[:50]}...")
                    continue

                # STEP 4: Add to processed URLs
                PROCESSED_JOB_URLS.add(job_link)

                print(f"📄 Processing job {processed_jobs + 1}/{len(job_cards)}: {job_link[:70]}...")

                # STEP 5: Fetch job description
                job_description = await extract_job_description(context, job_link)
                
                if job_description and job_description != "Description not found":
                    # STEP 6: Final keyword verification
                    if has_relevant_keywords(job_description, threshold=2):
                        job_dict[job_link] = job_description
                        processed_jobs += 1
                        print(f"✅ Job {processed_jobs} added - keyword match confirmed")
                    else:
                        print(f"⚠️  Job filtered out - insufficient keywords in description")
                        PROCESSED_JOB_URLS.discard(job_link)
                        filtered_out += 1
                else:
                    PROCESSED_JOB_URLS.discard(job_link)
                
                # REMOVED: No break condition - process all cards

            except Exception as e:
                print(f"❌ Error processing job card {i}: {e}")
                continue

        print(f"📊 COMPLETE Results for '{job_title}':")
        print(f"   ✅ Jobs added: {processed_jobs}")
        print(f"   🔄 Duplicates skipped: {duplicates_skipped}")
        print(f"   ⚠️  Jobs filtered out: {filtered_out}")
        print(f"   📁 Total cards processed: {len(job_cards)}")
        print(f"   📈 Success rate: {(processed_jobs/len(job_cards)*100):.1f}%")
        
        return job_dict
        
    except Exception as e:
        print(f"❌ Error searching '{job_title}' on {platform_name}: {e}")
        return {}
    finally:
        await context.close()

# ---------------------------------------------------------------------------
# 3. FUNCTION TO LOAD MORE JOBS BY SCROLLING
# ---------------------------------------------------------------------------
async def load_all_available_jobs(page):
    """Scroll and load as many jobs as possible"""
    try:
        print("🔄 Loading more jobs by scrolling...")
        
        # Get initial job count
        initial_jobs = await page.query_selector_all('.base-card__full-link')
        initial_count = len(initial_jobs)
        print(f"📊 Initial jobs found: {initial_count}")
        
        # Scroll to load more jobs
        for scroll_attempt in range(10):  # Try up to 10 scrolls
            # Scroll to bottom
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(3)
            
            # Check if "Show more" button exists and click it
            show_more_selectors = [
                'button[aria-label*="Show more"]',
                'button:has-text("Show more")',
                '.infinite-scroller__show-more-button',
                'button[data-tracking-control-name="infinite-scroller_show-more"]'
            ]
            
            for selector in show_more_selectors:
                show_more_btn = await page.query_selector(selector)
                if show_more_btn:
                    try:
                        await show_more_btn.click()
                        print(f"🔘 Clicked 'Show more' button (attempt {scroll_attempt + 1})")
                        await asyncio.sleep(3)
                        break
                    except:
                        continue
            
            # Check current job count
            current_jobs = await page.query_selector_all('.base-card__full-link')
            current_count = len(current_jobs)
            
            if current_count > initial_count:
                print(f"📈 Loaded more jobs: {current_count} (was {initial_count})")
                initial_count = current_count
            else:
                print(f"📊 No new jobs loaded, stopping at {current_count}")
                break
        
        final_jobs = await page.query_selector_all('.base-card__full-link')
        print(f"🎯 Final job count after scrolling: {len(final_jobs)}")
        
    except Exception as e:
        print(f"⚠️  Error during scrolling: {e}")

# ---------------------------------------------------------------------------
# 4. KEYWORD FILTERING FUNCTIONS (unchanged)
# ---------------------------------------------------------------------------
def has_relevant_keywords(text_content: str, threshold: int = 1) -> bool:
    """Check if text contains relevant keywords from our filtering list"""
    text_lower = text_content.lower()
    
    keyword_matches = []
    for keyword in FILTERING_KEYWORDS:
        if keyword.lower() in text_lower:
            keyword_matches.append(keyword)
    
    if len(keyword_matches) >= threshold:
        # Only print for first few matches to avoid spam
        if len(keyword_matches) <= 3:
            print(f"   🎯 Keywords found: {keyword_matches}")
        return True
    
    return False

# ---------------------------------------------------------------------------
# 5. HELPER FUNCTIONS
# ---------------------------------------------------------------------------
def normalize_job_url(url: str) -> str:
    """Normalize job URL to catch duplicates with different parameters"""
    try:
        if "/jobs/view/" in url:
            base_url = url.split("?")[0].rstrip("/")
            return base_url
        return url
    except:
        return url

async def extract_job_link(card, config):
    """Extract job link from card element with normalization"""
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

        # Method 3: Any job view link in the card
        all_links = await card.query_selector_all('a[href]')
        for link in all_links:
            href = await link.get_attribute('href')
            if href and "/jobs/view/" in href:
                full_url = href if href.startswith('http') else config["base_url"] + href
                return normalize_job_url(full_url)

        return "Link not found"
        
    except Exception as e:
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
        
    except Exception as e:
        return "Description not found"

# ---------------------------------------------------------------------------
# 6. GEMINI CONFIGURATION
# ---------------------------------------------------------------------------
genai.configure(api_key=GOOGLE_API)
model = genai.GenerativeModel("gemini-2.5-flash-lite-preview-06-17")

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

def infer_source_from_url(url: str) -> str:
    return "linkedin" if "linkedin" in url else "unknown"

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
# 7. MAIN EXECUTION - MAXIMIZED RESULTS
# ---------------------------------------------------------------------------
async def search_by_job_titles_with_keyword_filtering(job_titles, platforms=None):
    """Main function with NO LIMITS - get maximum jobs"""
    global PROCESSED_JOB_URLS
    
    if platforms is None:
        platforms = list(PLATFORMS.keys())
    
    all_jobs = {}
    
    # Reset duplicate tracker
    PROCESSED_JOB_URLS.clear()
    print(f"🧹 Starting fresh - targeting MAXIMUM jobs with Easy Apply")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        
        for i, job_title in enumerate(job_titles, 1):
            print(f"\n{'='*70}")
            print(f"🎯 MAXIMIZING JOBS FOR TITLE {i}/{len(job_titles)}: '{job_title}'")
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
    print(f"🏆 MAXIMUM RESULTS ACHIEVED!")
    print(f"📊 Total unique Easy Apply jobs: {len(all_jobs)}")
    print(f"🔢 Total URLs processed: {len(PROCESSED_JOB_URLS)}")
    print(f"🎯 Success rate: {(len(all_jobs)/len(PROCESSED_JOB_URLS)*100):.1f}%")
    print(f"{'='*70}")
    return all_jobs

async def main(data_dict):
    print("🧠 Sending ALL filtered jobs to Gemini for detailed extraction...")
    if len(data_dict) == 0:
        print("❌ No jobs found to analyze...")
        return

    extracted = await extract_jobs_in_batches(data_dict, batch_size=15)
    
    # Save results
    timestamp = "2025-01-27"
    filename = f"maximum_jobs_{timestamp}.json"
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(extracted, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Successfully extracted data for {len(extracted)} jobs")
    print(f"📁 Results saved to {filename}")
    
    # Print summary
    total_skills = set()
    companies = set()
    easy_apply_count = 0
    
    for job in extracted:
        if job.get("key_skills"):
            total_skills.update(job["key_skills"])
        if job.get("company_name") and job["company_name"] != "Not extracted":
            companies.add(job["company_name"])
    
    print(f"\n📊 MAXIMUM RESULTS SUMMARY:")
    print(f"   🏢 Companies: {len(companies)}")
    print(f"   🛠️  Unique skills found: {len(total_skills)}")
    print(f"   📄 Total jobs extracted: {len(extracted)}")
    print(f"   🔵 Easy Apply enabled: YES (f_AL=true)")
    print(f"   📅 Latest jobs: Last 24 hours")
    print(f"   🎯 All matching job titles and keywords included")

# ---------------------------------------------------------------------------
# 8. SCRIPT ENTRY POINT
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("🚀 Starting MAXIMUM Job Extraction with Easy Apply...")
    print(f"📋 Job Titles to search: {len(JOB_TITLES)}")
    print(f"🔍 Filtering keywords: {len(FILTERING_KEYWORDS)}")
    print(f"📅 Target: Latest jobs (24 hours)")
    print(f"🔵 Easy Apply: ENABLED")
    print("🎯 Goal: MAXIMUM qualifying jobs (NO LIMITS)")
    
    # Execute the search for maximum results
    all_jobs = asyncio.run(search_by_job_titles_with_keyword_filtering(JOB_TITLES))
    
    # Process with Gemini
    asyncio.run(main(all_jobs))
