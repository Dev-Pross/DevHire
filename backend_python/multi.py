import asyncio
from playwright.async_api import async_playwright
import json
import google.generativeai as genai
import json
from urllib.parse import urlparse
from config import GOOGLE_API

PLATFORMS = {
    "ycombinator": {
        "url_template": "https://www.ycombinator.com/jobs/role/{role}",
        "base_url": "https://www.ycombinator.com"
    },
    "linkedin": {
        "url_template": "https://www.linkedin.com/jobs/search/?keywords={role}-posted-at-&location=India&geoId=102713980&f_TPR=r3600&f_WT=1%2C2%2C3&position=1&pageNum=0",
        "base_url": "https://www.linkedin.com"
    },
}

WEB_DEV_KEYWORDS = [
    'web developer',    
    'frontend-developer',
    'backend-developer', 
    'full-stack-developer',
    'react-developer'
]

async def scrape_platform(browser, platform_name, config, role):
    page = await browser.new_page()
    job_dict = {}
    try:
        url = config["url_template"].format(role=role.replace(' ', '%20').lower())
        print(f"Navigating to {platform_name} jobs page: {url}")
        await page.goto(url)
        await asyncio.sleep(5)

        print(f"Searching for job listings on {platform_name}...")

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
                print(f"Found {len(cards)} elements with selector: {selector} on {platform_name}")
                job_cards = cards
                break

        if not job_cards:
            job_cards = await page.query_selector_all('a, button, [role="button"]')
            print(f"Using fallback: Found {len(job_cards)} clickable elements on {platform_name}")

        max_jobs = 100  # Max to process
        for i, card in enumerate(job_cards[:max_jobs]):
            try:
                text_content = (await card.inner_text()).strip()
                if not text_content:
                    continue

                # Basic webdev filtering
                title = "title not found"
                title_elements = await card.query_selector_all('h1, h2, h3, h4, h5, h6')
                if title_elements:
                    title = (await title_elements[0].inner_text()).strip().lower()
                elif text_content:
                    lines = text_content.split('\n')
                    if lines:
                        title = lines[0].strip().lower()
                has_web_dev_keyword = any(keyword in title or keyword in text_content.lower() for keyword in WEB_DEV_KEYWORDS)
                if not has_web_dev_keyword:
                    print(f"Skipping irrelevant job card {i} on {platform_name}")
                    continue

                # URL extraction
                tag_name = await card.evaluate('el => el.tagName.toLowerCase()')
                job_link = "Link not found"
                if tag_name == 'a':
                    job_link = await card.get_attribute('href') or "Link not found"
                else:
                    link_elem = await card.query_selector('a[href*="job"], a[href*="apply"]')
                    job_link = await link_elem.get_attribute('href') if link_elem else "Link not found"
                if job_link != "Link not found" and not job_link.startswith("http"):
                    job_link = config["base_url"] + job_link

                # YC Additional filter: must have /companies/
                should_add = True
                if platform_name.lower() == "ycombinator":
                    if "/companies/" not in job_link:
                        print(f"Skipping YC non-job (not a /companies/ link): {job_link}")
                        should_add = False

                # Fetch job description
                job_description = "Description not found"
                if job_link != "Link not found":
                    try:
                        detail_page = await browser.new_page()
                        await detail_page.goto(job_link)
                        await asyncio.sleep(2)
                        desc_header_selector = ".ycdc-card.max-w-2xl"
                        
                        desc_selectors = [
                            '[class*="description"]', '[class*="job-details"]',
                            'article', '.prose', '.job-desc',
                        ]
                        
                        for selector in desc_selectors:
                            desc_elem = await detail_page.query_selector(selector)
                            if desc_elem:
                                if platform_name == "ycombinator":
                                    desc_header = await detail_page.query_selector(desc_header_selector)
                                    if desc_header:
                                        job_description = (await desc_header.inner_text()).strip() + (await desc_elem.inner_text()).strip()
                                    print(f"  [Debug] Found description + header with selector: {selector}, {desc_header_selector} ---{platform_name}")
                                    break
                                job_description = (await desc_elem.inner_text()).strip()
                                print(f"  [Debug] Found description with selector: {selector} ---{platform_name}")
                                break
                        
                        await detail_page.close()
                    except Exception as e:
                        print(f"Error fetching job description for {job_link}: {e}")

                if should_add and job_link != "Link not found" and job_description != "Description not found":
                    job_dict[job_link] = job_description
                    print(f"✅ Stored: {job_link[:50]}... JD chars: {len(job_description)} for role: {role} --job card of {i}")
            except Exception as e:
                print(f"Error processing job card {i} on {platform_name}: {e}")
                continue

        print(f"[{platform_name}] Extracted {len(job_dict)} jobs (url + JD).")
        return job_dict
    except Exception as e:
        print(f"Error on {platform_name}: {e}")
        return {}
    finally:
        await page.close()




# Configure Gemini API
genai.configure(api_key=GOOGLE_API)
model = genai.GenerativeModel('gemini-2.5-flash-lite-preview-06-17')


# def extract_all_jobs_at_once(jobs_dict: dict) -> list:
#     """
#     Process all jobs in a single API call to Gemini
    
#     Args:
#         jobs_dict: Dictionary with {url: job_description, ...}
    
#     Returns:
#         List of extracted job data dictionaries
#     """
    
#     print(f"Processing {len(jobs_dict)} jobs in a single API call...")
    
#     try:
#         # Create the prompt with all jobs
#         prompt = create_bulk_prompt(jobs_dict)
        
#         # Single API call for all jobs
#         response = model.generate_content(prompt)
        
#         # Parse the response
#         extracted_jobs = parse_bulk_response(response.text, jobs_dict)
        
#         print(f"Successfully processed {len(extracted_jobs)} jobs")
#         return extracted_jobs
        
#     except Exception as e:
#         print(f"Error processing jobs: {e}")
#         # Return fallback data for all jobs
#         return [create_fallback_data_from_dict(url, jd) for url, jd in jobs_dict.items()]

def create_bulk_prompt(jobs_dict: dict) -> str:

    SYSTEM_PROMPT ="""You are a professional job data extraction specialist. You will receive a dictionary where keys are job URLs and values are job descriptions. Extract structured information for ALL jobs and return a JSON array.

EXTRACTION RULES:
- Process every URL-JD pair in the dictionary
- Extract information ONLY from the job description text
- If information is not explicitly mentioned, use "Not specified"
- For Experience, look for experinece it may years like 3+,4+,5+0 or new grads or freshers etc
- For locations, look for city names, state/country, or "Remote" indicators  
- For posted_at or last_date to apply, look for phrases like "Posted 3 days ago", "2 weeks ago" or even timestamp or etc for posted date and deadline.
- Company names are often mentioned in phrases like "Join [Company]", "About [Company] or it may specified in url after the phrase of '/companies/'"
-  For Salary, look for salary it may specified in  usd or INR or any other currency dont use currency symbols code use direct symbol or just specify currency name like USD or INR or Yen etc
- Infer platform/source from the URL domain (e.g., ycombinator.com → "ycombinator")

REQUIRED OUTPUT FORMAT:
Return a JSON array with one object per job:
[
  {
    "title": "extracted job title",
    "company_name": "extracted company name",
    "location": "city, state/country or Remote", 
    "Experience": "experience specified",
    "Salary": "salary in currency value and amount with proper symbol DONT MENTION ANY SYSMBOL CODES or name of the currency"
    "job_url": "the URL key from input",
    "posted_at" or "last_date": "time posted" or "last date",
    "job_description": "full job description text",
    "source": "platform name inferred from URL",
  }
]

IMPORTANT: 
- Return ONLY the JSON array, no additional text
- Process ALL jobs in the dictionary
- Maintain the same order as the input dictionary"""

    """Create a single prompt for all jobs"""
    
    prompt = f"""{SYSTEM_PROMPT}

You will receive {len(jobs_dict)} job descriptions as URL-JD pairs. Process ALL of them and return a JSON array with {len(jobs_dict)} objects.

JOBS TO PROCESS:
"""
    
    for idx, (url, jd) in enumerate(jobs_dict.items(), 1):
        prompt += f"""

--- JOB {idx} ---
URL: {url}
JOB DESCRIPTION:
{jd}
--- END JOB {idx} ---
"""
    
    prompt += f"""

Return a JSON array with exactly {len(jobs_dict)} objects, one for each job in the same order they were provided above."""
    
    # print(prompt)
    return prompt

def parse_bulk_response(response_text: str, original_jobs: dict) -> list:
    """Parse Gemini's response for all jobs"""
    
    try:

        # Clean the response
        clean_response = response_text.strip()
        if clean_response.startswith('```json'):
            clean_response = clean_response[7:].lstrip()
        elif clean_response.startswith('```'):
            clean_response = clean_response[3:].lstrip()
        if clean_response.endswith('```'):
            clean_response = clean_response[:-3].rstrip()
        
        with open("gemini_raw_response.json", "w", encoding="utf-8") as f:
            f.write(clean_response)
        # Parse JSON
        extracted_jobs = json.loads(clean_response)
        
        # Ensure it's a list
        if not isinstance(extracted_jobs, list):
            extracted_jobs = [extracted_jobs]
            print(f"{"="*60} extracted job sample: {extracted_jobs[(len(extracted_jobs)-1)]} {"="*60}")
        
        # Validate and ensure we have data for all jobs
        job_urls = list(original_jobs.keys())
        
        for i, job in enumerate(extracted_jobs):
            if i < len(job_urls):
                # Ensure URL matches and add missing fields
                job['job_url'] = job_urls[i]
                job['job_description'] = original_jobs[job_urls[i]]
                
                # Infer source from URL if not present
                if not job.get('source') or job['source'] == 'Not specified':
                    job['source'] = infer_source_from_url(job_urls[i])
        
        # If we got fewer results than expected, add fallbacks
        while len(extracted_jobs) < len(job_urls):
            idx = len(extracted_jobs)
            url = job_urls[idx]
            fallback_job = create_fallback_data_from_dict(url, original_jobs[url])
            extracted_jobs.append(fallback_job)
        
        return extracted_jobs
        
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print(f"Response was: {response_text[:500]}...")
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
    """Process jobs in batches of 50 to balance efficiency and reliability"""
    all_extracted = []
    job_items = list(jobs_dict.items())
    total_batches = (len(job_items) + batch_size - 1) // batch_size
    
    print(f"Processing {len(job_items)} jobs in {total_batches} batches of {batch_size}")
    
    for i in range(0, len(job_items), batch_size):
        batch_dict = dict(job_items[i:i + batch_size])
        batch_num = (i // batch_size) + 1
        
        print(f"Processing batch {batch_num}/{total_batches}: {len(batch_dict)} jobs")
        
        try:
            # Use your existing extract_all_jobs_at_once function for each batch
            batch_result = await extract_single_batch(batch_dict)
            all_extracted.extend(batch_result)
            print(f"✅ Batch {batch_num} completed: {len(batch_result)} jobs processed")
            
        except Exception as e:
            print(f"❌ Batch {batch_num} failed: {e}")
            # Add fallback data for failed batch
            fallback_jobs = [create_fallback_data_from_dict(url, jd) 
                           for url, jd in batch_dict.items()]
            all_extracted.extend(fallback_jobs)
        
        # Rate limiting between batches (adjust as needed)
        if batch_num < total_batches:
            await asyncio.sleep(3)
    
    print(f"Total jobs processed: {len(all_extracted)}")
    return all_extracted

async def extract_single_batch(batch_dict: dict) -> list:
    """Process a single batch - reuse your existing logic"""
    try:
        prompt = create_bulk_prompt(batch_dict)
        response = model.generate_content(prompt)
        extracted_jobs = parse_bulk_response(response.text, batch_dict)
        return extracted_jobs
    except Exception as e:
        print(f"Error in batch processing: {e}")
        return [create_fallback_data_from_dict(url, jd) for url, jd in batch_dict.items()]



async def search_web_dev_jobs(role="web-developer", platforms=None):
    if platforms is None:
        platforms = list(PLATFORMS.keys())
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        tasks = [
            scrape_platform(browser, platform, PLATFORMS[platform], role)
            for platform in platforms
        ]
        results = await asyncio.gather(*tasks)
        await browser.close()
        # Merge all job dicts
        all_jobs = {}
        for platform_result in results:
            all_jobs.update(platform_result)
        print(f"\n{'='*60}\nTOTAL JOBS SCRAPED: {len(all_jobs)}\n{'='*60}")


        extractedJobs = await extract_jobs_in_batches(all_jobs, batch_size=50)
        print(f"{"="*30} extrated job after gemini {extractedJobs[0]} {"="*30}")

        # Save to JSON
        with open("jobs_urls_jds.json", "w", encoding="utf-8") as f:
            json.dump(all_jobs, f, indent=2)
        with open("jobs_after_gemini.json", "w", encoding="utf-8") as f:
            json.dump(extractedJobs, f, indent=2)
        print("Sample:")
        for i, (url, jd) in enumerate(list(all_jobs.items())[:3]):
            print(f"\nURL: {url}\nJD Preview: {jd[:200]}\n{'-'*40}")
        return all_jobs

async def main():
    with open("jobs_urls_jds.json", "r", encoding="utf-8") as file:
        data_dict = json.load(file)
    
    # Use batch processing instead of single request
    extracted = await extract_jobs_in_batches(data_dict, batch_size=50)
    
    with open("extract_job_data.json", "w", encoding="utf-8") as file:
        json.dump(extracted, file, indent=2, ensure_ascii=False)
    
    print(f"Successfully extracted data for {len(extracted)} jobs")

if __name__ == "__main__":
    # asyncio.run(search_web_dev_jobs())
    asyncio.run(main())
