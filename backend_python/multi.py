import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# Top 10 job board URLs for developers
JOB_BOARDS = [
    ("LinkedIn", "https://www.linkedin.com/jobs/search/?keywords=web%20developer&location=United%20States"),
    # ("Indeed", "https://www.indeed.com/jobs?q=web+developer&l="),
    # ("Stack Overflow", "https://stackoverflow.com/jobs?r=true&q=web+developer"),
    # ("AngelList", "https://wellfound.com/jobs"),
    # ("Glassdoor", "https://www.glassdoor.com/Job/web-developer-jobs-SRCH_KO0,14.htm"),
    ("Remote OK", "https://remoteok.com/remote-web+developer-jobs"),
    ("We Work Remotely", "https://weworkremotely.com/remote-jobs/search?term=web+developer"),
    # ("Dice", "https://www.dice.com/jobs?q=web+developer"),
    # ("Hired", "https://hired.com/job-search/software-engineer"),
    ("Y Combinator", "https://www.ycombinator.com/jobs"),
]

# Updated selectors for each board (use lists for robustness)
SELECTORS = {
    "LinkedIn": [
        'a[href*="/jobs/view/"]',
        'a.job-card-list__title',
    ],
    "Indeed": [
        'a[data-jk]',
        'a.tapItem',
        'a.jobtitle',
    ],
    "Stack Overflow": [
        'div.js-result',
        'a.s-link',
    ],
    "AngelList": [
        'div[data-test="job-listing-title"]',
        'div.styles_component__jobCard',
        'a[href*="/jobs/"]',
    ],
    "Glassdoor": [
        'li.react-job-listing',
        'div.JobCard',
        'a.jobLink',
    ],
    "Remote OK": [
        'tr.job',
        'a.preventLink',
    ],
    "We Work Remotely": [
        'section.jobs li.feature',
        'li.feature',
    ],
    "Dice": [
        'a.card-title-link',
        'div.card',
    ],
    "Hired": [
        'div.job-card',
        'a.job-link',
    ],
    "Y Combinator": [
        'a[class^="styles_jobLink__"]',
        'a[href*="/companies/"]',
    ],
}

# Helper: Scroll to bottom to load more jobs (for infinite scroll sites)
def scroll_to_bottom(page, pause=1, max_scrolls=10):
    last_height = page.evaluate('() => document.body.scrollHeight')
    for _ in range(max_scrolls):
        page.evaluate('() => window.scrollTo(0, document.body.scrollHeight)')
        time.sleep(pause)
        new_height = page.evaluate('() => document.body.scrollHeight')
        if new_height == last_height:
            break
        last_height = new_height

# Helper: Make link absolute
def make_absolute_link(link, page_url):
    if not link:
        return ''
    if link.startswith('http'):
        return link
    if link.startswith('/'):
        base = page_url.split('/')[0] + '//' + page_url.split('/')[2]
        return base + link
    return link

# Extraction logic for each board (expand for more accuracy)
def extract_jobs(page, board_name):
    selectors = SELECTORS.get(board_name, ['a'])
    jobs = []
    found = False
    for selector in selectors:
        selector = selector.strip()
        try:
            print(f"[DEBUG] Waiting for selector '{selector}' on {board_name}")
            page.wait_for_selector(selector, timeout=20000)
            if board_name in ["Indeed", "Glassdoor", "AngelList", "Stack Overflow"]:
                scroll_to_bottom(page, pause=1, max_scrolls=5)
            cards = page.query_selector_all(selector)
            print(f"[DEBUG] {board_name}: Found {len(cards)} elements for selector '{selector}'")
            if not cards:
                continue
            found = True
            for card in cards[:20]:  # Limit to 20 per board for demo
                try:
                    text = card.inner_text().strip()
                    # Try to get link from card or its children
                    link = card.get_attribute('href')
                    if not link:
                        # Try to find a child anchor
                        a_child = card.query_selector('a[href]')
                        if a_child:
                            link = a_child.get_attribute('href')
                    link = make_absolute_link(link, page.url)
                    # Only add jobs with a valid link and title
                    title = text.split('\n')[0][:80] if text else 'No Title'
                    if link and title and len(title) > 2:
                        jobs.append({
                            'board': board_name,
                            'title': title,
                            'link': link,
                            'preview': text[:120] + ('...' if len(text) > 120 else '')
                        })
                except Exception as e:
                    print(f"[DEBUG] Error extracting job card: {e}")
                    continue
            if found:
                break  # If jobs found with this selector, stop
        except PlaywrightTimeoutError:
            print(f"[DEBUG] Timeout for selector '{selector}' on {board_name}")
            continue
        except Exception as e:
            print(f"[Error] {board_name} ({selector}): {e}")
            continue
    if not found:
        print(f"[Timeout] No jobs found for {board_name} (selectors: {selectors})")
        # Print first 10 anchor tags and their text for manual inspection
        anchors = page.query_selector_all('a')
        print(f"[DEBUG] First 10 anchor tags on {board_name}:")
        for i, anchor in enumerate(anchors[:10]):
            try:
                href = anchor.get_attribute('href')
                text = anchor.inner_text().strip()
                print(f"  Anchor {i}: {text[:60]} -> {href}")
            except Exception as e:
                print(f"  [DEBUG] Error reading anchor {i}: {e}")
    return jobs

def scrape_yc_jobs():
    from playwright.sync_api import sync_playwright
    import time
    jobs = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        try:
            print("Navigating to Y Combinator jobs page...")
            page.goto("https://www.ycombinator.com/jobs")
            time.sleep(5)
            selectors_to_try = [
                'a[href*="/jobs/"]',
                '[data-testid*="job"]',
                '.job-card', '.job-listing', '.job-item',
                'article', '.card', '.listing',
                'div[class*="job"]', 'div[class*="listing"]',
                'li',
            ]
            job_cards = []
            for selector in selectors_to_try:
                cards = page.query_selector_all(selector)
                if cards:
                    print(f"Found {len(cards)} elements with selector: {selector}")
                    job_cards = cards
                    break
            if not job_cards:
                job_cards = page.query_selector_all('a, button, [role="button"]')
                print(f"Using fallback: Found {len(job_cards)} clickable elements")
            web_dev_keywords = [
                'web developer', 'frontend', 'backend', 'full stack', 'fullstack',
                'javascript', 'react', 'angular', 'vue', 'node.js', 'python',
                'html', 'css', 'php', 'ruby', 'java', 'developer', 'programmer',
                'software engineer', 'engineer', 'development', 'coding', 'programming'
            ]
            for i, card in enumerate(job_cards[:40]):
                try:
                    text_content = card.inner_text().strip()
                    if not text_content:
                        continue
                    has_web_dev_keyword = any(keyword in text_content.lower() for keyword in web_dev_keywords)
                    if has_web_dev_keyword:
                        title = "Title not found"
                        company = "Company not found"
                        job_link = "Link not found"
                        title_elements = card.query_selector_all('h1, h2, h3, h4, h5, h6')
                        if title_elements:
                            title = title_elements[0].inner_text().strip()
                        if title == "Title not found":
                            lines = text_content.split('\n')
                            if lines:
                                title = lines[0].strip()
                        # Company extraction
                        children = card.query_selector_all(':scope > *')
                        company = "Company not found"
                        company_candidates = []
                        if len(children) > 1:
                            for idx, child in enumerate(children):
                                child_text = child.inner_text().strip()
                                if child_text and child_text != title and 2 < len(child_text) < 50:
                                    company_candidates.append((idx, child_text))
                        if company_candidates:
                            company = company_candidates[0][1]
                        # Try to extract company from job link
                        if card.evaluate('el => el.tagName.toLowerCase()') == 'a':
                            job_link = card.get_attribute('href')
                            if job_link is None:
                                job_link = ""
                        else:
                            link_elem = card.query_selector('a[href*="job"], a[href*="apply"]')
                            job_link = link_elem.get_attribute('href') if link_elem else ""
                            if job_link is None:
                                job_link = ""
                        import re
                        m = re.match(r"/companies/([\w\-]+)/jobs/", job_link)
                        if m:
                            company_from_link = m.group(1).replace('-', ' ').title()
                            company = company_from_link
                        base_url = "https://www.ycombinator.com"
                        if job_link and not job_link.startswith("http"):
                            job_link = base_url + job_link
                        if title and title != "Title not found":
                            jobs.append({
                                'board': 'Y Combinator',
                                'title': title,
                                'link': job_link,
                                'preview': text_content[:120] + ("..." if len(text_content) > 120 else "")
                            })
                except Exception as e:
                    print(f"Error processing job card {i}: {e}")
                    continue
        except Exception as e:
            print(f"Error scraping Y Combinator: {e}")
        finally:
            browser.close()
    print(f"Y Combinator: Found {len(jobs)} jobs.")
    return jobs

def scrape_linkedin_jobs():
    from playwright.sync_api import sync_playwright
    import time
    jobs = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        try:
            print("Navigating to LinkedIn jobs page...")
            page.goto("https://www.linkedin.com/jobs/search/?keywords=web%20developer&location=United%20States")
            time.sleep(5)
            selectors_to_try = [
                'a[href*="/jobs/view/"]',
                '[data-testid*="job"]',
                '.job-card', '.job-listing', '.job-item',
                'article', '.card', '.listing',
                'div[class*="job"]', 'div[class*="listing"]',
                'li',
            ]
            job_cards = []
            for selector in selectors_to_try:
                cards = page.query_selector_all(selector)
                if cards:
                    print(f"Found {len(cards)} elements with selector: {selector}")
                    job_cards = cards
                    break
            if not job_cards:
                job_cards = page.query_selector_all('a, button, [role="button"]')
                print(f"Using fallback: Found {len(job_cards)} clickable elements")
            web_dev_keywords = [
                'web developer', 'frontend', 'backend', 'full stack', 'fullstack',
                'javascript', 'react', 'angular', 'vue', 'node.js', 'python',
                'html', 'css', 'php', 'ruby', 'java', 'developer', 'programmer',
                'software engineer', 'engineer', 'development', 'coding', 'programming'
            ]
            for i, card in enumerate(job_cards[:40]):
                try:
                    text_content = card.inner_text().strip()
                    if not text_content:
                        continue
                    has_web_dev_keyword = any(keyword in text_content.lower() for keyword in web_dev_keywords)
                    if has_web_dev_keyword:
                        title = "Title not found"
                        job_link = "Link not found"
                        title_elements = card.query_selector_all('h1, h2, h3, h4, h5, h6')
                        if title_elements:
                            title = title_elements[0].inner_text().strip()
                        if title == "Title not found":
                            lines = text_content.split('\n')
                            if lines:
                                title = lines[0].strip()
                        if card.evaluate('el => el.tagName.toLowerCase()') == 'a':
                            job_link = card.get_attribute('href')
                            if job_link is None:
                                job_link = ""
                        else:
                            link_elem = card.query_selector('a[href*="job"], a[href*="apply"]')
                            job_link = link_elem.get_attribute('href') if link_elem else ""
                            if job_link is None:
                                job_link = ""
                        base_url = "https://www.linkedin.com"
                        if job_link and not job_link.startswith("http"):
                            job_link = base_url + job_link
                        if title and title != "Title not found":
                            jobs.append({
                                'board': 'LinkedIn',
                                'title': title,
                                'link': job_link,
                                'preview': text_content[:120] + ("..." if len(text_content) > 120 else "")
                            })
                except Exception as e:
                    print(f"Error processing job card {i}: {e}")
                    continue
        except Exception as e:
            print(f"Error scraping LinkedIn: {e}")
        finally:
            browser.close()
    print(f"LinkedIn: Found {len(jobs)} jobs.")
    return jobs

def scrape_board_generic(board_name, url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Non-headless for debugging
        # Set user-agent to look like a real browser
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = context.new_page()
        try:
            print(f"Scraping {board_name}...")
            page.goto(url, timeout=60000)
            time.sleep(2)  # Initial wait for page load
            jobs = extract_jobs(page, board_name)
            if not jobs:
                print(f"[DEBUG] No jobs found for {board_name}. Printing first 500 chars of page HTML:")
                print(page.content()[:500])
                # Special handling for Y Combinator: try broader selector
                if board_name == "Y Combinator":
                    print("[DEBUG] Trying broader selector 'a' for Y Combinator...")
                    links = page.query_selector_all('a')
                    for i, link in enumerate(links[:10]):
                        try:
                            href = link.get_attribute('href')
                            text = link.inner_text().strip()
                            print(f"[DEBUG] Link {i}: {text} -> {href}")
                        except Exception as e:
                            print(f"[DEBUG] Error reading link: {e}")
            print(f"{board_name}: Found {len(jobs)} jobs.")
            return jobs
        except Exception as e:
            print(f"Error scraping {board_name}: {e}")
            return []
        finally:
            browser.close()

def scrape_board(board_name, url):
    if board_name == "Y Combinator":
        return scrape_yc_jobs()
    if board_name == "LinkedIn":
        return scrape_linkedin_jobs()
    return scrape_board_generic(board_name, url)

def main():
    all_jobs_by_board = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(scrape_board, name, url): name for name, url in JOB_BOARDS}
        for future in as_completed(futures):
            board = futures[future]
            jobs = future.result()
            all_jobs_by_board[board] = jobs
    print("\n================= AGGREGATED JOBS BY BOARD =================\n")
    total = 0
    for board, jobs in all_jobs_by_board.items():
        print(f"\n=== {board} ({len(jobs)} jobs) ===")
        for i, job in enumerate(jobs, 1):
            print(f"{i}. {job['title']}")
            print(f"   Link: {job['link']}\n   Preview: {job['preview']}")
            print("-" * 60)
        total += len(jobs)
    print(f"\nTotal jobs found: {total}")

if __name__ == "__main__":
    main() 