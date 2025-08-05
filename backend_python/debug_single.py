import asyncio
import os
import sys
from playwright.async_api import async_playwright

# Import config from correct location (backend_python/config.py)
sys.path.append(os.path.dirname(__file__))
try:
    from config import LINKEDIN_ID, LINKEDIN_PASSWORD
    print(f"[CONFIG] Successfully imported config")
    print(f"[CONFIG] LINKEDIN_ID: {'***' if LINKEDIN_ID else 'None'}")
    print(f"[CONFIG] LINKEDIN_PASSWORD: {'***' if LINKEDIN_PASSWORD else 'None'}")
except ImportError as e:
    print(f"[CONFIG] Error importing config: {e}")
    LINKEDIN_ID = None
    LINKEDIN_PASSWORD = None

LINKEDIN_LOGIN_URL = "https://www.linkedin.com/login"

async def linkedin_login(page, username, password):
    """Login to LinkedIn with comprehensive logging"""
    print(f"[LOGIN] Starting LinkedIn login process...")
    
    if not username or not password:
        print(f"[LOGIN] Missing credentials, cannot proceed")
        return False
    
    try:
        print(f"[LOGIN] Navigating to: {LINKEDIN_LOGIN_URL}")
        await page.goto(LINKEDIN_LOGIN_URL)
        print(f"[LOGIN] Successfully navigated to login page")
        
        # Wait for page to load
        await page.wait_for_load_state('domcontentloaded')
        print(f"[LOGIN] Page loaded successfully")
        
        # Fill username
        print(f"[LOGIN] Filling username field...")
        await page.fill('input#username', username)
        print(f"[LOGIN] Username filled successfully")
        
        # Fill password
        print(f"[LOGIN] Filling password field...")
        await page.fill('input#password', password)
        print(f"[LOGIN] Password filled successfully")
        
        # Click submit
        print(f"[LOGIN] Clicking submit button...")
        try:
            async with page.expect_navigation(timeout=60000):
                await page.click('button[type="submit"]')
            print(f"[LOGIN] Submit button clicked, navigation completed")
        except Exception as e:
            print(f"[LOGIN] Navigation timeout, but continuing: {e}")
            await page.click('button[type="submit"]')
        
        # Wait for page to load
        print(f"[LOGIN] Waiting for page to load...")
        try:
            await page.wait_for_load_state('networkidle', timeout=60000)
            print(f"[LOGIN] Page loaded to networkidle state")
        except Exception as e:
            print(f"[LOGIN] Networkidle timeout, trying domcontentloaded: {e}")
            try:
                await page.wait_for_load_state('domcontentloaded', timeout=30000)
                print(f"[LOGIN] Page loaded to domcontentloaded state")
            except Exception as e2:
                print(f"[LOGIN] Domcontentloaded timeout: {e2}")
        
        # Check current URL
        try:
            current_url = page.url
            print(f"[LOGIN] Current URL after login: {current_url}")
        except Exception as e:
            print(f"[LOGIN] Error getting current URL: {e}")
            return False
        
        # Check if login was successful
        if "feed" in current_url or "jobs" in current_url:
            print(f"[LOGIN] Login successful - redirected to feed/jobs")
            return True
        elif "login" in current_url:
            print(f"[LOGIN] Login failed - still on login page")
            return False
        else:
            print(f"[LOGIN] Login status unclear - URL: {current_url}")
            return True
            
    except Exception as e:
        print(f"[LOGIN] Error during login process: {e}")
        return False

async def debug_single_job(context, job_url):
    """
    Debug function to test scraping a single job URL.
    """
    print(f"[DEBUG] Testing single job URL: {job_url}")
    
    page = await context.new_page()
    try:
        await page.goto(job_url, wait_until="domcontentloaded")
        await asyncio.sleep(5)
        
        # Take a screenshot for debugging
        screenshot_path = "debug_job_page.png"
        await page.screenshot(path=screenshot_path)
        print(f"[DEBUG] Screenshot saved to: {screenshot_path}")
        
        # Get page title and URL
        page_title = await page.title()
        current_url = page.url
        print(f"[DEBUG] Page title: {page_title}")
        print(f"[DEBUG] Current URL: {current_url}")
        
        # Try to get any text content
        try:
            body_text = await page.locator('body').text_content()
            print(f"[DEBUG] Body text length: {len(body_text) if body_text else 0}")
            if body_text:
                print(f"[DEBUG] First 1000 chars of body: {body_text[:1000]}")
        except Exception as e:
            print(f"[DEBUG] Error getting body text: {e}")
        
        # Try to find any h1 elements
        try:
            h1_elements = await page.locator('h1').all()
            print(f"[DEBUG] Found {len(h1_elements)} h1 elements")
            for i, h1 in enumerate(h1_elements):
                h1_text = await h1.text_content()
                h1_class = await h1.get_attribute('class')
                print(f"[DEBUG] H1 {i+1}: {h1_text}")
                print(f"[DEBUG] H1 {i+1} class: {h1_class}")
        except Exception as e:
            print(f"[DEBUG] Error getting h1 elements: {e}")
        
        # Try to find any elements with "job" in the class name
        try:
            job_elements = await page.locator('[class*="job"]').all()
            print(f"[DEBUG] Found {len(job_elements)} elements with 'job' in class name")
            for i, elem in enumerate(job_elements[:10]):  # First 10
                elem_text = await elem.text_content()
                elem_class = await elem.get_attribute('class')
                print(f"[DEBUG] Job element {i+1} class: {elem_class}")
                print(f"[DEBUG] Job element {i+1} text: {elem_text[:200] if elem_text else 'None'}")
        except Exception as e:
            print(f"[DEBUG] Error getting job elements: {e}")
        
        # Try to find any elements with "title" in the class name
        try:
            title_elements = await page.locator('[class*="title"]').all()
            print(f"[DEBUG] Found {len(title_elements)} elements with 'title' in class name")
            for i, elem in enumerate(title_elements[:5]):  # First 5
                elem_text = await elem.text_content()
                elem_class = await elem.get_attribute('class')
                print(f"[DEBUG] Title element {i+1} class: {elem_class}")
                print(f"[DEBUG] Title element {i+1} text: {elem_text[:200] if elem_text else 'None'}")
        except Exception as e:
            print(f"[DEBUG] Error getting title elements: {e}")
        
        # Try to find any elements with "company" in the class name
        try:
            company_elements = await page.locator('[class*="company"]').all()
            print(f"[DEBUG] Found {len(company_elements)} elements with 'company' in class name")
            for i, elem in enumerate(company_elements[:5]):  # First 5
                elem_text = await elem.text_content()
                elem_class = await elem.get_attribute('class')
                print(f"[DEBUG] Company element {i+1} class: {elem_class}")
                print(f"[DEBUG] Company element {i+1} text: {elem_text[:200] if elem_text else 'None'}")
        except Exception as e:
            print(f"[DEBUG] Error getting company elements: {e}")
        
        # Try to find any elements with "description" in the class name
        try:
            desc_elements = await page.locator('[class*="description"]').all()
            print(f"[DEBUG] Found {len(desc_elements)} elements with 'description' in class name")
            for i, elem in enumerate(desc_elements[:3]):  # First 3
                elem_text = await elem.text_content()
                elem_class = await elem.get_attribute('class')
                print(f"[DEBUG] Description element {i+1} class: {elem_class}")
                print(f"[DEBUG] Description element {i+1} text: {elem_text[:500] if elem_text else 'None'}")
        except Exception as e:
            print(f"[DEBUG] Error getting description elements: {e}")
        
        # Try to find any elements with "content" in the class name
        try:
            content_elements = await page.locator('[class*="content"]').all()
            print(f"[DEBUG] Found {len(content_elements)} elements with 'content' in class name")
            for i, elem in enumerate(content_elements[:3]):  # First 3
                elem_text = await elem.text_content()
                elem_class = await elem.get_attribute('class')
                print(f"[DEBUG] Content element {i+1} class: {elem_class}")
                print(f"[DEBUG] Content element {i+1} text: {elem_text[:500] if elem_text else 'None'}")
        except Exception as e:
            print(f"[DEBUG] Error getting content elements: {e}")
        
        # Wait for user input to keep browser open
        input("[DEBUG] Press Enter to continue...")
        
    except Exception as e:
        print(f"[DEBUG] Error in debug function: {e}")
    finally:
        await page.close()

async def main():
    print(f"[MAIN] Starting LinkedIn job debugger...")
    
    # Check credentials
    print(f"\n[MAIN] Step 1: Checking LinkedIn credentials")
    if LINKEDIN_ID is None or LINKEDIN_PASSWORD is None:
        print(f"[MAIN] LinkedIn credentials not found in config. Exiting.")
        print(f"[MAIN] Please create a .env file in the backend_python directory with:")
        print(f"[MAIN] LINKEDIN_ID=your_linkedin_email@example.com")
        print(f"[MAIN] LINKEDIN_PASSWORD=your_linkedin_password")
        return
    
    print(f"[MAIN] Credentials found, proceeding with debugging")
    
    # Start Playwright
    print(f"\n[MAIN] Step 2: Starting Playwright browser")
    try:
        playwright = await async_playwright().start()
        print(f"[MAIN] Playwright started successfully")
        
        browser = await playwright.chromium.launch(headless=False)
        print(f"[MAIN] Browser launched successfully")
        
        context = await browser.new_context()
        print(f"[MAIN] Browser context created")
        
    except Exception as e:
        print(f"[MAIN] Error starting Playwright: {e}")
        return
    
    # Login to LinkedIn
    print(f"\n[MAIN] Step 3: Logging into LinkedIn")
    page = await context.new_page()
    login_success = await linkedin_login(page, LINKEDIN_ID, LINKEDIN_PASSWORD)
    await page.close()
    
    if not login_success:
        print(f"[MAIN] LinkedIn login failed. Exiting.")
        await context.close()
        await browser.close()
        await playwright.stop()
        return
    
    print(f"[MAIN] LinkedIn login successful")
    
    # DEBUG: Test a single job URL
    print(f"\n[MAIN] Step 4: DEBUG - Testing single job URL")
    test_job_url = "https://www.linkedin.com/jobs/view/4275922794/"
    await debug_single_job(context, test_job_url)
    
    # Cleanup
    print(f"\n[MAIN] Step 5: Cleaning up resources")
    await context.close()
    await browser.close()
    await playwright.stop()
    print(f"[MAIN] Resources cleaned up")

if __name__ == "__main__":
    print(f"[SCRIPT] LinkedIn Job Debugger Started")
    print(f"[SCRIPT] =================================")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n[SCRIPT] Exiting on user interrupt.")
    except Exception as e:
        print(f"\n[SCRIPT] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"[SCRIPT] Script completed.") 