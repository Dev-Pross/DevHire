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
# 2. ENHANCED SCRAPING WITH KEYWORD FILTERING
# ---------------------------------------------------------------------------
async def scrape_platform(browser, platform_name, config, job_title):
    # Create context with popup blocking
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
    
    # Block popups immediately
    # context.on("page", lambda popup: asyncio.create_task(popup.close()))
    
    page = await context.new_page()
    job_dict = {}
    
    try:
        # Use job title in URL
        url = config["url_template"].format(role=job_title.replace(" ", "%20").lower())
        print(f"🔍 Searching for '{job_title}' on {platform_name}")
        print(f"📄 URL: {url}")
        await page.goto(url)
        await asyncio.sleep(5)

        # LinkedIn job card selectors
        selectors_to_try = [
            '.base-card__full-link',                         # Base card links
            'div[data-entity-urn*="jobPosting"]',           # LinkedIn specific
            'div.job-search-card',                           # LinkedIn job cards
            
            'a[href*="/jobs/view"]',                         # Direct job links
            'div.base-card',                                 # LinkedIn base cards
            'div[class*="job-card"]',                        # Generic job cards
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
        
        for i, card in enumerate(job_cards[:50]):  # Process up to 50 jobs
            try:
                text_content = (await card.inner_text()).strip()
                if not text_content:
                    continue

                # **KEY FEATURE: Filter by keywords**
                if not has_relevant_keywords(text_content):
                    filtered_out += 1
                    continue

                # Extract job link
                job_link = await extract_job_link(card, config)
                if not job_link or job_link == "Link not found":
                    continue

                print(f"📄 Processing job {processed_jobs + 1}: {job_link[:70]}...")

                # Extract full job description
                job_description = await extract_job_description(context, job_link)
                
                if job_description and job_description != "Description not found":
                    # **DOUBLE CHECK: Verify keywords in full description**
                    if has_relevant_keywords(job_description, threshold=2):
                        job_dict[job_link] = job_description
                        processed_jobs += 1
                        print(f"✅ Job {processed_jobs} added - keyword match confirmed")
                    else:
                        print(f"⚠️  Job filtered out - insufficient keyword matches in description")
                        filtered_out += 1
                
                # Stop if we have enough quality jobs
                if processed_jobs >= 20:
                    break

            except Exception as e:
                print(f"❌ Error processing job card {i}: {e}")
                continue

        print(f"📊 Results for '{job_title}':")
        print(f"   ✅ Jobs added: {processed_jobs}")
        print(f"   ⚠️  Jobs filtered out: {filtered_out}")
        print(f"   📁 Total extracted: {len(job_dict)}")
        
        return job_dict
        
    except Exception as e:
        print(f"❌ Error searching '{job_title}' on {platform_name}: {e}")
        return {}
    finally:
        await context.close()

# ---------------------------------------------------------------------------
# 3. KEYWORD FILTERING FUNCTIONS
# ---------------------------------------------------------------------------
def has_relevant_keywords(text_content: str, threshold: int = 1) -> bool:
    """
    Check if text contains relevant keywords from our filtering list
    Args:
        text_content: Job card text or job description
        threshold: Minimum number of keywords required to consider relevant
    """
    text_lower = text_content.lower()
    
    # Count keyword matches
    keyword_matches = []
    for keyword in FILTERING_KEYWORDS:
        if keyword.lower() in text_lower:
            keyword_matches.append(keyword)
    
    # Debug: Print matched keywords for first few jobs
    if len(keyword_matches) >= threshold:
        print(f"   🎯 Keywords found: {keyword_matches[:5]}...")  # Show first 5 matches
        return True
    
    return False

def get_job_relevance_score(text_content: str) -> dict:
    """Get detailed relevance scoring for a job"""
    text_lower = text_content.lower()
    
    matches = {
        "frontend": ["react", "javascript", "html", "css", "bootstrap"],
        "backend": ["node.js", "express.js", "java", "spring", "python", "rest api"],
        "database": ["mysql", "mongodb", "sqlite", "postgresql"],
        "tools": ["git", "github", "linux", "docker"],
        "emerging": ["ai", "machine learning", "blockchain"]
    }
    
    score_breakdown = {}
    for category, keywords in matches.items():
        found = [kw for kw in keywords if kw in text_lower]
        score_breakdown[category] = {
            "count": len(found),
            "keywords": found
        }
    
    total_score = sum(cat["count"] for cat in score_breakdown.values())
    return {
        "total_score": total_score,
        "breakdown": score_breakdown,
        "is_relevant": total_score >= 3
    }

# ---------------------------------------------------------------------------
# 4. HELPER FUNCTIONS (Updated)
# ---------------------------------------------------------------------------
async def extract_job_link(card, config):
    """Extract job link from card element"""
    try:
        # Method 1: Direct job view link
        job_link_elem = await card.query_selector('a[href*="/jobs/view/"]')
        if job_link_elem:
            href = await job_link_elem.get_attribute('href')
            if href:
                return href if href.startswith('http') else config["base_url"] + href

        # Method 2: Check if card itself is a link
        tag_name = await card.evaluate("el => el.tagName.toLowerCase()")
        if tag_name == "a":
            href = await card.get_attribute("href")
            if href and "/jobs/view/" in href:
                return href if href.startswith('http') else config["base_url"] + href

        # Method 3: Any job view link in the card
        all_links = await card.query_selector_all('a[href]')
        for link in all_links:
            href = await link.get_attribute('href')
            if href and "/jobs/view/" in href:
                return href if href.startswith('http') else config["base_url"] + href

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
# 5. GEMINI CONFIGURATION (Updated)
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

# Your existing helper functions...
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
# 6. MAIN EXECUTION FUNCTIONS
# ---------------------------------------------------------------------------
async def search_by_job_titles_with_keyword_filtering(job_titles, platforms=None):
    """
    Main function: Search by job titles in URL, filter by keywords
    """
    if platforms is None:
        platforms = list(PLATFORMS.keys())
    
    all_jobs = {}
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        
        for i, job_title in enumerate(job_titles, 1):
            print(f"\n{'='*70}")
            print(f"🎯 SEARCHING JOB TITLE {i}/{len(job_titles)}: '{job_title}'")
            print(f"{'='*70}")
            
            for platform_name in platforms:
                try:
                    result = await scrape_platform(browser, platform_name, PLATFORMS[platform_name], job_title)
                    
                    # Avoid duplicates
                    new_jobs = {k: v for k, v in result.items() if k not in all_jobs}
                    all_jobs.update(new_jobs)
                    
                    print(f"📈 Total jobs for '{job_title}': {len(result)} ({len(new_jobs)} new)")
                    
                except Exception as e:
                    print(f"❌ Error searching '{job_title}' on {platform_name}: {e}")
                
                await asyncio.sleep(3)
            
            print(f"📊 Completed '{job_title}'. Running total: {len(all_jobs)} unique jobs")
        
        await browser.close()
    
    print(f"\n{'='*70}")
    print(f"🏆 FINAL RESULTS: {len(all_jobs)} unique, keyword-filtered jobs")
    print(f"{'='*70}")
    return all_jobs

async def main(data_dict):
    print("🧠 Sending filtered jobs to Gemini for detailed extraction...")
    if len(data_dict) == 0:
        print("❌ No jobs found to analyze...")
        return

    extracted = await extract_jobs_in_batches(data_dict, batch_size=15)
    
    # Save results
    timestamp = "2025-01-27"
    filename = f"filtered_jobs_{timestamp}.json"
    
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
    
    print(f"\n📊 SUMMARY:")
    print(f"   🏢 Companies: {len(companies)}")
    print(f"   🛠️  Unique skills found: {len(total_skills)}")
    print(f"   📄 Total jobs: {len(extracted)}")

# ---------------------------------------------------------------------------
# 7. SCRIPT ENTRY POINT
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("🚀 Starting Job Title Search with Keyword Filtering...")
    print(f"📋 Job Titles to search: {len(JOB_TITLES)}")
    print(f"🔍 Filtering keywords: {len(FILTERING_KEYWORDS)}")
    print(f"📅 Search date: January 27, 2025")
    
    # Execute the search
    all_jobs = asyncio.run(search_by_job_titles_with_keyword_filtering(JOB_TITLES))
    
    # Process with Gemini
    asyncio.run(main(all_jobs))
