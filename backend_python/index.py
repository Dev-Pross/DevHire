import asyncio
from playwright.async_api import async_playwright
import json
import google.generativeai as genai
from urllib.parse import urlparse
from config import GOOGLE_API

PLATFORMS = {
    "ycombinator": {
        "url_template": "https://www.ycombinator.com/jobs/role/{role}",
        "base_url": "https://www.ycombinator.com"
    },
    "linkedin": {
        "url_template": "https://www.linkedin.com/jobs/search/?keywords={role}&location=India&geoId=102713980&f_TPR=r3600&f_WT=1%2C2%2C3&position=1&pageNum=0",
        "base_url": "https://www.linkedin.com"
    },
}

# 5 keywords as requested
WEB_DEV_KEYWORDS = [
    'frontend-developer',
    'backend-developer', 
    'full-stack-developer',
    'react-developer',
    'python-developer'
]

# Configure Gemini API
genai.configure(api_key=GOOGLE_API)
model = genai.GenerativeModel('gemini-2.5-flash-lite-preview-06-17')

async def scrape_platform(browser, platform_name, config, role):
    """Scrape jobs for a specific role from a platform"""
    page = await browser.new_page()
    job_dict = {}
    
    try:
        url = config["url_template"].format(role=role.replace(' ', '-').lower())
        print(f"Navigating to {platform_name} for '{role}': {url}")
        await page.goto(url)
        await asyncio.sleep(5)

        selectors_to_try = [
            'a[href*="/jobs/"]', '[data-testid*="job"]',
            '.job-card', '.job-listing', '.job-item',
            'article', '.card', '.listing',
            'div[class*="job"]', 'div[class*="listing"]',
            'li'
        ]

        job_cards = []
        for selector in selectors_to_try:
            cards = await page.query_selector_all(selector)
            if cards:
                print(f"Found {len(cards)} elements with selector: {selector}  ---{platform_name}")
                job_cards = cards
                break

        if not job_cards:
            job_cards = await page.query_selector_all('a, button, [role="button"]')
            print(f"Using fallback: Found {len(job_cards)} clickable elements")

        max_jobs = 100
        for i, card in enumerate(job_cards[:max_jobs]):
            try:
                text_content = (await card.inner_text()).strip()
                if not text_content:
                    continue

                # Check if job is relevant
                title = "title not found"
                title_elements = await card.query_selector_all('h1, h2, h3, h4, h5, h6')
                if title_elements:
                    title = (await title_elements[0].inner_text()).strip().lower()
                elif text_content:
                    lines = text_content.split('\n')
                    if lines:
                        title = lines[0].strip().lower()
                
                # More flexible keyword matching
                role_keywords = role.replace('-', ' ').split()
                has_relevant_keyword = (
                    any(kw in title for kw in role_keywords) or
                    any(kw in text_content.lower() for kw in role_keywords) or
                    any(keyword in title or keyword in text_content.lower() 
                        for keyword in ['developer', 'engineer', 'programming', 'coding'])
                )
                
                if not has_relevant_keyword:
                    continue

                # Extract job URL
                tag_name = await card.evaluate('el => el.tagName.toLowerCase()')
                job_link = "Link not found"
                
                if tag_name == 'a':
                    job_link = await card.get_attribute('href') or "Link not found"
                else:
                    link_elem = await card.query_selector('a[href*="job"], a[href*="apply"]')
                    job_link = await link_elem.get_attribute('href') if link_elem else "Link not found"
                
                if job_link != "Link not found" and not job_link.startswith("http"):
                    job_link = config["base_url"] + job_link

                # YC filter
                should_add = True
                if platform_name.lower() == "ycombinator":
                    if "/companies/" not in job_link:
                        continue

                # Extract job description
                job_description = "Description not found"
                if job_link != "Link not found":
                    try:
                        detail_page = await browser.new_page()
                        await detail_page.goto(job_link)
                        await asyncio.sleep(2)
                        
                        # YC specific header extraction
                        header_text = ""
                        if platform_name == "ycombinator":
                            desc_header_selector = ".ycdc-card.max-w-2xl"
                            desc_header = await detail_page.query_selector(desc_header_selector)
                            if desc_header:
                                header_text = (await desc_header.inner_text()).strip()
                        
                        # Main content extraction
                        desc_selectors = [
                            '[class*="description"]', '[class*="job-details"]',
                            'article', '.prose', '.job-desc'
                        ]
                        
                        desc_text = ""
                        for selector in desc_selectors:
                            desc_elem = await detail_page.query_selector(selector)
                            if desc_elem:
                                desc_text = (await desc_elem.inner_text()).strip()
                                break
                        
                        # Combine header and description
                        if header_text and desc_text:
                            job_description = f"{header_text}\n\n{desc_text}"
                        elif desc_text:
                            job_description = desc_text
                        elif header_text:
                            job_description = header_text
                            
                        await detail_page.close()
                        
                    except Exception as e:
                        print(f"Error fetching description for {job_link}: {e}")

                if should_add and job_link != "Link not found" and job_description != "Description not found":
                    job_dict[job_link] = job_description
                    print(f"✅ Found for '{role}': {job_link[:50]}... ({len(job_description)} chars --{platform_name} card-{i})")
                    
            except Exception as e:
                print(f"Error processing card {i}: {e}")
                continue

        print(f"[{platform_name}] Found {len(job_dict)} jobs for '{role}'")
        return job_dict
        
    except Exception as e:
        print(f"Error on {platform_name} for role {role}: {e}")
        return {}
    finally:
        await page.close()

async def scrape_all_keywords():
    """Scrape jobs for all keywords with deduplication"""
    all_jobs_combined = {}  # {url: {description, roles_found}}
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        
        for keyword_index, role in enumerate(WEB_DEV_KEYWORDS, 1):
            print(f"\n{'='*80}")
            print(f"PROCESSING KEYWORD {keyword_index}/{len(WEB_DEV_KEYWORDS)}: '{role}'")
            print(f"{'='*80}")
            
            # Scrape all platforms for this keyword in parallel
            tasks = [
                scrape_platform(browser, platform, PLATFORMS[platform], role)
                for platform in PLATFORMS.keys()
            ]
            results = await asyncio.gather(*tasks)
            
            # Merge platform results for this keyword
            keyword_jobs = {}
            for platform_result in results:
                keyword_jobs.update(platform_result)
            
            print(f"Keyword '{role}' total: {len(keyword_jobs)} jobs")
            
            # Smart deduplication
            new_jobs = 0
            duplicate_jobs = 0
            
            for url, description in keyword_jobs.items():
                if url not in all_jobs_combined:
                    # New unique job
                    all_jobs_combined[url] = {
                        'description': description,
                        'found_by_roles': [role]
                    }
                    new_jobs += 1
                else:
                    # Duplicate job - just track the additional role
                    if role not in all_jobs_combined[url]['found_by_roles']:
                        all_jobs_combined[url]['found_by_roles'].append(role)
                    duplicate_jobs += 1
            
            print(f"  📊 New jobs: {new_jobs}, Duplicates: {duplicate_jobs}")
        
        await browser.close()
    
    # Prepare final format for Gemini
    final_jobs = {}
    for url, job_data in all_jobs_combined.items():
        roles_list = ", ".join(job_data['found_by_roles'])
        final_jobs[url] = f"[MATCHED_ROLES: {roles_list}]\n\n{job_data['description']}"
    
    print(f"\n📊 FINAL SUMMARY:")
    print(f"Total unique jobs after deduplication: {len(final_jobs)}")
    
    # Show breakdown by keyword
    role_stats = {}
    for job_data in all_jobs_combined.values():
        for role in job_data['found_by_roles']:
            role_stats[role] = role_stats.get(role, 0) + 1
    
    print(f"\n📈 Jobs found per keyword:")
    for role, count in role_stats.items():
        print(f"  {role}: {count} jobs")
    
    return final_jobs

def create_bulk_prompt(jobs_dict: dict) -> str:
    """Create optimized prompt for Gemini"""
    SYSTEM_PROMPT = """You are a professional job data extraction specialist. Extract structured information from job descriptions and return a JSON array.

EXTRACTION RULES:
- Process every URL-JD pair
- Extract information ONLY from the job description text
- If information is not mentioned, use "Not specified"
- For matched_keywords, look for [MATCHED_ROLES: role1, role2] at the beginning
- For experience: look for years like "3+", "5+ years", "Senior", "Junior", "Entry level"
- For location: city, state/country, or "Remote"
- For salary: include currency and amount (e.g., "$90K-$120K", "₹15-20 LPA")
- For company: extract from text or URL path /companies/[company-name]/

REQUIRED OUTPUT FORMAT (JSON array):
[
  {
    "title": "extracted job title",
    "company_name": "company name",
    "location": "location or Remote",
    "experience": "experience level",
    "salary": "salary range with currency",
    "matched_keywords": "roles that matched this job",
    "job_url": "the URL",
    "posted_at": "posting date or Not specified",
    "job_description": "full description",
    "source": "platform name"
  }
]

IMPORTANT: Return ONLY valid JSON array, no extra text."""

    prompt = f"""{SYSTEM_PROMPT}

Process {len(jobs_dict)} job descriptions:

"""
    
    for idx, (url, jd) in enumerate(jobs_dict.items(), 1):
        # Truncate very long descriptions to save tokens
        truncated_jd = jd[:2000] + "..." if len(jd) > 2000 else jd
        prompt += f"""--- JOB {idx} ---
URL: {url}
DESCRIPTION: {truncated_jd}
--- END JOB {idx} ---

"""
    
    prompt += f"Return JSON array with exactly {len(jobs_dict)} objects in the same order."
    return prompt

def parse_bulk_response(response_text: str, original_jobs: dict) -> list:
    """Parse Gemini response with error handling"""
    try:
        # Clean response
        clean_response = response_text.strip()
        if clean_response.startswith('```json'):
            clean_response = clean_response[7:].lstrip()
        elif clean_response.startswith('```'):
            clean_response = clean_response[3:].lstrip()
        if clean_response.endswith('```'):
            clean_response = clean_response[:-3].rstrip()
        
        # Save for debugging
        with open("gemini_raw_response.json", "w", encoding="utf-8") as f:
            f.write(clean_response)
        
        # Parse JSON
        extracted_jobs = json.loads(clean_response)
        
        if not isinstance(extracted_jobs, list):
            extracted_jobs = [extracted_jobs]
        
        # Ensure all jobs have required fields
        job_urls = list(original_jobs.keys())
        for i, job in enumerate(extracted_jobs):
            if i < len(job_urls):
                job['job_url'] = job_urls[i]
                job['job_description'] = original_jobs[job_urls[i]]
                
                if not job.get('source'):
                    job['source'] = infer_source_from_url(job_urls[i])
        
        # Add fallbacks for missing jobs
        while len(extracted_jobs) < len(job_urls):
            idx = len(extracted_jobs)
            url = job_urls[idx]
            fallback_job = create_fallback_data_from_dict(url, original_jobs[url])
            extracted_jobs.append(fallback_job)
        
        return extracted_jobs
        
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print(f"Response preview: {response_text[:500]}...")
        return [create_fallback_data_from_dict(url, jd) for url, jd in original_jobs.items()]
    except Exception as e:
        print(f"Error parsing response: {e}")
        return [create_fallback_data_from_dict(url, jd) for url, jd in original_jobs.items()]

def create_fallback_data_from_dict(url: str, job_description: str) -> dict:
    """Create fallback data when extraction fails"""
    return {
        "title": "Not extracted",
        "company_name": "Not extracted",
        "location": "Not extracted",
        "experience": "Not specified",
        "salary": "Not specified",
        "matched_keywords": "Not specified",
        "job_url": url,
        "posted_at": "Not specified",
        "job_description": job_description,
        "source": infer_source_from_url(url)
    }

def infer_source_from_url(url: str) -> str:
    """Extract platform name from URL"""
    try:
        domain = urlparse(url).netloc.lower()
        if 'ycombinator' in domain:
            return 'ycombinator'
        elif 'linkedin' in domain:
            return 'linkedin'
        else:
            return domain.replace('www.', '').split('.')
    except:
        return 'unknown'

async def extract_jobs_in_batches(jobs_dict: dict, batch_size: int = 50) -> list:
    """Process jobs in batches"""
    all_extracted = []
    job_items = list(jobs_dict.items())
    total_batches = (len(job_items) + batch_size - 1) // batch_size
    
    print(f"\n🔄 Processing {len(job_items)} jobs in {total_batches} batches of {batch_size}")
    
    for i in range(0, len(job_items), batch_size):
        batch_dict = dict(job_items[i:i + batch_size])
        batch_num = (i // batch_size) + 1
        
        print(f"Processing batch {batch_num}/{total_batches}: {len(batch_dict)} jobs")
        
        try:
            batch_result = await extract_single_batch(batch_dict)
            all_extracted.extend(batch_result)
            print(f"✅ Batch {batch_num} completed: {len(batch_result)} jobs processed")
            
        except Exception as e:
            print(f"❌ Batch {batch_num} failed: {e}")
            fallback_jobs = [create_fallback_data_from_dict(url, jd) 
                           for url, jd in batch_dict.items()]
            all_extracted.extend(fallback_jobs)
        
        # Rate limiting
        if batch_num < total_batches:
            print(f"⏳ Waiting 3 seconds before next batch...")
            await asyncio.sleep(3)
    
    return all_extracted

async def extract_single_batch(batch_dict: dict) -> list:
    """Process single batch through Gemini"""
    try:
        prompt = create_bulk_prompt(batch_dict)
        response = model.generate_content(prompt)
        extracted_jobs = parse_bulk_response(response.text, batch_dict)
        return extracted_jobs
    except Exception as e:
        print(f"Error in batch processing: {e}")
        return [create_fallback_data_from_dict(url, jd) for url, jd in batch_dict.items()]

async def main():
    """Main orchestration function"""
    print(f"🚀 Starting job scraping for keywords: {WEB_DEV_KEYWORDS}")
    
    # Step 1: Scrape all jobs for all keywords
    all_jobs = await scrape_all_keywords()
    
    # Step 2: Save raw scraped data
    with open("jobs_raw_all_keywords.json", "w", encoding="utf-8") as f:
        json.dump(all_jobs, f, indent=2, ensure_ascii=False)
    print(f"💾 Raw data saved to: jobs_raw_all_keywords.json")
    
    # Step 3: Process through Gemini in batches
    print(f"\n🤖 Starting Gemini processing...")
    extracted_jobs = await extract_jobs_in_batches(all_jobs, batch_size=50)
    
    # Step 4: Save final structured data
    with open("jobs_final_structured.json", "w", encoding="utf-8") as f:
        json.dump(extracted_jobs, f, indent=2, ensure_ascii=False)
    
    # Step 5: Generate summary
    print(f"\n{'='*80}")
    print(f"🎉 PROCESSING COMPLETE!")
    print(f"{'='*80}")
    print(f"📁 Files generated:")
    print(f"  - jobs_raw_all_keywords.json (raw scraped data)")
    print(f"  - jobs_final_structured.json (structured data)")
    print(f"  - gemini_raw_response.json (debug data)")
    print(f"📊 Total jobs processed: {len(extracted_jobs)}")
    
    # Keyword breakdown
    keyword_stats = {}
    for job in extracted_jobs:
        keywords = job.get('matched_keywords', 'Unknown')
        for keyword in keywords.split(', '):
            keyword = keyword.strip()
            if keyword:
                keyword_stats[keyword] = keyword_stats.get(keyword, 0) + 1
    
    print(f"\n📈 Final breakdown by keyword:")
    for keyword, count in sorted(keyword_stats.items()):
        print(f"  {keyword}: {count} jobs")
    
    print(f"\n✨ Done! Check jobs_final_structured.json for complete results.")

if __name__ == "__main__":
    asyncio.run(main())