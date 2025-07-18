import asyncio
import random
import re
from playwright.async_api import async_playwright
from fpdf import FPDF  # Assuming already installed (pip install fpdf)

# Platform configs (same as before)
PLATFORMS = {
    "ycombinator": {
        "url_template": "https://www.ycombinator.com/jobs/role/{role}",
        "base_url": "https://www.ycombinator.com"
    },
    "linkedin": {
        "url_template": "https://www.linkedin.com/jobs/search/?keywords={role}&location=india&refresh=true",
        "base_url": "https://www.linkedin.com"
    },
}

WEB_DEV_KEYWORDS = [
    'web developer', 'frontend', 'backend', 'full stack', 'fullstack',
    'javascript', 'react', 'angular', 'vue', 'node.js', 'python',
    'html', 'css', 'php', 'ruby', 'java', 'developer', 'programmer',
    'software engineer', 'engineer', 'development', 'coding', 'programming'
]

async def scrape_platform(browser, platform_name, config, role):
    page = await browser.new_page()
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

        print(f"\n===== JOB CARD DEBUGGING for {platform_name} =====")
        for i, card in enumerate(job_cards[:5]):
            try:
                text_content = (await card.inner_text()).strip()
                print(f"\n--- Card {i} ---")
                print(f"Text: {text_content[:200]}{'...' if len(text_content) > 200 else ''}")
                card_class = await card.get_attribute('class')
                print(f"Card class: {card_class}")
                children = await card.query_selector_all('*')
                for j, child in enumerate(children[:5]):
                    child_class = await child.get_attribute('class')
                    child_text = (await child.inner_text()).strip()
                    print(f"  Child {j} class: {child_class}, text: {child_text[:60]}")
            except Exception as e:
                print(f"Error printing card {i}: {e}")
        print(f"\n===== END JOB CARD DEBUGGING for {platform_name} =====\n")

        web_dev_jobs = []
        max_jobs = 100
        for i, card in enumerate(job_cards[:max_jobs]):
            try:
                text_content = (await card.inner_text()).strip()
                if not text_content:
                    continue

                title_lower = "title not found"
                title_elements = await card.query_selector_all('h1, h2, h3, h4, h5, h6')
                if title_elements:
                    title_lower = (await title_elements[0].inner_text()).strip().lower()
                elif text_content:
                    lines = text_content.split('\n')
                    if lines:
                        title_lower = lines[0].strip().lower()

                has_web_dev_keyword = any(keyword in title_lower or keyword in text_content.lower() for keyword in WEB_DEV_KEYWORDS)
                if not has_web_dev_keyword:
                    print(f"Skipping irrelevant job card {i} on {platform_name}")
                    continue

                title = "Title not found"
                company = "Company not found"
                job_link = "Link not found"
                job_description = "Description not found"

                title_elements = await card.query_selector_all('h1, h2, h3, h4, h5, h6')
                if title_elements:
                    title = (await title_elements[0].inner_text()).strip()
                if title == "Title not found":
                    title_selectors = [
                        '[class*="title"]', '[class*="job-title"]', '[class*="position"]',
                        '[class*="role"]', '[class*="name"]', '[class*="heading"]'
                    ]
                    for selector in title_selectors:
                        title_elem = await card.query_selector(selector)
                        if title_elem:
                            title = (await title_elem.inner_text()).strip()
                            break
                if title == "Title not found":
                    lines = text_content.split('\n')
                    if lines:
                        title = lines[0].strip()

                print(f"\n--- Card {i} Children Debug ---")
                children = await card.query_selector_all(':scope > *')
                for idx, child in enumerate(children):
                    child_class = await child.get_attribute('class')
                    child_text = (await child.inner_text()).strip()
                    print(f"  Child {idx}: class='{child_class}', text='{child_text[:60]}'")
                print(f"--- End Card {i} Children Debug ---\n")

                company_candidates = []
                if len(children) > 1:
                    for idx, child in enumerate(children):
                        child_text = (await child.inner_text()).strip()
                        if child_text and child_text != title and 2 < len(child_text) < 50:
                            company_candidates.append((idx, child_text))
                if company_candidates:
                    company = company_candidates[0][1]
                    print(f"  [Debug] Using child {company_candidates[0][0]} as company: {company}")
                else:
                    print(f"  [Warning] No company candidate found in children. Candidates: {[c[1] for c in company_candidates]}")

                tag_name = await card.evaluate('el => el.tagName.toLowerCase()')
                if tag_name == 'a':
                    job_link = await card.get_attribute('href') or "Link not found"
                else:
                    link_elem = await card.query_selector('a[href*="job"], a[href*="apply"]')
                    job_link = await link_elem.get_attribute('href') if link_elem else "Link not found"
                if job_link != "Link not found" and not job_link.startswith("http"):
                    job_link = config["base_url"] + job_link

                if company == "Company not found" or company == title:
                    m = re.match(r"/companies/([\w\-]+)/jobs/", job_link)
                    if m:
                        company = m.group(1).replace('-', ' ').title()
                        print(f"  [Debug] Extracted company from link: {company}")

                if company == "Company not found" or company == title:
                    company_selectors = [
                        '[class*="block font-bold md:inline"]',
                        '.block.font-bold.md\\:inline'
                    ]
                    for selector in company_selectors:
                        company_elem = await card.query_selector(selector)
                        if company_elem:
                            company_text = (await company_elem.inner_text()).strip()
                            if company_text and company_text != title and 2 < len(company_text) < 50:
                                company = company_text
                                print(f"  [Debug] Using selector {selector} as company: {company}")
                                break

                if company == "Company not found" or company == title:
                    company_patterns = [
                        r'([A-Z][a-zA-Z\s&\.]+)\s*•',
                        r'at\s+([A-Z][a-zA-Z\s&\.]+)',
                        r'([A-Z][a-zA-Z\s&\.]+)\s*\(',
                        r'([A-Z][a-zA-Z\s&\.]+)\s*\|',
                        r'([A-Z][a-zA-Z\s&\.]+)\s*[-–—]',
                        r'([A-Z][a-zA-Z\s&\.]+)\s*$',
                        r'([A-Z][a-zA-Z\s&\.]+)\s*Remote',
                        r'([A-Z][a-zA-Z\s&\.]+)\s*Full-time',
                        r'([A-Z][a-zA-Z\s&\.]+)\s*Part-time',
                    ]
                    for pattern in company_patterns:
                        match = re.search(pattern, text_content)
                        if match:
                            potential_company = match.group(1).strip()
                            if (len(potential_company) > 2 and 
                                potential_company.lower() not in ['remote', 'full-time', 'part-time', 'contract', 'internship'] and
                                not any(word in potential_company.lower() for word in ['years', 'experience', 'salary', 'location']) and
                                potential_company != title):
                                company = potential_company
                                print(f"  [Debug] Using regex as company: {company}")
                                break

                if company == "Company not found" or company == title:
                    lines = [line.strip() for line in text_content.split('\n') if line.strip()]
                    for line in lines:
                        if line != title and 2 < len(line) < 50:
                            company = line
                            print(f"  [Debug] Using line as company: {company}")
                            break

                print(f"[RESULT] Card {i}: Title='{title}', Company='{company}'")

                if job_link != "Link not found":
                    detail_page = await browser.new_page()
                    await detail_page.goto(job_link)
                    await asyncio.sleep(2)
                    desc_selectors = [
                        '[class*="description"]', '[class*="job-details"]',
                        'article', '.prose', '.job-desc'
                    ]
                    for selector in desc_selectors:
                        desc_elem = await detail_page.query_selector(selector)
                        if desc_elem:
                            job_description = (await desc_elem.inner_text()).strip()
                            print(f"  [Debug] Found description with selector: {selector}")
                            break
                    await detail_page.close()

                if title != "Title not found":
                    job_info = {
                        'platform': platform_name,
                        'title': title,
                        'company': company,
                        'link': job_link,
                        'description': job_description,
                        'text_preview': text_content[:200] + "..." if len(text_content) > 200 else text_content
                    }
                    web_dev_jobs.append(job_info)
                    print(f"✅ Found relevant web dev job on {platform_name}: {title} at {company}")
                    print(f"   Link: {job_link}")
                    print(f"   Preview: {job_info['text_preview']}")
                    print(f"   Description: {job_description[:200]}{'...' if len(job_description) > 200 else ''}")
            except Exception as e:
                print(f"Error processing job card {i} on {platform_name}: {e}")
                continue

        return web_dev_jobs
    except Exception as e:
        print(f"Error on {platform_name}: {e}")
        return []
    finally:
        await page.close()

def clean_text(text):
    # Clean text for latin1 encoding by replacing unknown chars with '?'
    return text.encode('latin-1', 'replace').decode('latin-1')

def generate_pdf(jobs, filename="web_dev_jobs.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt=clean_text("Web Development Jobs Report"), ln=1, align='C')
    pdf.cell(200, 10, txt=clean_text(f"Total Jobs: {len(jobs)}"), ln=1, align='C')
    pdf.ln(10)

    for job in jobs:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt=clean_text(f"Job Title: {job['title']}"), ln=1)
        pdf.set_font("Arial", size=10)
        pdf.cell(200, 10, txt=clean_text(f"Platform: {job['platform']}"), ln=1)
        pdf.cell(200, 10, txt=clean_text(f"Company: {job['company']}"), ln=1)
        pdf.cell(200, 10, txt=clean_text(f"Link: {job['link']}"), ln=1)
        desc = job['description'][:500] + "..." if len(job['description']) > 500 else job['description']
        pdf.multi_cell(0, 10, txt=clean_text(f"Description: {desc}"))
        pdf.ln(5)

    pdf.output(filename)
    print(f"PDF generated: {filename}")

async def search_web_dev_jobs(role="web-developer", platforms=list(PLATFORMS.keys())):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        tasks = [scrape_platform(browser, plat, PLATFORMS[plat], role) for plat in platforms]
        all_jobs = await asyncio.gather(*tasks)
        await browser.close()

        flat_jobs = [job for sublist in all_jobs for job in sublist]
        print(f"\n{'='*60}")
        print(f"FOUND {len(flat_jobs)} RELEVANT WEB DEV JOBS:")
        print(f"{'='*60}")

        for i, job in enumerate(flat_jobs, 1):
            print(f"\n{i}. {job['title']}")
            print(f"   Platform: {job['platform']}")
            print(f"   Company: {job['company']}")
            print(f"   Link: {job['link']}")
            print(f"   Preview: {job['text_preview']}")
            print(f"   Description: {job['description'][:200]}{'...' if len(job['description']) > 200 else ''}")
            print("-" * 50)

        if not flat_jobs:
            print("No relevant web development jobs found.")

        # Generate PDF with cleaned text
        generate_pdf(flat_jobs)

        print("\nPress Enter to close...")
        input()

if __name__ == "__main__":
    asyncio.run(search_web_dev_jobs())



# import asyncio
# import random
# import re
# from playwright.async_api import async_playwright

# # Platform configs (same as before)
# PLATFORMS = {
#     "ycombinator": {
#         "url_template": "https://www.ycombinator.com/jobs/role/{role}",
#         "base_url": "https://www.ycombinator.com"
#     },
#     "linkedin": {
#         "url_template": "https://www.linkedin.com/jobs/search/?keywords={role}&location=india&refresh=true",
#         "base_url": "https://www.linkedin.com"
#     },
# }

# WEB_DEV_KEYWORDS = [
#     'web developer', 'frontend', 'backend', 'full stack', 'fullstack',
#     'javascript', 'react', 'angular', 'vue', 'node.js', 'python',
#     'html', 'css', 'php', 'ruby', 'java', 'developer', 'programmer',
#     'software engineer', 'engineer', 'development', 'coding', 'programming'
# ]

# async def scrape_platform(browser, platform_name, config, role):
#     page = await browser.new_page()
#     try:
#         url = config["url_template"].format(role=role.replace(' ', '%20').lower())
#         print(f"Navigating to {platform_name} jobs page: {url}")
#         await page.goto(url)
#         await asyncio.sleep(5)

#         print(f"Searching for job listings on {platform_name}...")

#         selectors_to_try = [
#             'a[href*="/jobs/"]', '[data-testid*="job"]',
#             '.job-card', '.job-listing', '.job-item',
#             'article', '.card', '.listing',
#             'div[class*="job"]', 'div[class*="listing"]',
#             'li'
#         ]

#         job_cards = []
#         for selector in selectors_to_try:
#             cards = await page.query_selector_all(selector)
#             if cards:
#                 print(f"Found {len(cards)} elements with selector: {selector} on {platform_name}")
#                 job_cards = cards
#                 break

#         if not job_cards:
#             job_cards = await page.query_selector_all('a, button, [role="button"]')
#             print(f"Using fallback: Found {len(job_cards)} clickable elements on {platform_name}")

#         print(f"\n===== JOB CARD DEBUGGING for {platform_name} =====")
#         for i, card in enumerate(job_cards[:5]):
#             try:
#                 text_content = (await card.inner_text()).strip()
#                 print(f"\n--- Card {i} ---")
#                 print(f"Text: {text_content[:200]}{'...' if len(text_content) > 200 else ''}")
#                 card_class = await card.get_attribute('class')
#                 print(f"Card class: {card_class}")
#                 children = await card.query_selector_all('*')
#                 for j, child in enumerate(children[:5]):
#                     child_class = await child.get_attribute('class')
#                     child_text = (await child.inner_text()).strip()
#                     print(f"  Child {j} class: {child_class}, text: {child_text[:60]}")
#             except Exception as e:
#                 print(f"Error printing card {i}: {e}")
#         print(f"\n===== END JOB CARD DEBUGGING for {platform_name} =====\n")

#         web_dev_jobs = []
#         max_jobs = 100  # Max to process, increase if needed
#         for i, card in enumerate(job_cards[:max_jobs]):
#             try:
#                 text_content = (await card.inner_text()).strip()
#                 if not text_content:
#                     continue

#                 # Stricter filter: Check keywords in title or text (to avoid irrelevant)
#                 title = "Title not found"  # Temp for check
#                 title_elements = await card.query_selector_all('h1, h2, h3, h4, h5, h6')
#                 if title_elements:
#                     title = (await title_elements[0].inner_text()).strip().lower()
#                 elif text_content:
#                     lines = text_content.split('\n')
#                     if lines:
#                         title = lines[0].strip().lower()

#                 has_web_dev_keyword = any(keyword in title or keyword in text_content.lower() for keyword in WEB_DEV_KEYWORDS)
#                 if not has_web_dev_keyword:
#                     print(f"Skipping irrelevant job card {i} on {platform_name}")
#                     continue

#                 # Rest of extraction (same as your code)
#                 title = "Title not found"  # Reset for full extraction
#                 company = "Company not found"
#                 job_link = "Link not found"
#                 job_description = "Description not found"

#                 title_elements = await card.query_selector_all('h1, h2, h3, h4, h5, h6')
#                 if title_elements:
#                     title = (await title_elements[0].inner_text()).strip()
#                 if title == "Title not found":
#                     title_selectors = [
#                         '[class*="title"]', '[class*="job-title"]', '[class*="position"]',
#                         '[class*="role"]', '[class*="name"]', '[class*="heading"]'
#                     ]
#                     for selector in title_selectors:
#                         title_elem = await card.query_selector(selector)
#                         if title_elem:
#                             title = (await title_elem.inner_text()).strip()
#                             break
#                 if title == "Title not found":
#                     lines = text_content.split('\n')
#                     if lines:
#                         title = lines[0].strip()

#                 print(f"\n--- Card {i} Children Debug ---")
#                 children = await card.query_selector_all(':scope > *')
#                 for idx, child in enumerate(children):
#                     child_class = await child.get_attribute('class')
#                     child_text = (await child.inner_text()).strip()
#                     print(f"  Child {idx}: class='{child_class}', text='{child_text[:60]}'")
#                 print(f"--- End Card {i} Children Debug ---\n")

#                 company_candidates = []
#                 if len(children) > 1:
#                     for idx, child in enumerate(children):
#                         child_text = (await child.inner_text()).strip()
#                         if child_text and child_text != title and 2 < len(child_text) < 50:
#                             company_candidates.append((idx, child_text))
#                 if company_candidates:
#                     company = company_candidates[0][1]
#                     print(f"  [Debug] Using child {company_candidates[0][0]} as company: {company}")
#                 else:
#                     print(f"  [Warning] No company candidate found in children. Candidates: {[c[1] for c in company_candidates]}")

#                 tag_name = await card.evaluate('el => el.tagName.toLowerCase()')
#                 if tag_name == 'a':
#                     job_link = await card.get_attribute('href') or "Link not found"
#                 else:
#                     link_elem = await card.query_selector('a[href*="job"], a[href*="apply"]')
#                     job_link = await link_elem.get_attribute('href') if link_elem else "Link not found"
#                 if job_link != "Link not found" and not job_link.startswith("http"):
#                     job_link = config["base_url"] + job_link

#                 if company == "Company not found" or company == title:
#                     m = re.match(r"/companies/([\w\-]+)/jobs/", job_link)
#                     if m:
#                         company = m.group(1).replace('-', ' ').title()
#                         print(f"  [Debug] Extracted company from link: {company}")

#                 if company == "Company not found" or company == title:
#                     company_selectors = [
#                         '[class*="block font-bold md:inline"]',
#                         '.block.font-bold.md\\:inline'
#                     ]
#                     for selector in company_selectors:
#                         company_elem = await card.query_selector(selector)
#                         if company_elem:
#                             company_text = (await company_elem.inner_text()).strip()
#                             if company_text and company_text != title and 2 < len(company_text) < 50:
#                                 company = company_text
#                                 print(f"  [Debug] Using selector {selector} as company: {company}")
#                                 break

#                 if company == "Company not found" or company == title:
#                     company_patterns = [
#                         r'([A-Z][a-zA-Z\s&\.]+)\s*•',
#                         r'at\s+([A-Z][a-zA-Z\s&\.]+)',
#                         r'([A-Z][a-zA-Z\s&\.]+)\s*\(',
#                         r'([A-Z][a-zA-Z\s&\.]+)\s*\|',
#                         r'([A-Z][a-zA-Z\s&\.]+)\s*[-–—]',
#                         r'([A-Z][a-zA-Z\s&\.]+)\s*$',
#                         r'([A-Z][a-zA-Z\s&\.]+)\s*Remote',
#                         r'([A-Z][a-zA-Z\s&\.]+)\s*Full-time',
#                         r'([A-Z][a-zA-Z\s&\.]+)\s*Part-time',
#                     ]
#                     for pattern in company_patterns:
#                         match = re.search(pattern, text_content)
#                         if match:
#                             potential_company = match.group(1).strip()
#                             if (len(potential_company) > 2 and 
#                                 potential_company.lower() not in ['remote', 'full-time', 'part-time', 'contract', 'internship'] and
#                                 not any(word in potential_company.lower() for word in ['years', 'experience', 'salary', 'location']) and
#                                 potential_company != title):
#                                 company = potential_company
#                                 print(f"  [Debug] Using regex as company: {company}")
#                                 break

#                 if company == "Company not found" or company == title:
#                     lines = [line.strip() for line in text_content.split('\n') if line.strip()]
#                     for line in lines:
#                         if line != title and 2 < len(line) < 50:
#                             company = line
#                             print(f"  [Debug] Using line as company: {company}")
#                             break

#                 print(f"[RESULT] Card {i}: Title='{title}', Company='{company}'")

#                 # Fetch job description
#                 if job_link != "Link not found":
#                     detail_page = await browser.new_page()
#                     await detail_page.goto(job_link)
#                     await asyncio.sleep(2)
#                     desc_selectors = [
#                         '[class*="description"]', '[class*="job-details"]',
#                         'article', '.prose', '.job-desc'
#                     ]
#                     for selector in desc_selectors:
#                         desc_elem = await detail_page.query_selector(selector)
#                         if desc_elem:
#                             job_description = (await desc_elem.inner_text()).strip()
#                             print(f"  [Debug] Found description with selector: {selector}")
#                             break
#                     await detail_page.close()

#                 if title != "Title not found":
#                     job_info = {
#                         'platform': platform_name,
#                         'title': title,
#                         'company': company,
#                         'link': job_link,
#                         'description': job_description,
#                         'text_preview': text_content[:200] + "..." if len(text_content) > 200 else text_content
#                     }
#                     web_dev_jobs.append(job_info)
#                     print(f"✅ Found relevant web dev job on {platform_name}: {title} at {company}")
#                     print(f"   Link: {job_link}")
#                     print(f"   Preview: {job_info['text_preview']}")
#                     print(f"   Description: {job_description[:200]}{'...' if len(job_description) > 200 else ''}")
#             except Exception as e:
#                 print(f"Error processing job card {i} on {platform_name}: {e}")
#                 continue

#         return web_dev_jobs
#     except Exception as e:
#         print(f"Error on {platform_name}: {e}")
#         return []
#     finally:
#         await page.close()

# async def search_web_dev_jobs(role="web-developer", platforms=list(PLATFORMS.keys())):
#     async with async_playwright() as p:
#         browser = await p.chromium.launch(headless=False)
#         tasks = [scrape_platform(browser, plat, PLATFORMS[plat], role) for plat in platforms]
#         all_jobs = await asyncio.gather(*tasks)
#         await browser.close()

#         flat_jobs = [job for sublist in all_jobs for job in sublist]
#         print(f"\n{'='*60}")
#         print(f"FOUND {len(flat_jobs)} RELEVANT WEB DEV JOBS:")
#         print(f"{'='*60}")

#         for i, job in enumerate(flat_jobs, 1):
#             print(f"\n{i}. {job['title']}")
#             print(f"   Platform: {job['platform']}")
#             print(f"   Company: {job['company']}")
#             print(f"   Link: {job['link']}")
#             print(f"   Preview: {job['text_preview']}")
#             print(f"   Description: {job['description'][:200]}{'...' if len(job['description']) > 200 else ''}")
#             print("-" * 50)

#         if not flat_jobs:
#             print("No relevant web development jobs found.")

#         print("\nPress Enter to close...")
#         input()

# if __name__ == "__main__":
#     asyncio.run(search_web_dev_jobs())
