import asyncio
import json
import random
import time
import shutil
import os
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError


async def human_like_typing(element, text):
    await element.click()
    await asyncio.sleep(random.uniform(0.2, 0.5))
    for char in text:
        await element.type(char)
        await asyncio.sleep(random.uniform(0.05, 0.15))
        if random.random() < 0.1:
            await asyncio.sleep(random.uniform(0.3, 0.7))


async def add_flat_cookies_to_context(context, flat_cookies_dict):
    """
    Converts ALL flat dict cookies (name:value) into proper cookie objects with metadata,
    then adds them to the Playwright browser context.
    """
    cookies_to_add = []
    expires_timestamp = int(time.time()) + 3600 * 24 * 365  # 1 year from now

    print(f"🔍 Processing {len(flat_cookies_dict)} cookies from JSON...")
    
    for name, value in flat_cookies_dict.items():
        print(f"Processing cookie: {name}")
        
        # Remove quotes from cookie value if present
        original_value = value
        if isinstance(value, str) and value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
            print(f"  Stripped quotes: {original_value} -> {value}")

        cookie = {
            "name": name,
            "value": value,
            "domain": ".linkedin.com",  # Leading dot for all LinkedIn subdomains
            "path": "/",
            "httpOnly": name in ["li_at", "JSESSIONID", "bcookie", "bscookie"],
            "secure": True,
            "sameSite": "Lax",
            "expires": expires_timestamp,
        }
        cookies_to_add.append(cookie)
        print(f"  ✅ Added cookie: {name}")

    print(f"📊 Total cookies to add: {len(cookies_to_add)}")
    
    # Add all cookies to context
    await context.add_cookies(cookies_to_add)
    
    # Verify cookies were added
    added_cookies = await context.cookies("https://www.linkedin.com")
    print(f"🔍 Cookies actually added to browser: {len(added_cookies)}")
    for cookie in added_cookies:
        print(f"  - {cookie['name']}: {cookie['value'][:20]}...")
    
    return len(added_cookies)


async def setup_browser_context(playwright, cookies_data):
    """
    Create a Playwright browser context with enhanced error handling and retry logic.
    """
    chromium = playwright.chromium
    
    # Clear any existing persistent data to avoid conflicts
    if os.path.exists("./playwright_persistent"):
        try:
            shutil.rmtree("./playwright_persistent")
            print("🧹 Cleared existing browser data")
        except Exception as e:
            print(f"⚠️ Could not clear browser data: {e}")

    # Enhanced browser context with stealth options
    context = await chromium.launch_persistent_context(
        user_data_dir="./playwright_persistent",
        headless=False,
        viewport={"width": 1366, "height": 768},
        locale="en-US",
        timezone_id="Asia/Calcutta",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        device_scale_factor=1,
        ignore_https_errors=True,
        java_script_enabled=True,
        args=[
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--disable-extensions-except',
            '--disable-plugins-discovery'
        ]
    )

    # Add ALL cookies from flat dict
    cookies_added = await add_flat_cookies_to_context(context, cookies_data)
    print(f"✅ Successfully added {cookies_added} cookies to browser context")

    page = await context.new_page()

    # Enhanced stealth evasion scripts
    await page.add_init_script(
        """
        // Remove webdriver property completely
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        delete navigator.__proto__.webdriver;
        
        // Mock plugins to appear like real browser
        Object.defineProperty(navigator, 'plugins', {
            get: () => [{
                0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format", enabledPlugin: null},
                description: "Portable Document Format",
                filename: "internal-pdf-viewer",
                length: 1,
                name: "Chrome PDF Plugin"
            }]
        });
        
        // Mock languages
        Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
        
        // Add chrome property
        window.chrome = {
            runtime: {},
            loadTimes: function() {},
            csi: function() {},
            app: {}
        };
        
        // Mock permissions API
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = parameters =>
          parameters.name === 'notifications'
            ? Promise.resolve({ state: Notification.permission })
            : originalQuery(parameters);
            
        // Override hardware specs to appear realistic
        Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8});
        Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});
        
        // Mock connection
        Object.defineProperty(navigator, 'connection', {
            get: () => ({
                effectiveType: '4g',
                rtt: 100,
                downlink: 2
            })
        });
        
        // Override getUserMedia
        navigator.mediaDevices = navigator.mediaDevices || {};
        navigator.mediaDevices.getUserMedia = navigator.mediaDevices.getUserMedia || function() {
            return Promise.reject(new Error('Permission denied'));
        };
        """
    )

    # Enhanced navigation with multiple fallbacks and better error handling
    linkedin_urls = [
        "https://www.linkedin.com/feed/",
        "https://www.linkedin.com/",
        "https://linkedin.com/",
        "https://www.linkedin.com/login"
    ]
    
    navigation_successful = False
    last_error = None
    
    for attempt, url in enumerate(linkedin_urls, 1):
        try:
            print(f"🌐 Navigation attempt {attempt}: {url}")
            
            # Set additional headers to appear more like real browser
            await page.set_extra_http_headers({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0'
            })
            
            # Try to navigate with different wait strategies
            wait_strategies = ["domcontentloaded", "load"]
            
            for strategy in wait_strategies:
                try:
                    print(f"   Using wait strategy: {strategy}")
                    await page.goto(url, wait_until=strategy, timeout=30000)
                    await asyncio.sleep(3)  # Let page settle
                    
                    # Check if page loaded successfully
                    current_url = page.url
                    if "linkedin.com" in current_url:
                        navigation_successful = True
                        print(f"✅ Successfully navigated to: {current_url}")
                        break
                        
                except Exception as strategy_error:
                    print(f"   ❌ Strategy {strategy} failed: {str(strategy_error)[:100]}...")
                    last_error = strategy_error
                    continue
            
            if navigation_successful:
                break
                
        except Exception as e:
            print(f"❌ Navigation attempt {attempt} failed: {str(e)[:100]}...")
            last_error = e
            
            # Wait before next attempt
            if attempt < len(linkedin_urls):
                await asyncio.sleep(5)
            continue
    
    if not navigation_successful:
        raise Exception(f"❌ Could not navigate to LinkedIn after trying all URLs. Last error: {last_error}")

    # Check if we need to handle any blocking pages
    try:
        page_content = await page.content()
        current_url = page.url
        
        if any(indicator in page_content.lower() for indicator in ["blocked", "access denied", "not available"]):
            print("⚠️ Detected blocking page, trying alternative approach...")
            # Try going to a different LinkedIn page
            await page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded", timeout=20000)
            await asyncio.sleep(2)
    except Exception as e:
        print(f"⚠️ Could not check page content: {e}")

    print("✅ Browser context setup completed successfully")
    return page


async def human_like_scroll(page):
    """Simulate human-like scrolling behavior"""
    for _ in range(random.randint(3, 6)):
        await page.keyboard.press("PageDown")
        await asyncio.sleep(random.uniform(0.7, 1.5))
    if random.random() < 0.3:
        await page.keyboard.press("PageUp")
        await asyncio.sleep(random.uniform(0.7, 1.2))


async def warm_up_session(page):
    """Browse LinkedIn naturally to warm up the session"""
    print("🔥 Warming up LinkedIn session...")
    pages = [
        "https://www.linkedin.com/feed/",
        "https://www.linkedin.com/jobs/",
        "https://www.linkedin.com/in/me/",
    ]
    
    for i, url in enumerate(pages, 1):
        try:
            print(f"  📄 Visiting page {i}/{len(pages)}: {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            await asyncio.sleep(random.uniform(3, 5))
            await human_like_scroll(page)
        except Exception as e:
            print(f"  ⚠️ Could not visit {url}: {e}")
            continue
    
    print("✅ Session warm-up completed")


async def human_like_mouse_move(page, element_handle):
    """Simulate natural mouse movement to element"""
    try:
        box = await element_handle.bounding_box()
        if not box:
            return
        
        # Scroll element into view first
        await element_handle.scroll_into_view_if_needed()
        await asyncio.sleep(random.uniform(0.5, 1.0))
        
        # Start from random position
        start_x = random.randint(100, 300)
        start_y = random.randint(100, 300)
        await page.mouse.move(start_x, start_y, steps=10)
        
        # Move to element center with slight randomness
        target_x = box["x"] + box["width"] / 2 + random.randint(-10, 10)
        target_y = box["y"] + box["height"] / 2 + random.randint(-5, 5)
        await page.mouse.move(target_x, target_y, steps=random.randint(15, 25))
        await asyncio.sleep(random.uniform(0.3, 0.8))
    except Exception as e:
        print(f"⚠️ Mouse movement error: {e}")


async def apply_to_job(page, job_url, cover_letter_text=None):
    """Apply to a LinkedIn job with human-like behavior"""
    try:
        print(f"🎯 Opening job URL: {job_url}")
        await page.goto(job_url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(random.uniform(3, 5))

        # Read job description naturally
        print("📖 Reading job description...")
        await human_like_scroll(page)

        # Look for Easy Apply button with multiple selectors
        print("🔍 Looking for Easy Apply button...")
        easy_apply_selectors = [
            'button[data-test-easy-apply-button]',
            'button[aria-label*="Easy Apply"]',
            'button:has-text("Easy Apply")',
            '.jobs-apply-button',
            'button[data-control-name="jobdetails_topcard_inapply"]'
        ]
        
        easy_apply_btn = None
        for selector in easy_apply_selectors:
            try:
                easy_apply_btn = await page.wait_for_selector(selector, timeout=5000)
                if easy_apply_btn:
                    print(f"✅ Found Easy Apply button with selector: {selector}")
                    break
            except:
                continue
        
        if not easy_apply_btn:
            print("❌ Easy Apply button not found on page")
            return False

        # Human-like interaction with Easy Apply button
        await human_like_mouse_move(page, easy_apply_btn)
        await asyncio.sleep(random.uniform(1.0, 2.0))
        
        print("🖱️ Clicking Easy Apply button...")
        await easy_apply_btn.click()
        await asyncio.sleep(random.uniform(3, 5))

        # Wait for application modal or form
        print("⏳ Waiting for application modal...")
        modal_selectors = [
            ".artdeco-modal",
            ".jobs-easy-apply-modal",
            "[data-test-modal]",
            ".application-outlet"
        ]
        
        modal_found = False
        for selector in modal_selectors:
            try:
                await page.wait_for_selector(selector, timeout=10000)
                print(f"✅ Application modal found: {selector}")
                modal_found = True
                break
            except:
                continue
        
        if not modal_found:
            print("❌ No application modal found")
            return False

        # Fill cover letter if provided
        if cover_letter_text:
            print("✍️ Looking for cover letter field...")
            cover_letter_selectors = [
                'textarea[name="coverLetter"]',
                'textarea[id*="coverLetter"]',
                'textarea[placeholder*="cover letter"]',
                'textarea[placeholder*="Cover letter"]',
                '.jobs-easy-apply-form-section__grouping textarea',
                'textarea[data-test-single-line-text-form-component-formElement-urn-li-jobs-applyformcommon-easyApplyFormElement-4017839806-102454604-coverLetter]'
            ]
            
            for selector in cover_letter_selectors:
                try:
                    textarea = await page.wait_for_selector(selector, timeout=3000)
                    if textarea:
                        await human_like_typing(textarea, cover_letter_text)
                        await asyncio.sleep(1)
                        print("✅ Cover letter added")
                        break
                except:
                    continue

        # Navigate through application steps
        print("📝 Proceeding through application steps...")
        step_count = 0
        max_steps = 15  # Increased limit
        
        while step_count < max_steps:
            step_count += 1
            print(f"  Step {step_count}: Looking for next action...")
            
            # Look for various submit/continue buttons
            submit_selectors = [
                'button[aria-label*="Submit application"]',
                'button[aria-label*="Submit"]',
                'button[aria-label*="Continue to next step"]',
                'button[aria-label*="Next"]',
                'button[aria-label*="Continue"]',
                'button[data-test*="submit"]',
                'button:has-text("Submit application")',
                'button:has-text("Submit")',
                'button:has-text("Next")',
                'button:has-text("Continue")',
                'button:has-text("Review")',
                'button:has-text("Send application")'
            ]
            
            submit_btn = None
            for selector in submit_selectors:
                try:
                    submit_btn = await page.wait_for_selector(selector, timeout=3000)
                    if submit_btn and await submit_btn.is_visible():
                        print(f"    Found button with selector: {selector}")
                        break
                except:
                    continue
            
            if not submit_btn:
                print("    No more submit/next buttons found")
                break

            # Click the button with human-like behavior
            await human_like_mouse_move(page, submit_btn)
            await asyncio.sleep(random.uniform(1.0, 2.0))
            
            try:
                button_text = await submit_btn.inner_text()
                print(f"    Clicking button: {button_text}")
            except:
                print("    Clicking submit button")
            
            await submit_btn.click()
            await asyncio.sleep(random.uniform(4, 7))

            # Check for completion indicators
            success_indicators = [
                'text="Application sent"',
                'text="Your application was sent"',
                'text="Application submitted"',
                '[data-test="application-sent"]',
                '.jobs-apply-confirmation'
            ]
            
            for indicator in success_indicators:
                try:
                    success_element = await page.wait_for_selector(indicator, timeout=2000)
                    if success_element:
                        print("🎉 Application success indicator found!")
                        return True
                except:
                    continue

            # Check if modal closed (another success indicator)
            modal_still_open = False
            for selector in modal_selectors:
                try:
                    modal = await page.query_selector(selector)
                    if modal:
                        modal_still_open = True
                        break
                except:
                    continue
            
            if not modal_still_open:
                print("✅ Application modal closed - application likely completed")
                return True

        print("✅ Job application process completed")
        return True

    except PlaywrightTimeoutError:
        print("⏰ Timeout during job application")
        return False
    except Exception as e:
        print(f"💥 Exception during job application: {e}")
        return False


async def main():
    # Load cookie data - your JSON is flat cookies only
    try:
        with open("cookies.json", "r", encoding="utf-8") as f:
            cookies_data = json.load(f)
        print(f"📋 Loaded {len(cookies_data)} cookies from file")
        print("🍪 Cookie names:", list(cookies_data.keys()))
    except FileNotFoundError:
        print("❌ cookies.json file not found")
        return
    except json.JSONDecodeError:
        print("❌ Invalid JSON in cookies.json file")
        return

    # Validate that we have essential cookies
    essential_cookies = ["li_at", "JSESSIONID"]
    missing_cookies = [cookie for cookie in essential_cookies if cookie not in cookies_data]
    if missing_cookies:
        print(f"⚠️ Warning: Missing essential cookies: {missing_cookies}")
    else:
        print("✅ All essential cookies present")

    job_url = "https://www.linkedin.com/jobs/view/4207981559/?alternateChannel=search&eBP=BUDGET_EXHAUSTED_JOB&refId=jEOZjvGpTbOGj2CNUbCJgw%3D%3D&trackingId=xgMloByp1SHl6nTNhd0zOg%3D%3D"
    cover_letter = (
        "Dear Hiring Manager,\n\n"
        "I am excited to apply for this Frontend Developer position. "
        "My experience with modern web technologies including React, JavaScript, "
        "and responsive design makes me a great fit for this remote role.\n\n"
        "I am passionate about creating exceptional user experiences and "
        "would love to contribute to your team's success.\n\n"
        "Thank you for considering my application.\n\n"
        "Best regards"
    )

    async with async_playwright() as pw:
        print("🚀 Starting DevHire LinkedIn Apply Agent...")
        
        try:
            # Setup browser context with authentication
            page = await setup_browser_context(pw, cookies_data)
            
            # Verify authentication status
            await asyncio.sleep(3)
            current_url = page.url
            page_content = await page.content()
            
            if any(indicator in page_content for indicator in ["Sign in", "Join LinkedIn", "/login"]):
                print("❌ Authentication failed - still on login page")
                print("🔍 Possible reasons:")
                print("   - Cookies may be expired or invalid")
                print("   - li_at cookie missing or incorrect")
                print("   - LinkedIn detected automation")
                print("   - IP or region may be blocked")
                
                # Try to continue anyway in case it's a false positive
                print("⚠️ Continuing with job application attempt...")
            else:
                print("✅ Successfully authenticated with LinkedIn")

            # Warm up the session
            await warm_up_session(page)

            # Apply to the job
            print("🎯 Starting job application process...")
            success = await apply_to_job(page, job_url, cover_letter)

            if success:
                print("🎉 Job application completed successfully!")
            else:
                print("💥 Job application failed")

            # Keep browser open for review
            print("⏳ Keeping browser open for 15 seconds for review...")
            await asyncio.sleep(15)

        except Exception as e:
            print(f"💥 Fatal error: {e}")
        finally:
            try:
                await page.context.close()
            except:
                pass


if __name__ == "__main__":
    asyncio.run(main())
