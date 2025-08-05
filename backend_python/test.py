import asyncio
import os
import sys
import re
from playwright.async_api import async_playwright

# Import config from correct location (backend_python/config.py)
sys.path.append(os.path.dirname(__file__))
from config import LINKEDIN_ID, LINKEDIN_PASSWORD

LINKEDIN_LOGIN_URL = "https://www.linkedin.com/login"
LINKEDIN_JOBS_URL = "https://www.linkedin.com/jobs/"

def extract_keywords_and_titles_from_resume0_tex(tex_path=None):
    """
    Extract keywords and job titles from resume0.tex.
    - Keywords: skills, technologies, capitalized words.
    - Titles: from \resumeSubheading and section headers.
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
        return [], []
    with open(tex_path, "r", encoding="utf-8") as f:
        text = f.read()
    text_nocomment = re.sub(r"%.*", "", text)
    text_clean = re.sub(r"\\[a-zA-Z]+\{[^}]*\}", " ", text_nocomment)
    text_clean = re.sub(r"\\[a-zA-Z]+\s*", " ", text_clean)
    text_clean = re.sub(r"\{|\}|\[|\]", " ", text_clean)
    text_lower = text_clean.lower()
    tech_terms = [
        "python", "java", "c++", "javascript", "sql", "aws", "azure", "docker", "kubernetes",
        "machine learning", "data science", "react", "node", "typescript", "django", "flask",
        "pandas", "numpy", "tensorflow", "pytorch", "linux", "git", "html", "css"
    ]
    found_terms = set()
    for term in tech_terms:
        if term in text_lower:
            found_terms.add(term)
    cap_words = set(re.findall(r"\b([A-Z][a-zA-Z]{2,})\b", text_clean))
    stopwords = {"and", "the", "for", "with", "from", "this", "that", "have", "are", "was", "has", "will", "can"}
    cap_words = {w for w in cap_words if w.lower() not in stopwords}
    keywords = list(found_terms) + list(cap_words)
    seen = set()
    result_keywords = []
    for k in keywords:
        if k.lower() not in seen:
            result_keywords.append(k)
            seen.add(k.lower())
    result_keywords = result_keywords[:5]
    titles = []
    for m in re.finditer(r"\\resumeSubheading\{([^\}]*)\}", text_nocomment):
        title = m.group(1).strip()
        if title and title.lower() not in ("", "education"):
            titles.append(title)
    for m in re.finditer(r"\\section\*?\{([^\}]*)\}", text_nocomment):
        sec = m.group(1).strip()
        if sec and sec.lower() not in ("summary", "education", "skills", "projects", "additional information"):
            titles.append(sec)
    seen_titles = set()
    result_titles = []
    for t in titles:
        t_norm = t.lower()
        if t_norm not in seen_titles and t_norm not in ("", "education"):
            result_titles.append(t)
            seen_titles.add(t_norm)
    return result_keywords, result_titles

async def linkedin_login(page, username, password):
    await page.goto(LINKEDIN_LOGIN_URL)
    await page.fill('input#username', username)
    await page.fill('input#password', password)
    await page.click('button[type="submit"]')
    await page.wait_for_load_state('networkidle')
    # Check if login was successful
    if "feed" in page.url or "jobs" in page.url:
        return True
    # If still on login page, login failed
    if "login" in page.url:
        return False
    return True

async def scrap_linkedin_jobs(context, keyword, max_jobs=10):
    jobs = []
    page = await context.new_page()
    await page.goto(LINKEDIN_JOBS_URL, wait_until="domcontentloaded")
    await asyncio.sleep(2)
    # Find the search input
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
        await page.close()
        return []
    await search_input.fill(keyword)
    await page.keyboard.press("Enter")
    await asyncio.sleep(4)
    try:
        await page.wait_for_selector('li.jobs-search-results__list-item', timeout=15000)
    except Exception:
        await page.close()
        return []
    jobs_seen = set()
    total_found = 0
    while total_found < max_jobs:
        await asyncio.sleep(2)
        job_cards = await page.locator('li.jobs-search-results__list-item').all()
        if not job_cards:
            break
        for card in job_cards:
            if total_found >= max_jobs:
                break
            try:
                link_el = card.locator('a[href*="/jobs/view/"]')
                if await link_el.count() == 0:
                    continue
                href = await link_el.first.get_attribute('href')
                job_url = f"https://www.linkedin.com{href}" if href and href.startswith('/') else href
                if not job_url or job_url in jobs_seen:
                    continue
                jobs_seen.add(job_url)
                title = await card.locator('span[aria-hidden="true"]').first.inner_text() if await card.locator('span[aria-hidden="true"]').count() > 0 else ""
                company = await card.locator('a[data-control-name*="company"] span').first.inner_text() if await card.locator('a[data-control-name*="company"] span').count() > 0 else ""
                location = await card.locator('span.job-search-card__location').first.inner_text() if await card.locator('span.job-search-card__location').count() > 0 else ""
                try:
                    await link_el.first.click()
                    await asyncio.sleep(1.2)
                except Exception:
                    pass
                desc = ""
                try:
                    desc_el = page.locator('div.jobs-description-content__text, div.jobs-description__container, div.jobs-description__content, div.description__text')
                    if await desc_el.count() > 0:
                        await desc_el.first.scroll_into_view_if_needed()
                        desc = await desc_el.first.inner_text()
                    if not desc.strip():
                        desc_alt = await card.locator('[aria-label*="description"], [data-test-description]').all_inner_texts()
                        if desc_alt:
                            desc = desc_alt[0]
                except Exception:
                    desc = ""
                if not desc.strip():
                    try:
                        desc = await card.inner_text()
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
                total_found += 1
            except Exception:
                pass
        # Pagination
        if total_found < max_jobs:
            next_btn = page.locator('button[aria-label*="Page next"], button[aria-label="Next"]')
            if await next_btn.count() > 0 and not await next_btn.first.is_disabled():
                try:
                    await next_btn.first.click()
                    await asyncio.sleep(3)
                except Exception:
                    break
            else:
                break
        else:
            break
    await page.close()
    return jobs

async def main():
    resume_tex_path = None
    keywords, titles = extract_keywords_and_titles_from_resume0_tex(resume_tex_path)
    if not keywords and not titles:
        print("No keywords or titles extracted from resume0.tex. Please check your resume file.")
        return
    search_terms = keywords + [t for t in titles if t not in keywords]
    if not search_terms:
        print("No search terms found from resume.")
        return
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context()
    page = await context.new_page()
    # Login
    login_success = await linkedin_login(page, LINKEDIN_ID, LINKEDIN_PASSWORD)
    if not login_success:
        print("Login failed, exiting.")
        await context.close()
        await browser.close()
        await playwright.stop()
        return
    all_jobs = []
    for i, keyword in enumerate(search_terms):
        jobs = await scrap_linkedin_jobs(context, keyword, max_jobs=10)
        all_jobs.extend(jobs)
    await context.close()
    await browser.close()
    await playwright.stop()
    # Print jobs
    if not all_jobs:
        print("No jobs found for any keyword/title.")
    else:
        print(f"Total jobs found: {len(all_jobs)}")
        for idx, job in enumerate(all_jobs, 1):
            print(f"\nJob {idx}:")
            print(f"  Title: {job['job_title']}")
            print(f"  Company: {job['company']}")
            print(f"  Location: {job['location']}")
            print(f"  Link: {job['application_link']}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exiting on user interrupt.")
