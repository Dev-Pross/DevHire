import json
import asyncio
import os
import sys
import re

from playwright.async_api import async_playwright

# Import config from correct location (backend_python/config.py)
sys.path.append(os.path.dirname(__file__))
from config import LINKEDIN_ID, LINKEDIN_PASSWORD

LINKEDIN_FEED_URL = "https://www.linkedin.com/feed/"
LINKEDIN_LOGIN_URL = "https://www.linkedin.com/login"
LINKEDIN_JOBS_URL = "https://www.linkedin.com/jobs/"

def extract_keywords_from_resume0_tex(tex_path=None):
    """
    Extract keywords from resume0.tex by looking for skill, technology, and capitalized words.
    This is a simple parser for LaTeX resume files.
    Tries D:/DevHire/backend_python/resume0.tex first, then backend_python/resume0.tex.
    """
    possible_paths = []
    if tex_path is not None:
        possible_paths.append(tex_path)
    else:
        possible_paths = [
            r"D:\DevHire\backend_python\resume0.tex",
            "backend_python/resume0.tex"
        ]
    for path in possible_paths:
        if os.path.exists(path):
            tex_path = path
            break
    else:
        print(f"resume0.tex not found at any of: {possible_paths}")
        return []
    with open(tex_path, "r", encoding="utf-8") as f:
        text = f.read()
    # Remove LaTeX commands
    text = re.sub(r"\\[a-zA-Z]+\{[^}]*\}", " ", text)
    text = re.sub(r"\\[a-zA-Z]+\s*", " ", text)
    text = re.sub(r"\{|\}|\[|\]|%.*", " ", text)
    # Lowercase for matching
    text_lower = text.lower()
    tech_terms = [
        "python", "java", "c++", "javascript", "sql", "aws", "azure", "docker", "kubernetes",
        "machine learning", "data science", "react", "node", "typescript", "django", "flask",
        "pandas", "numpy", "tensorflow", "pytorch", "linux", "git", "html", "css"
    ]
    found_terms = set()
    for term in tech_terms:
        if term in text_lower:
            found_terms.add(term)
    # Add capitalized words (likely job titles, skills, etc.)
    cap_words = set(re.findall(r"\b([A-Z][a-zA-Z]{2,})\b", text))
    stopwords = {"and", "the", "for", "with", "from", "this", "that", "have", "are", "was", "has", "will", "can"}
    cap_words = {w for w in cap_words if w.lower() not in stopwords}
    # Combine and return as list
    keywords = list(found_terms) + list(cap_words)
    # Remove duplicates, keep order
    seen = set()
    result = []
    for k in keywords:
        if k.lower() not in seen:
            result.append(k)
            seen.add(k.lower())
    return result[:10]  # Limit to 10 keywords for search

async def login_if_required(page, username, password):
    await page.goto(LINKEDIN_FEED_URL, wait_until="networkidle")
    # Check if login is required
    if page.url.startswith(LINKEDIN_LOGIN_URL) or await page.locator('input#username').count() > 0:
        print("Login required, performing login...")
        await page.fill('input#username', username)
        await page.fill('input#password', password)
        await page.click('button[type="submit"]')
        for _ in range(30):
            await asyncio.sleep(1)
            curr_url = page.url
            if "/feed" in curr_url:
                print("Logged in successfully!")
                return True
            if any(x in curr_url for x in ["/checkpoint", "/captcha", "/login"]):
                print(f"Encountered checkpoint at {curr_url}. Manual intervention probably needed.")
                return False
        print("Timeout waiting for feed after login.")
        return False
    else:
        print("Already logged in.")
        return True

async def get_all_jobs_for_keyword(context, keyword, max_pages=5):
    """
    Search for jobs using a keyword and return all jobs (not just first 10).
    Returns: list of job dicts with title, link, company, location, description.
    """
    jobs = []
    page = await context.new_page()
    await page.goto(LINKEDIN_JOBS_URL, wait_until="domcontentloaded")
    await asyncio.sleep(2)
    # Try multiple selectors for the search input
    search_input = None
    selectors = [
        'input[aria-label*="Search by title, skill, or company"]',
        'input[placeholder*="Search job titles"]',
        'input[aria-label*="Search jobs"]'
    ]
    for sel in selectors:
        locator = page.locator(sel)
        if await locator.count() > 0:
            search_input = locator.first
            break
    if not search_input:
        print(f"Could not find search input for keyword: {keyword}")
        await page.close()
        return []
    await search_input.fill(keyword)
    await page.keyboard.press("Enter")
    await asyncio.sleep(4)  # Wait for search results to load

    # Wait for job cards to appear
    try:
        await page.wait_for_selector('a[href*="/jobs/view/"]', timeout=15000)
    except Exception:
        print(f"No jobs found for keyword: {keyword}")
        await page.close()
        return []

    # Try to get total number of jobs (if available)
    total_jobs = None
    try:
        count_text = await page.locator('span.results-context-header__job-count').first.inner_text()
        total_jobs = int(re.sub(r"[^\d]", "", count_text))
    except Exception:
        total_jobs = None

    # Scroll and paginate to get all jobs
    jobs_seen = set()
    page_num = 0
    while True:
        await asyncio.sleep(2)
        job_cards = await page.locator('li.jobs-search-results__list-item').all()
        if not job_cards:
            break
        for card in job_cards:
            try:
                # Get job link
                link_el = card.locator('a[href*="/jobs/view/"]')
                if await link_el.count() == 0:
                    continue
                href = await link_el.first.get_attribute('href')
                job_url = f"https://www.linkedin.com{href}" if href and href.startswith('/') else href
                if not job_url or job_url in jobs_seen:
                    continue
                jobs_seen.add(job_url)

                # Get job title
                title = await card.locator('span[aria-hidden="true"]').first.inner_text() if await card.locator('span[aria-hidden="true"]').count() > 0 else ""
                # Get company name
                company = await card.locator('a[data-control-name*="company"] span').first.inner_text() if await card.locator('a[data-control-name*="company"] span').count() > 0 else ""
                # Get location
                location = await card.locator('span.job-search-card__location').first.inner_text() if await card.locator('span.job-search-card__location').count() > 0 else ""
                # Click to load description
                try:
                    await link_el.first.click()
                    await asyncio.sleep(1.5)
                except Exception:
                    pass
                # Try to get job description from the right panel
                desc = ""
                try:
                    desc_el = page.locator('div.jobs-description-content__text, div.jobs-description__container')
                    if await desc_el.count() > 0:
                        desc = await desc_el.first.inner_text()
                except Exception:
                    desc = ""
                jobs.append({
                    "job_title": title.strip(),
                    "application_link": job_url,
                    "company": company.strip(),
                    "location": location.strip(),
                    "description": desc.strip(),
                    "keyword": keyword
                })
            except Exception as e:
                print(f"Error extracting job card: {e}")

        # Try to click "next" for pagination
        next_btn = page.locator('button[aria-label*="Page next"], button[aria-label="Next"]')
        if await next_btn.count() > 0 and not await next_btn.first.is_disabled():
            try:
                await next_btn.first.click()
                page_num += 1
                await asyncio.sleep(3)
                if max_pages and page_num >= max_pages:
                    break
            except Exception:
                break
        else:
            break

    await page.close()
    print(f"Found {len(jobs)} jobs for keyword: {keyword}")
    return jobs

async def main():
    resume_tex_path = None  # Let extract_keywords_from_resume0_tex handle the path logic
    keywords = extract_keywords_from_resume0_tex(resume_tex_path)
    if not keywords:
        print("No keywords extracted from resume0.tex. Please check your resume file.")
        return
    print(f"Extracted keywords from resume0.tex: {keywords}")

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context()

    # Create initial page for login
    main_page = await context.new_page()

    # Login using credentials from config
    if not await login_if_required(main_page, LINKEDIN_ID, LINKEDIN_PASSWORD):
        print("Login failed, exiting.")
        await context.close()
        await browser.close()
        await playwright.stop()
        return

    print("Successfully logged in! Starting job search...")

    all_jobs = []

    # Search for each keyword and collect all job details (all pages)
    for i, keyword in enumerate(keywords):
        print(f"\nSearching for jobs with keyword: {keyword}")
        jobs = await get_all_jobs_for_keyword(context, keyword, max_pages=10)
        all_jobs.extend(jobs)
        print(f"Total jobs found so far: {len(all_jobs)}")

    # Remove duplicates by application_link
    seen_links = set()
    unique_jobs = []
    for job in all_jobs:
        if job["application_link"] and job["application_link"] not in seen_links:
            unique_jobs.append(job)
            seen_links.add(job["application_link"])

    print(f"\nTotal unique jobs found: {len(unique_jobs)}")

    # Output all found jobs as JSON to stdout
    print(json.dumps(unique_jobs, indent=2, ensure_ascii=False))

    await context.close()
    await browser.close()
    await playwright.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exiting on user interrupt.")
