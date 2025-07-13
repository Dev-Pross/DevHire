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
            page.goto("https://www.ycombinator.com/jobs")
            time.sleep(5)  # Wait for page to load
            
            print("Searching for job listings...")
            
            # Let's first debug what we can find on the page
            print("Debugging page structure...")
            
            # Try different selectors to find job listings
            selectors_to_try = [
                'a[href*="/jobs/"]',  # Links to job pages
                '[data-testid*="job"]',  # Data test IDs
                '.job-card', '.job-listing', '.job-item',  # Common class names
                'article', '.card', '.listing',  # Generic containers
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
            
            print(f"Processing {len(job_cards)} potential job listings")
            
            web_dev_jobs = []
            
            # Keywords for web development roles
            web_dev_keywords = [
                'web developer', 'frontend', 'backend', 'full stack', 'fullstack',
                'javascript', 'react', 'angular', 'vue', 'node.js', 'python',
                'html', 'css', 'php', 'ruby', 'java', 'developer', 'programmer',
                'software engineer', 'engineer', 'development', 'coding', 'programming'
            ]
            
            for i, card in enumerate(job_cards[:20]):  # Check first 20 cards
                try:
                    # Get text content
                    text_content = card.inner_text().strip()
                    
                    if not text_content:
                        continue
                    
                    # Check if it contains web development keywords
                    has_web_dev_keyword = any(keyword in text_content.lower() for keyword in web_dev_keywords)
                    
                    if has_web_dev_keyword:
                        # Try multiple strategies to get job title
                        title = "Title not found"
                        company = "Company not found"
                        job_link = "Link not found"
                        
                        # Strategy 1: Look for heading elements
                        title_elements = card.query_selector_all('h1, h2, h3, h4, h5, h6')
                        if title_elements:
                            title = title_elements[0].inner_text().strip()
                        
                        # Strategy 2: Look for elements with title-related classes
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
                        
                        # Strategy 3: If still no title, use first line of text
                        if title == "Title not found":
                            lines = text_content.split('\n')
                            if lines:
                                title = lines[0].strip()
                        
                        # Strategy 4: Look for company name
                        company_selectors = [
                            '[class*="company"]', '[class*="employer"]', '[class*="organization"]',
                            '[class*="brand"]', '[class*="logo"]'
                        ]
                        for selector in company_selectors:
                            company_elem = card.query_selector(selector)
                            if company_elem:
                                company = company_elem.inner_text().strip()
                                break
                        
                        # Strategy 5: If no company found, try to extract from text
                        if company == "Company not found":
                            # Look for patterns like "Company Name •" or "at Company Name"
                            import re
                            company_patterns = [
                                r'([A-Z][a-zA-Z\s&]+)\s*•',  # Company Name •
                                r'at\s+([A-Z][a-zA-Z\s&]+)',  # at Company Name
                                r'([A-Z][a-zA-Z\s&]+)\s*\(',  # Company Name (
                            ]
                            for pattern in company_patterns:
                                match = re.search(pattern, text_content)
                                if match:
                                    company = match.group(1).strip()
                                    break
                        
                        # Get job link
                        if card.evaluate('el => el.tagName.toLowerCase()') == 'a':
                            job_link = card.get_attribute('href') or "Link not found"
                        else:
                            link_elem = card.query_selector('a[href*="job"], a[href*="apply"]')
                            if link_elem:
                                job_link = link_elem.get_attribute('href') or "Link not found"
                        
                        # Clean up the data
                        if title and title != "Title not found":
                            job_info = {
                                'title': title,
                                'company': company,
                                'link': job_link,
                                'text_preview': text_content[:200] + "..." if len(text_content) > 200 else text_content
                            }
                            
                            web_dev_jobs.append(job_info)
                            print(f"✅ Found web dev job: {title} at {company}")
                
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
