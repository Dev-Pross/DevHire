from playwright.sync_api import sync_playwright
import time

def search_web_dev_jobs():
    with sync_playwright() as p:
        # Launch browser in headless mode (set headless=False to see the browser)
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            # Navigate to Y Combinator jobs page
            print("Navigating to Y Combinator jobs page...")
            # page.goto("https://www.ycombinator.com/jobs")
            page.goto("https://www.linkedin.com/jobs/search/?currentJobId=3945000000&geoId=90009590&keywords=web%20developer&location=india&refresh=true")

            time.sleep(5)  # Wait for page to load
            
            print("Searching for job listings...")
            
            # Let's first debug what we can find on the page
            print("Debugging page structure...")
            
            # Try different selectors to find job listings
            selectors_to_try = [
                'a[href*="/jobs/"]',  # Links to job pages
                '[data-testid*="job"]',  # Data test IDs
                '.job-card', '.job-listing', '.job-item',  # Common class names
                'article', '.card', '.listing',  # Generic containersgit 
                'div[class*="job"]', 'div[class*="listing"]',  # Partial class matches
                'li',  # List items
            ]
            
            job_cards = []
            for selector in selectors_to_try:
                cards = page.query_selector_all(selector)
                if cards:
                    print(f"Found {len(cards)} elements with selector: {selector}")
                    job_cards = cards
                    break
            
            if not job_cards:
                # If still no cards, try to get all clickable elements
                job_cards = page.query_selector_all('a, button, [role="button"]')
                print(f"Using fallback: Found {len(job_cards)} clickable elements")
            
            print(f"\n===== JOB CARD DEBUGGING =====")
            for i, card in enumerate(job_cards[:5]):
                try:
                    print(f"\n--- Card {i} ---")
                    text_content = card.inner_text().strip()
                    print(f"Text: {text_content[:200]}{'...' if len(text_content) > 200 else ''}")
                    # Print classes of the card
                    card_class = card.get_attribute('class')
                    print(f"Card class: {card_class}")
                    # Print classes and text of children
                    children = card.query_selector_all('*')
                    for j, child in enumerate(children[:5]):
                        child_class = child.get_attribute('class')
                        child_text = child.inner_text().strip()
                        print(f"  Child {j} class: {child_class}, text: {child_text[:60]}")
                except Exception as e:
                    print(f"Error printing card {i}: {e}")
            print(f"\n===== END JOB CARD DEBUGGING =====\n")

            web_dev_jobs = []
            web_dev_keywords = [
                'web developer', 'frontend', 'backend', 'full stack', 'fullstack',
                'javascript', 'react', 'angular', 'vue', 'node.js', 'python',
                'html', 'css', 'php', 'ruby', 'java', 'developer', 'programmer',
                'software engineer', 'engineer', 'development', 'coding', 'programming'
            ]

            for i, card in enumerate(job_cards[:20]):  # Check first 20 cards
                try:
                    text_content = card.inner_text().strip()
                    if not text_content:
                        continue
                    has_web_dev_keyword = any(keyword in text_content.lower() for keyword in web_dev_keywords)
                    if has_web_dev_keyword:
                        title = "Title not found"
                        company = "Company not found"
                        job_link = "Link not found"
                        # Title extraction
                        title_elements = card.query_selector_all('h1, h2, h3, h4, h5, h6')
                        if title_elements:
                            title = title_elements[0].inner_text().strip()
                        if title == "Title not found":
                            title_selectors = [
                                '[class*="title"]', '[class*="job-title"]', '[class*="position"]',
                                '[class*="role"]', '[class*="name"]', '[class*="heading"]'
                            ]
                            for selector in title_selectors:
                                title_elem = card.query_selector(selector)
                                if title_elem:
                                    title = title_elem.inner_text().strip()
                                    break
                        if title == "Title not found":
                            lines = text_content.split('\n')
                            if lines:
                                title = lines[0].strip()
                        # Debug: print all direct children classes and text
                        print(f"\n--- Card {i} Children Debug ---")
                        children = card.query_selector_all(':scope > *')
                        for idx, child in enumerate(children):
                            child_class = child.get_attribute('class')
                            child_text = child.inner_text().strip()
                            print(f"  Child {idx}: class='{child_class}', text='{child_text[:60]}")
                        print(f"--- End Card {i} Children Debug ---\n")
                        # Company extraction: try to get from a different child than the title
                        company = "Company not found"
                        company_candidates = []
                        if len(children) > 1:
                            for idx, child in enumerate(children):
                                child_text = child.inner_text().strip()
                                if child_text and child_text != title and 2 < len(child_text) < 50:
                                    company_candidates.append((idx, child_text))
                        if company_candidates:
                            company = company_candidates[0][1]
                            print(f"  [Debug] Using child {company_candidates[0][0]} as company: {company}")
                        else:
                            print(f"  [Warning] No company candidate found in children. Candidates: {[c[1] for c in company_candidates]}")
                        # Try to extract company from job link
                        if company == "Company not found" or company == title:
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
                                print(f"  [Debug] Extracted company from link: {company}")
                        # Fallback: try previous selectors
                        if company == "Company not found" or company == title:
                            company_selectors = [
                                '[class*="block font-bold md:inline"]',
                                '.block.font-bold.md\\:inline'
                            ]
                            for selector in company_selectors:
                                company_elem = card.query_selector(selector)
                                if company_elem:
                                    company_text = company_elem.inner_text().strip()
                                    if company_text and company_text != title and 2 < len(company_text) < 50:
                                        company = company_text
                                        print(f"  [Debug] Using selector {selector} as company: {company}")
                                        break
                        # Fallback: regex and line-based, but filter out job titles
                        if company == "Company not found" or company == title:
                            import re
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
                        if card.evaluate('el => el.tagName.toLowerCase()') == 'a':
                            job_link = card.get_attribute('href') or "Link not found"
                        else:
                            link_elem = card.query_selector('a[href*="job"], a[href*="apply"]')
                            if link_elem:
                                job_link = link_elem.get_attribute('href') or "Link not found"
                        # Make job link absolute if needed
                        base_url = "https://www.ycombinator.com"
                        if job_link and not job_link.startswith("http"):
                            job_link = base_url + job_link
                        if title and title != "Title not found":
                            job_info = {
                                'title': title,
                                'company': company,
                                'link': job_link,
                                'text_preview': text_content[:200] + "..." if len(text_content) > 200 else text_content
                            }
                            web_dev_jobs.append(job_info)
                            print(f"✅ Found web dev job: {title} at {company}")
                            print(f"   Link: {job_link}")
                            print(f"   Preview: {job_info['text_preview']}")
                except Exception as e:
                    print(f"Error processing job card {i}: {e}")
                    continue
            
            # Print results
            print(f"\n{'='*60}")
            print(f"FOUND {len(web_dev_jobs)} WEB DEVELOPMENT JOBS:")
            print(f"{'='*60}")
            
            for i, job in enumerate(web_dev_jobs, 1):
                print(f"\n{i}. {job['title']}")
                print(f"   Company: {job['company']}")
                print(f"   Link: {job['link']}")
                print(f"   Preview: {job['text_preview']}")
                print("-" * 50)
            
            if not web_dev_jobs:
                print("No web development jobs found.")
                print("Debug info - First few text contents:")
                for i, card in enumerate(job_cards[:5]):
                    try:
                        text = card.inner_text().strip()
                        if text:
                            print(f"Card {i}: {text[:100]}...")
                    except:
                        continue
            
        except Exception as e:
            print(f"Error: {e}")
        
        finally:
            # Keep browser open for a few seconds to see results
            print("\nPress Enter to close browser...")
            input()
            browser.close()

if __name__ == "__main__":
    search_web_dev_jobs()



# from playwright.sync_api import sync_playwright, Page, ElementHandle
# import time
# import re
# from typing import List, Dict, Optional

# WEB_DEV_KEYWORDS = ["Frontend Developer","Full Stack Developer","Software Engineer","AI Engineer","JavaScript Developer","React Developer","Node.js Developer","Backend Developer","Web Developer","Junior Frontend Developer"]

# JOB_SELECTORS = [
#     'a[href*="/jobs/"]',
#     '[data-testid*="job"]',
#     '.job-card', '.job-listing', '.job-item',
#     'article', '.card', '.listing',
#     'div[class*="job"]', 'div[class*="listing"]',
#     'li'
# ]

# def find_job_cards(page: Page) -> List[ElementHandle]:
#     for selector in JOB_SELECTORS:
#         cards = page.query_selector_all(selector)
#         if cards:
#             print(f"[+] Found {len(cards)} job cards with selector: {selector}")
#             return cards
#     # Fallback
#     fallback_cards = page.query_selector_all('a, button, [role="button"]')
#     print(f"[!] Fallback: Found {len(fallback_cards)} clickable elements")
#     return fallback_cards

# def extract_title(card: ElementHandle, text: str) -> str:
#     for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
#         elem = card.query_selector(tag)
#         if elem:
#             return elem.inner_text().strip()
#     for pattern in ['[class*="title"]', '[class*="job-title"]', '[class*="heading"]']:
#         elem = card.query_selector(pattern)
#         if elem:
#             return elem.inner_text().strip()
#     return text.split('\n')[0].strip()

# def extract_company(card: ElementHandle, title: str, text: str) -> str:
#     children = card.query_selector_all(':scope > *')
#     for child in children:
#         try:
#             child_text = child.inner_text().strip()
#             if child_text and child_text != title and 2 < len(child_text) < 50:
#                 return child_text
#         except:
#             continue

#     # Try regex fallback
#     patterns = [
#         r'at\s+([A-Z][a-zA-Z\s&\.]+)',
#         r'([A-Z][a-zA-Z\s&\.]+)\s*[-•|()]',
#         r'([A-Z][a-zA-Z\s&\.]+)\s*(Remote|Full-time|Part-time)?$'
#     ]
#     for pattern in patterns:
#         match = re.search(pattern, text)
#         if match:
#             potential = match.group(1).strip()
#             if potential.lower() not in title.lower():
#                 return potential

#     return "Company not found"

# def extract_link(card: ElementHandle) -> str:
#     if card.evaluate('el => el.tagName.toLowerCase()') == 'a':
#         return card.get_attribute('href') or "Link not found"
#     link = card.query_selector('a[href*="job"], a[href*="apply"]')
#     return link.get_attribute('href') if link else "Link not found"

# def matches_keywords(text: str, keywords: List[str]) -> bool:
#     return any(keyword in text.lower() for keyword in keywords)

# def search_web_dev_jobs():
#     with sync_playwright() as p:
#         browser = p.chromium.launch(headless=False)
#         page = browser.new_page()
#         keyword=""
#         try:
#             for title in WEB_DEV_KEYWORDS:
#                 url = title 
#                 print(url)
#                 keyword += url.split(" ")+"%20"
#                 print(keyword)
            
#             print("[*] Navigating to LinkedIn jobs...")
#             print(keyword)
#             page.goto("https://www.linkedin.com/jobs/search/?keywords=",keyword,"&location=United%20States")
#             time.sleep(5)

#             job_cards = find_job_cards(page)
#             web_jobs = []

#             for i, card in enumerate(job_cards[:20]):
#                 try:
#                     text = card.inner_text().strip()
#                     if not matches_keywords(text, WEB_DEV_KEYWORDS):
#                         continue

#                     title = extract_title(card, text)
#                     company = extract_company(card, title, text)
#                     link = extract_link(card)
#                     preview = text[:200] + "..." if len(text) > 200 else text

#                     web_jobs.append({
#                         "title": title,
#                         "company": company,
#                         "link": link,
#                         "preview": preview
#                     })

#                     print(f"\n✅ {title} at {company}")
#                     print(f"🔗 {link}")
#                     print(f"📝 {preview}")
#                 except Exception as e:
#                     print(f"[!] Error in card {i}: {e}")
#                     continue

#             print(f"\n{'='*50}\nFound {len(web_jobs)} Web Dev Jobs\n{'='*50}")
#             for idx, job in enumerate(web_jobs, 1):
#                 print(f"{idx}. {job['title']} at {job['company']}")
#                 print(f"   Link: {job['link']}")
#                 print(f"   Preview: {job['preview']}\n")

#         except Exception as e:
#             print(f"[X] Fatal Error: {e}")
#         finally:
#             input("Press Enter to close browser...")
#             browser.close()

# if __name__ == "__main__":
#     search_web_dev_jobs()
