import asyncio
import json
import sys
import re
from datetime import datetime
from typing import Dict, List, Any, Optional

# Optional third-party imports - handle missing packages gracefully so static analyzers / runtime show clear messages.
try:
    import aiohttp
except Exception:
    aiohttp = None
    print("Missing dependency: aiohttp (install with: pip install aiohttp)")

try:
    from playwright.async_api import async_playwright
except Exception:
    async_playwright = None
    print("Missing dependency: playwright (install with: pip install playwright) and run: playwright install")

try:
    from google import genai
    from google.genai import types
except Exception:
    genai = None
    types = None
    print("Missing dependency: google-genai (install the Google GenAI SDK to enable Gemini extraction)")

# Local config (must exist)
try:
    from config import GOOGLE_API, LINKEDIN_ID, LINKEDIN_PASSWORD
except Exception:
    GOOGLE_API = None
    LINKEDIN_ID = ""
    LINKEDIN_PASSWORD = ""

# Basic color helper so prints earlier in the file work
class Colors:
    END = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"

# Windows Playwright fix (only run when relevant)
if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception:
        pass

# Configuration
LINKEDIN_CONFIG = {
    "login_url": "https://www.linkedin.com/login",
    "api_jobs_endpoint": "https://www.linkedin.com/voyager/api/voyagerJobsDashJobCards",
}

# Safe defaults
MODEL_NAME = "gemini-1.0"  # placeholder model name

# Initialize Gemini client if available
client = None
if genai is not None and GOOGLE_API:
    try:
        client = genai.Client(api_key=GOOGLE_API)
    except Exception as e:
        client = None
        print(f"{Colors.RED}❌ Failed to create Gemini client: {e}{Colors.END}")
else:
    print(f"{Colors.YELLOW}⚠️ Gemini client not available - google-genai SDK not installed or API key missing{Colors.END}")

# ---------------------------------------------------------------------------
# STEP 1: LOGIN
# ---------------------------------------------------------------------------
async def linkedin_login_and_get_cookies() -> Optional[Dict[str, Any]]:
    """
    Login to LinkedIn using Playwright and return authenticated cookies.
    This is done ONCE at the start - much faster than opening browser for every job.
    If Playwright is not installed, return None.
    """
    print(f"{Colors.CYAN}🔐 Step 1: Authenticating with LinkedIn...{Colors.END}")
    if async_playwright is None:
        print(f"{Colors.RED}❌ Playwright is not installed or not available - install playwright to enable login{Colors.END}")
        return None

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
            )

            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                viewport={"width": 1920, "height": 1080}
            )

            page = await context.new_page()

            # Navigate to login
            await page.goto(LINKEDIN_CONFIG["login_url"], timeout=30000)
            await asyncio.sleep(1)
            print("   📧 Entering credentials...")
            await page.fill('#username', LINKEDIN_ID)
            await page.fill('#password', LINKEDIN_PASSWORD)
            await page.click('button[type="submit"]')
            await asyncio.sleep(4)

            current_url = page.url
            if "checkpoint" in current_url:
                print(f"{Colors.YELLOW}⚠️ LinkedIn security checkpoint detected - please login manually once{Colors.END}")
                await browser.close()
                return None

            # Extract cookies and csrf
            cookies = await context.cookies()
            cookie_dict = {c['name']: c['value'] for c in cookies}
            csrf_token = cookie_dict.get('JSESSIONID', '') or cookie_dict.get('li_at', '')
            if isinstance(csrf_token, str):
                csrf_token = csrf_token.strip('"')

            await browser.close()
            print(f"{Colors.GREEN}✅ Authentication complete - cookies extracted{Colors.END}")
            return {'cookies': cookie_dict, 'csrf_token': csrf_token}
    except Exception as e:
        print(f"{Colors.RED}❌ Login error: {e}{Colors.END}")
        return None

# ---------------------------------------------------------------------------
# STEP 2: FAST JOB SEARCH WITH AIOHTTP
# ---------------------------------------------------------------------------
async def search_jobs_via_api(session, job_title, start=0, count=25):
    """
    Search jobs using LinkedIn's internal API.
    """
    url = LINKEDIN_CONFIG["api_jobs_endpoint"]
    params = {
        "decorationId": "com.linkedin.voyager.dash.deco.jobs.search.JobSearchCardsCollection-174",
        "count": count,
        "start": start,
        "keywords": job_title
    }
    req_headers = {
        "Accept": "application/json",
        "x-restli-protocol-version": "2.0.0"
    }

    try:
        async with session.get(url, params=params, headers=req_headers, timeout=15) as resp:
            text = await resp.text()
            if resp.status == 200:
                cleaned = text.strip()
                cleaned = re.sub(r'^[^\{\[]+', '', cleaned)
                try:
                    return json.loads(cleaned)
                except Exception:
                    return {}
            else:
                print(f"   {Colors.RED}❌ API search failed: HTTP {resp.status}{Colors.END}")
                return {}
    except Exception as e:
        print(f"   {Colors.RED}❌ API request error: {e}{Colors.END}")
        return {}

def extract_job_urls_from_api_response(api_response: dict) -> List[Dict[str, Any]]:
    """
    Extract job URLs and basic info from LinkedIn API response.
    """
    jobs = []
    if not api_response:
        return []

    def find_job_postings(obj):
        found = []
        if isinstance(obj, dict):
            if 'jobPostingId' in obj or (obj.get('$type') and 'JobPosting' in obj.get('$type', '')) or ('entityUrn' in obj and 'jobPosting' in obj.get('entityUrn', '')):
                found.append(obj)
            for v in obj.values():
                found.extend(find_job_postings(v))
        elif isinstance(obj, list):
            for item in obj:
                found.extend(find_job_postings(item))
        return found

    postings = find_job_postings(api_response)
    for element in postings:
        job_id = element.get('jobPostingId') or element.get('id') or element.get('jobId')
        if not job_id:
            urn = element.get('entityUrn', '') or element.get('urn', '')
            if isinstance(urn, str) and ':' in urn:
                job_id = urn.split(':')[-1]
        if job_id:
            job_url = f"https://www.linkedin.com/jobs/view/{job_id}/"
            title = element.get('title', '') or element.get('positionTitle', '')
            company = element.get('companyName', '') or (element.get('company') or {}).get('name', '')
            jobs.append({'url': job_url, 'title': title, 'company': company, 'id': job_id})

    # Deduplicate
    seen = set()
    unique = []
    for j in jobs:
        if j['url'] not in seen:
            seen.add(j['url'])
            unique.append(j)
    return unique

# ---------------------------------------------------------------------------
# STEP 3: FETCH JOB DESCRIPTIONS
# ---------------------------------------------------------------------------
async def get_job_description_fast(session, job_url: str) -> str:
    try:
        async with session.get(job_url, timeout=15) as response:
            if response.status == 200:
                html = await response.text()
                patterns = [
                    r'<div class="show-more-less-html__markup[^\"]*"[^>]*>(.*?)</div>',
                    r'<div class="jobs-description__content[^\"]*"[^>]*>(.*?)</div>',
                    r'<article class="jobs-description[^\"]*"[^>]*>(.*?)</article>'
                ]
                for pattern in patterns:
                    match = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
                    if match:
                        desc_html = match.group(1)
                        desc_text = re.sub(r'<[^>]+>', ' ', desc_html)
                        desc_text = re.sub(r'\s+', ' ', desc_text).strip()
                        if len(desc_text) > 100:
                            return desc_text[:3000]
                return "Description not found"
            else:
                return f"Failed to fetch: HTTP {response.status}"
    except asyncio.TimeoutError:
        return "Timeout fetching description"
    except Exception as e:
        return f"Error: {str(e)[:100]}"

async def process_jobs_parallel(session, jobs: List[Dict[str, Any]], max_workers=10) -> Dict[str, str]:
    semaphore = asyncio.Semaphore(max_workers)

    async def fetch_with_limit(job):
        async with semaphore:
            url = job['url']
            desc = await get_job_description_fast(session, url)
            return url, desc

    print(f"   ⚡ Processing {len(jobs)} jobs with {max_workers} parallel workers...")
    tasks = [fetch_with_limit(job) for job in jobs]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    jobs_dict = {}
    success_count = 0
    for result in results:
        if isinstance(result, tuple):
            url, desc = result
            if desc and len(desc) > 50:
                jobs_dict[url] = desc
                success_count += 1

    print(f"   {Colors.GREEN}✅ Successfully fetched {success_count}/{len(jobs)} descriptions{Colors.END}")
    return jobs_dict

# ---------------------------------------------------------------------------
# STEP 4: MAIN SCRAPER
# ---------------------------------------------------------------------------
async def scrape_jobs_optimized(job_titles: List[str], auth_data: Dict[str, Any], progress=None, user_id=None) -> Dict[str, str]:
    print(f"\n{Colors.CYAN}{Colors.BOLD}🚀 Step 2: Fast job scraping with HTTP requests{Colors.END}")
    print(f"   Searching for {len(job_titles)} job titles...")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
        'csrf-token': auth_data.get('csrf_token', ''),
        'x-li-lang': 'en_US',
        'x-restli-protocol-version': '2.0.0',
        'x-li-track': '{"clientVersion":"1.13.0"}',
        'Referer': 'https://www.linkedin.com/jobs/search/'
    }

    all_jobs = {}
    processed_urls = set()

    if aiohttp is None:
        print(f"{Colors.RED}❌ aiohttp not installed - cannot proceed{Colors.END}")
        return {}

    connector = aiohttp.TCPConnector(limit=20, limit_per_host=10)
    timeout = aiohttp.ClientTimeout(total=30, connect=10)

    async with aiohttp.ClientSession(
        cookies=auth_data.get('cookies', {}),
        headers=headers,
        connector=connector,
        timeout=timeout
    ) as session:
        for idx, job_title in enumerate(job_titles, 1):
            print(f"\n{'='*70}")
            print(f"{Colors.BOLD}🔍 [{idx}/{len(job_titles)}] Searching: '{job_title}'{Colors.END}")
            print(f"{'='*70}")

            all_job_data = []
            for page_num in range(3):
                response = await search_jobs_via_api(session, job_title, start=page_num * 25, count=25)
                if response:
                    jobs = extract_job_urls_from_api_response(response)
                    new_jobs = [j for j in jobs if j['url'] not in processed_urls]
                    for job in new_jobs:
                        processed_urls.add(job['url'])
                    all_job_data.extend(new_jobs)
                    print(f"      ✅ Found {len(new_jobs)} new jobs")
                await asyncio.sleep(0.2)

            print(f"\n   📊 Total unique jobs for '{job_title}': {len(all_job_data)}")

            if all_job_data:
                jobs_dict = await process_jobs_parallel(session, all_job_data, max_workers=10)
                all_jobs.update(jobs_dict)
                print(f"   {Colors.GREEN}✅ Added {len(jobs_dict)} jobs to collection{Colors.END}")

            if progress is not None and user_id is not None:
                # simple progress update
                progress[user_id] = min(100, progress.get(user_id, 0) + (75 / max(len(job_titles), 1)))
                print(f"   📈 Progress: {progress[user_id]:.1f}%")

            await asyncio.sleep(0.5)

    print(f"\n{Colors.GREEN}{Colors.BOLD}✅ Scraping complete! Total unique jobs: {len(all_jobs)}{Colors.END}")
    return all_jobs

# ---------------------------------------------------------------------------
# STEP 5: GEMINI EXTRACTION (BATCHED, with fallbacks)
# ---------------------------------------------------------------------------
def create_bulk_prompt(jobs_dict: Dict[str, str]) -> str:
    system_instruction = """You are a professional job data extractor.

For each job entry, extract these fields:
- title, job_id, company_name, location, experience, salary, key_skills, job_url, posted_at, job_description, source, relevance_score

Output ONLY a pure JSON array. No explanations.
"""
    prompt = system_instruction + f"\n\nExtract data from these {len(jobs_dict)} jobs:\n\n"
    # Provide each job as a simple JSON line (Gemini will be asked to parse)
    for url, desc in jobs_dict.items():
        prompt += json.dumps({'job_url': url, 'job_description': desc}, ensure_ascii=False) + "\n"
    return prompt

def parse_gemini_response(text: str, batch_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Attempt to parse JSON from Gemini; fallback to constructing minimal records.
    """
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return parsed
    except Exception:
        pass

    # Fallback: create entries from batch_dict
    results = []
    for url, desc in batch_dict.items():
        results.append({
            "title": None,
            "job_id": url.rstrip('/').split('/')[-1],
            "company_name": None,
            "location": None,
            "experience": None,
            "salary": None,
            "key_skills": [],
            "job_url": url,
            "posted_at": None,
            "job_description": desc,
            "source": "linkedin",
            "relevance_score": None
        })
    return results

async def extract_batch_with_gemini(batch_dict: Dict[str, str], batch_num: int, total_batches: int) -> List[Dict[str, Any]]:
    print(f"   📦 Preparing Gemini extraction for batch {batch_num}/{total_batches} ({len(batch_dict)} jobs)")
    if client is None or types is None:
        print(f"   {Colors.YELLOW}⚠️ Gemini SDK not available - returning fallback structured data for this batch{Colors.END}")
        return parse_gemini_response("", batch_dict)

    prompt = create_bulk_prompt(batch_dict)
    max_retries = 2
    for attempt in range(max_retries):
        try:
            print(f"   🤖 Calling Gemini API for batch {batch_num}/{total_batches} (attempt {attempt + 1})...")
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.2)
            )
            text = getattr(response, "text", "") or str(response)
            # Save debug
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            debug_file = f"gemini_batch_{batch_num}_{timestamp}.txt"
            try:
                with open(debug_file, "w", encoding="utf-8") as f:
                    f.write(text)
            except Exception:
                pass

            extracted = parse_gemini_response(text, batch_dict)
            if extracted:
                print(f"   {Colors.GREEN}✅ Extracted {len(extracted)} jobs from batch{Colors.END}")
                return extracted
        except Exception as e:
            print(f"   {Colors.RED}❌ Gemini error (attempt {attempt + 1}): {e}{Colors.END}")
            await asyncio.sleep(1 + attempt)
    print(f"   {Colors.RED}❌ Failed to extract batch after {max_retries} attempts{Colors.END}")
    return parse_gemini_response("", batch_dict)

async def extract_all_jobs_with_gemini(all_jobs: Dict[str, str], batch_size: int = 50) -> List[Dict[str, Any]]:
    urls = list(all_jobs.keys())
    total = len(urls)
    if total == 0:
        return []
    results = []
    batches = [urls[i:i + batch_size] for i in range(0, total, batch_size)]
    for idx, batch_urls in enumerate(batches, 1):
        batch_dict = {u: all_jobs[u] for u in batch_urls}
        extracted = await extract_batch_with_gemini(batch_dict, idx, len(batches))
        if extracted:
            results.extend(extracted)
    return results

# ---------------------------------------------------------------------------
# MAIN / ENTRYPOINT
# ---------------------------------------------------------------------------
async def main(parsed_titles=None, parsed_keywords=None, progress=None, user_id=None, password=None):
    _ = parsed_keywords
    _ = password
    start_time = datetime.now()
    print(f"\n{'='*80}")
    print(f"{Colors.BOLD}{Colors.CYAN}🚀 OPTIMIZED LINKEDIN JOB SCRAPER{Colors.END}")
    print(f"{'='*80}")
    print(f"⏱️  Start time: {start_time.strftime('%H:%M:%S')}")

    job_titles = parsed_titles or [
        "Software Engineer",
        "Full Stack Developer",
        "Python Developer",
        "React Developer",
        "Backend Developer"
    ]

    if progress is not None and user_id is not None:
        progress[user_id] = 0

    auth_data = await linkedin_login_and_get_cookies()
    if not auth_data:
        print(f"{Colors.RED}❌ Authentication failed - exiting{Colors.END}")
        return []

    all_jobs = await scrape_jobs_optimized(job_titles, auth_data, progress, user_id)
    if not all_jobs:
        print(f"{Colors.RED}❌ No jobs found - exiting{Colors.END}")
        if progress is not None and user_id is not None:
            progress[user_id] = 100
        return []

    extracted_jobs = await extract_all_jobs_with_gemini(all_jobs, batch_size=50)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"jobs_optimized_{timestamp}.json"
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(extracted_jobs, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"{Colors.YELLOW}⚠️ Could not save results: {e}{Colors.END}")

    print(f"\n{'='*80}")
    print(f"{Colors.GREEN}{Colors.BOLD}✅ SCRAPING COMPLETE!{Colors.END}")
    print(f"{'='*80}")
    print(f"⏱️  Total time: {duration:.1f} seconds ({duration/60:.1f} minutes)")
    print(f"📄 Jobs extracted: {len(extracted_jobs)}")
    print(f"💾 Saved to: {filename}")
    print(f"🎯 Target met: {'✅ YES' if duration < 300 else '❌ NO (over 5 min)'}")
    try:
        speed_improve = int(1800 / duration) if duration > 0 else 0
    except Exception:
        speed_improve = 0
    print(f"⚡ Speed improvement: ~{speed_improve}x faster")
    print(f"{'='*80}\n")

    if progress is not None and user_id is not None:
        progress[user_id] = 100

    return extracted_jobs

def run_scraper_in_new_loop(titles, keywords, job_progress, user_id, password):
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(main(titles, keywords, job_progress, user_id, password))
            return result
        finally:
            loop.close()
    except Exception as e:
        print(f"{Colors.RED}❌ Scraper error: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    print("Starting optimized scraper...")
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"{Colors.RED}❌ Fatal error: {e}{Colors.END}")
