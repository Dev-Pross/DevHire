#!/usr/bin/env python3
"""
LinkedIn Easy-Apply AUTO-APPLIER - ENHANCED VERSION
──────────────────────────────────────────────────
• Added city/country/location handling
• Fixed resume upload issue
• Added known technologies database
• Improved Easy Apply button detection
"""

import asyncio, json, logging, base64, mimetypes, re, os
import asyncio, json, logging, base64, mimetypes, re, os, random
from pathlib import Path
import fitz
from playwright.async_api import (
    FilePayload,
    async_playwright,
    Page,
    TimeoutError as PlaywrightTimeoutError,
)

from database.linkedin_context import get_linkedin_context, save_linkedin_context
from config import LINKEDIN_CONTEXT_OPTIONS
from pdf2image import convert_from_bytes
import pytesseract
from playwright_stealth.stealth import Stealth
from config import GOOGLE_API, GROQ_API
from groq import Groq
import requests
from config import LINKEDIN_ID, LINKEDIN_PASSWORD

client = Groq(
    api_key=GROQ_API,
)
model="openai/gpt-oss-120b"

HEADLESS = os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() != "false"

# ────────────────────────── CONSTANTS ──────────────────────────

# client = genai.Client(api_key=GOOGLE_API)

LINKEDIN_LOGIN_URL = "https://www.linkedin.com/login"
RESUME_FILENAME = "RESUME.pdf"
RESUME_MIMETYPE = mimetypes.guess_type(RESUME_FILENAME)[0] or "application/pdf"
SHORT_TO = 8_000

# Profile settings
MY_GENERAL_EXPERIENCE = "1"
MY_KNOWN_TECH_EXPERIENCE = "0.6"
MY_UNKNOWN_TECH_EXPERIENCE = "0"
MY_CURRENT_CTC = "0"
MY_EXPECTED_CTC = "600000"  # 6 LPA for better opportunities
MY_NOTICE_PERIOD = "0"
FIRST_NAME = ""
LAST_NAME = ""
EMAIL = ""
PHONE = ""

# Personal location details - UPDATE THESE WITH YOUR INFO
MY_CURRENT_CITY = "Hyderabad, Andhra Pradesh"
MY_CURRENT_STATE = "Andhra Pradesh"
MY_CURRENT_COUNTRY = "India"
MY_FULL_LOCATION = f"{MY_CURRENT_CITY}, {MY_CURRENT_COUNTRY}"

# Known technologies database
KNOWN_TECHNOLOGIES = [
    # Programming Languages
    "java", "python", "javascript", "js", "typescript"
    # Web Technologies (MERN Stack)
    "mongodb", "mongo", "express", "expressjs", "react", "reactjs",
    "node", "nodejs", "html", "css", "bootstrap", "json", "xml", "next.js", "next"
    # Frameworks & Libraries
    "spring", "spring boot", "ajax",
    "rest", "restful", "api",
    # Databases
    "mysql", "sql", "postgresql", "nosql", "database",
    # Tools & Platforms
    "git", "github", "postman", "vscode", "eclipse", "intellij",
    "maven", "gradle", "npm",
    # Basic DevOps (if you've used)
    "linux", "ubuntu",
    # Add more technologies you know
    "json", "xml", "http", "https", "tcp", "ip"
]


# ─────────────────────────── LOGGING ───────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("EasyApply")

# ╭─────────────────── EasyApplyAgent ───────────────────╮
class EasyApplyAgent:
    NEXT_BTN_SEL = (
        ".artdeco-modal.jobs-easy-apply-modal "
        ".jobs-easy-apply-modal "
        "button.artdeco-button--2.artdeco-button--primary.ember-view:not([disabled])"
    )
    PRIMARY_BTN_SEL = (
        ".jobs-easy-apply-modal button.artdeco-button--primary:not([disabled])"
        ".artdeco-modal.jobs-easy-apply-modal button.artdeco-button--primary:not([disabled])"
    )

    def __init__(self, page: Page):
        self.page = page
        self.collected_questions: list[dict] = []
        self._resume_uploaded = False
        self._country_not_in_list = False
        self._country_picked = False
        self._phone_filled = False
        self._location_filled = False

    # ───────────────────────────────────────────────────────
    async def find_and_click_easy_apply(self) -> bool:
        """Better Easy Apply button detection with more selectors and retries"""
        await self.page.wait_for_load_state("domcontentloaded")
        await asyncio.sleep(2)

        selectors = [
            'a[data-view-name="job-apply-button"]:has-text("Easy Apply")',
            'a[data-view-name="job-apply-button"]',
            '[data-view-name="job-apply-button"]',
            '#jobs-apply-button-id',
            '.jobs-apply-button--top-card a:has-text("Easy Apply")',
            'button[aria-label*="Easy Apply"]',
            'a[aria-label*="Easy Apply to this job"]',
            '.jobs-apply-button--top-card button:has-text("Apply")',
            '.jobs-s-apply button:has-text("Apply")',
            '.jobs-apply-button button:has-text("Easy Apply")',
            'button[data-control-name="apply"]',
            '.jobs-apply-button button[aria-label*="Apply"]',
            'button:has-text("Apply"):has-text("Easy")',
            'button:has-text("Easy Apply")',
            'button:has-text("Apply")'
        ]

        for selector in selectors:
            try:
                log.info(f"Trying selector: {selector}")
                await self.page.wait_for_selector(selector, timeout=3000)
                buttons = await self.page.locator(selector).all()
                log.info(f"Found {len(buttons)} buttons with selector: {selector}")

                for idx, btn in enumerate(buttons):
                    try:
                        if not await btn.is_visible() or not await btn.is_enabled():
                            continue

                        text = (await btn.text_content() or "").strip()
                        log.info(f"Button {idx+1} text: '{text}'")

                        if "easy apply" in text.lower() or (selector == 'button:has-text("Apply")' and "apply" in text.lower()):
                            log.info(f"Clicking Easy Apply button: '{text}'")
                            await btn.scroll_into_view_if_needed()
                            await asyncio.sleep(0.8)

                            # Multiple click strategies for anchor tags
                            click_success = False
                            
                            # Strategy 1: Click with delay and no wait
                            try:
                                await btn.click(delay=100, no_wait_after=True, timeout=3000)
                                click_success = True
                                log.info("✅ Clicked with delay")
                            except Exception as e2:
                                log.debug(f"Delay click failed: {e2}")
                            
                            # Strategy 2: JavaScript click
                            if not click_success:
                                try:
                                    await self.page.evaluate("(b)=>b.click()", btn)
                                    click_success = True
                                    log.info("✅ Clicked with JavaScript")
                                except Exception as e3:
                                    log.debug(f"JS click failed: {e3}")
                            
                            # Strategy 3: Direct click with force
                            # if not click_success:
                            #     try:
                            #         await btn.click(force=True, timeout=3000)
                            #         click_success = True
                            #         log.info("✅ Clicked with force=True")
                            #     except Exception as e1:
                            #         log.debug(f"Force click failed: {e1}")

                            if not click_success:
                                log.warning("❌ Could not click Easy Apply button")
                                continue
                            
                            # Wait longer for modal to appear after click
                            log.info("⏳ Waiting for modal to appear...")
                            await asyncio.sleep(3)

                            # Check for modal with multiple attempts
                            modal_selectors = [
                                ".artdeco-modal-overlay.artdeco-modal-overlay--layer-default",
                                ".artdeco-modal-overlay--is-top-layer",
                                ".artdeco-modal.jobs-easy-apply-modal", 
                                "div[role='dialog'].jobs-easy-apply-modal",
                                "div.artdeco-modal",
                                "[aria-labelledby*='apply']",
                                ".artdeco-modal--layer-default"
                            ]
                            
                            modal_found = False
                            for attempt in range(5):
                                for modal_sel in modal_selectors:
                                    try:
                                        modal = await self.page.wait_for_selector(modal_sel, timeout=2000)
                                        if modal and await modal.is_visible():
                                            log.info(f"🪟 Easy-Apply modal found with: {modal_sel}")
                                            modal_found = True
                                            break
                                    except:
                                        continue
                                
                                if modal_found:
                                    log.info("✅ Modal opened successfully!")
                                    return True
                                
                                if attempt < 4:
                                    log.warning(f"Modal not visible yet, waiting... (attempt {attempt + 1}/5)")
                                    await asyncio.sleep(2)
                            
                            if not modal_found:
                                log.warning("⚠️ Modal did not appear after click, trying next selector")
                                continue
                            
                            return True

                    except Exception as e:
                        log.debug(f"Error with button {idx}: {e}")
                        continue

            except PlaywrightTimeoutError:
                log.debug(f"No elements found for selector: {selector}")
                continue
            except Exception as e:
                log.debug(f"Error with selector {selector}: {e}")
                continue

        log.warning("❌ No Easy Apply button found with any selector")
        return False

    # ───────────────────────────────────────────────────────
    async def _scroll_modal_bottom(self):
        await self.page.evaluate(
            """
            () => {
                const modal = document.querySelector('.artdeco-modal.jobs-easy-apply-modal');
                if (!modal) return;
                const walker = document.createTreeWalker(modal, NodeFilter.SHOW_ELEMENT);
                let box = null;
                while (walker.nextNode()) {
                    const el = walker.currentNode;
                    const st = getComputedStyle(el);
                    if ((st.overflowY === 'auto' || st.overflowY === 'scroll') &&
                        el.scrollHeight > el.clientHeight + 4) {
                        box = el;
                    }
                }
                (box || modal).scrollTop = (box || modal).scrollHeight;
            }
            """
        )
        await asyncio.sleep(0.4)

    # ───────────────────────────────────────────────────────
    async def _handle_location_autocomplete(self, input_element, location_text: str):
        """Handle LinkedIn's autocomplete location dropdown with NO external clicking"""
        try:
            # Clear the field completely first
            await input_element.click()
            await asyncio.sleep(0.2)
            
            # Multiple clearing attempts
            for _ in range(3):
                await input_element.press("Control+A")
                await asyncio.sleep(0.1)
                await input_element.press("Delete")
                await asyncio.sleep(0.1)
                await input_element.press("Backspace")
                await asyncio.sleep(0.1)
            
            # Verify field is empty
            current_val = await input_element.input_value()
            if current_val.strip():
                log.info(f"Field still has content: '{current_val}', force clearing...")
                await input_element.fill("")
                await asyncio.sleep(0.2)

            # Type just the city name to trigger dropdown
            city_only = location_text.split(",")[0].strip()
            log.info(f"Typing city: {city_only}")
            
            # Type character by character to ensure it's registered
            await input_element.press("Control+A")
            await asyncio.sleep(0.1)
            await input_element.press("Delete")
            await asyncio.sleep(0.1)
            await input_element.press("Backspace")
            await asyncio.sleep(0.1)

            for char in city_only:
                await input_element.type(char, delay=100)
            
            await asyncio.sleep(0.5)

            # Look for suggestion dropdown
            suggestion_selectors = [
                '.basic-typeahead__triggered-content li',
                '.typeahead-results li',
                '.typeahead-dropdown li',
                '[role="listbox"] li',
                '[role="option"]',
                '.dropdown-menu li',
                '.suggestions li',
                '.autocomplete-results li'
            ]

            suggestion_found = False
            for selector in suggestion_selectors:
                try:
                    # Wait for suggestions to appear
                    await self.page.wait_for_selector(selector, timeout=3000)
                    suggestions = await self.page.locator(selector).all()
                    
                    if suggestions:
                        log.info(f"Found {len(suggestions)} location suggestions")
                        
                        # Click the first suggestion automatically
                        first_suggestion = suggestions[0]
                        suggestion_text = await first_suggestion.text_content()
                        log.info(f"Auto-selecting first suggestion: {suggestion_text}")
                        
                        # Scroll suggestion into view if needed
                        await first_suggestion.scroll_into_view_if_needed()
                        await first_suggestion.click()
                        await asyncio.sleep(1.0)
                        
                        # Verify the selection worked
                        final_value = await input_element.input_value()
                        log.info(f"Location selected: {final_value}")
                        
                        suggestion_found = True
                        break
                        
                except Exception:
                    continue

            if not suggestion_found:
                # If no suggestions found, just press Tab to move to next field
                log.info("No suggestions dropdown found, pressing Tab to continue")
                await self.page.keyboard.press("Tab")
                await asyncio.sleep(0.5)

            # REMOVED: No external clicking that could trigger save dialog

            return True

        except Exception as e:
            log.debug(f"Location autocomplete error: {e}")
            return False

    async def _dismiss_overlays(self):
        """Dismiss any open dropdowns or overlays that might block buttons"""
        try:
            # Press Escape to close any open dropdowns
            await self.page.keyboard.press("Escape")
            await asyncio.sleep(0.3)
            
            # Click on a neutral area to dismiss overlays
            try:
                # Try to click on modal background
                await self.page.click(".artdeco-modal.jobs-easy-apply-modal", timeout=1000)
            except:
                # Fallback: click on body
                await self.page.click("body", timeout=1000)
            
            await asyncio.sleep(0.5)
            
        except Exception as e:
            log.debug(f"Error dismissing overlays: {e}")

# ───────────────────────────────────────────────────────
    async def _force_upload_resume(self, payload: FilePayload):
        """More aggressive resume upload - tries everything on every step"""
        if self._resume_uploaded:
            return

        log.info("🔍 Searching for resume upload...")

        # Strategy 1: Find ANY file input and try it
        try:
            all_file_inputs = await self.page.locator("input[type='file']").all()
            log.info(f"Found {len(all_file_inputs)} file inputs total")

            for fi in all_file_inputs:
                try:
                    # Check if it's visible or can be made visible
                    is_visible = await fi.is_visible()
                    input_id = await fi.get_attribute("id") or ""
                    input_name = await fi.get_attribute("name") or ""

                    log.info(f"File input: visible={is_visible}, id='{input_id}', name='{input_name}'")

                    # Skip cover letter inputs
                    if any(word in (input_id + input_name).lower() for word in ["cover", "letter"]):
                        log.info("⏭️ Skipping cover letter input")
                        continue

                    # Try to upload regardless of visibility
                    await fi.set_input_files(payload, timeout=3000)
                    log.info("📎 ✅ Resume uploaded successfully!")
                    self._resume_uploaded = True
                    return

                except Exception as e:
                    log.debug(f"File input attempt failed: {e}")
                    continue

        except Exception as e:
            log.debug(f"File input search failed: {e}")

        # Strategy 2: Look for upload buttons and intercept file chooser
        upload_buttons = [
            "button:has-text('Upload')",
            "button:has-text('Browse')",
            "label:has-text('Upload')",
            "[aria-label*='upload']",
            "[aria-label*='Upload']"
        ]

        for selector in upload_buttons:
            try:
                buttons = await self.page.locator(selector).all()
                for btn in buttons:
                    if not await btn.is_visible():
                        continue

                    btn_text = await btn.text_content() or ""
                    if "cover" in btn_text.lower():
                        continue

                    log.info(f"Trying upload button: {btn_text}")

                    try:
                        async with self.page.expect_file_chooser(timeout=3000) as fc_info:
                            await btn.click()

                        file_chooser = await fc_info.value
                        await file_chooser.set_files(payload)
                        log.info("📎 ✅ Resume uploaded via file chooser!")
                        self._resume_uploaded = True
                        return

                    except Exception as e:
                        log.debug(f"Upload button failed: {e}")
                        continue
            except Exception:
                continue

        log.debug("No resume upload found this step - will try next step")

    # ───────────────────────────────────────────────────────
    def _get_tech_experience(self, question_text: str) -> str:
        """Check if question contains known technologies"""
        q = question_text.lower()

        for tech in KNOWN_TECHNOLOGIES:
            if tech in q:
                log.info(f"🔧 Found known technology '{tech}' in question")
                return str(MY_KNOWN_TECH_EXPERIENCE)

        log.info("❌ Unknown technology in question")
        return MY_UNKNOWN_TECH_EXPERIENCE

    # ───────────────────────────────────────────────────────
    def _get_smart_answer(self, question_text: str, field_type: str = "text") -> str:
        """Smart answering with technology-specific experience and location handling"""
        q = question_text.lower()
        print(f"Question : '{q}'")
        # Location/Geography questions
        if any(word in q for word in [
            "city", "location", "where do you live", "current location",
            "currently reside", "based in", "located in", "hometown",
            "which city", "your location", "residing", "domicile"
        ]):
            if any(word in q for word in ["city", "which city", "current city"]):
                return MY_CURRENT_CITY
            elif any(word in q for word in ["state", "province"]):
                return MY_CURRENT_STATE
            else:
                return MY_FULL_LOCATION

        # Country questions
        if any(word in q for word in [
            "country", "which country", "current country", "nationality",
            "citizen", "citizenship", "passport", "from which country"
        ]):
            return MY_CURRENT_COUNTRY

        # Referral questions
        if any(word in q for word in [
            "referred", "referral", "reference", "recommended", "suggest",
            "how did you hear", "source", "came to know"
        ]):
            return "No" if field_type in ["radio", "select"] else "Online"

        # Experience related questions with technology check
        if any(word in q for word in [
            "experience", "years", "work experience", "total experience",
            "years of experience", "how many years", "experience do you have",
            "years have you worked", "years working", "programming experience",
            "development experience", "software experience", "coding experience"
        ]):
            tech_experience = self._get_tech_experience(question_text)
            if tech_experience != MY_UNKNOWN_TECH_EXPERIENCE:
                return tech_experience
            elif any(word in q for word in ["total", "overall", "general", "programming", "development", "software"]):
                return str(MY_GENERAL_EXPERIENCE)
            else:
                return tech_experience

        # Salary related questions
        if any(word in q for word in [
            "salary", "ctc", "current ctc", "expected ctc", "compensation",
            "package", "current salary", "expected salary", "pay", "wage",
            "expectations", "expectation"
        ]):
            if any(word in q for word in ["current", "present", "existing"]):
                return str(MY_CURRENT_CTC)
            elif any(word in q for word in ["expected", "expect", "desired", "target"]):
                return str(MY_EXPECTED_CTC)
            return str(MY_CURRENT_CTC)

        # Notice period
        if any(word in q for word in [
            "notice", "notice period", "joining", "available", "availability",
            "when can you join", "start date", "how soon"
        ]):
            return str(MY_NOTICE_PERIOD)

        # Authorization/Visa questions
        if any(word in q for word in [
            "authorized", "authorised", "visa", "permit", "eligibility", "eligible",
            "legal", "legally", "work authorization", "work permit", "right to work",
            "sponsor", "sponsorship"
        ]):
            return "Yes"

        # Relocation questions
        if any(word in q for word in [
            "relocate", "relocation", "willing to relocate", "move", "willing to move",
            "open to relocation", "comfortable relocating"
        ]):
            return "Yes"

        # Education questions
        if any(word in q for word in [
            "degree", "graduation", "education", "university", "college", "graduate",
            "bachelor", "master", "qualification", "educational background"
        ]):
            if field_type in ["radio", "select"]:
                return "Bachelor's Degree"
            return "Bachelor's Degree in Computer Science"

        # Skills/Certification questions
        if any(word in q for word in [
            "certification", "certified", "certificate", "skills", "skill",
            "proficient", "familiar", "knowledge"
        ]):
            return "Yes"

        # Availability questions
        if any(word in q for word in [
            "available", "availability", "free", "can you", "able to", "willing",
            "ready", "open to", "interested"
        ]):
            return "Yes"

        # Travel questions
        if any(word in q for word in [
            "travel", "travelling", "business travel", "willing to travel",
            "comfortable with travel"
        ]):
            return "Yes"

        # Remote work questions
        if any(word in q for word in [
            "remote", "work from home", "wfh", "telecommute", "virtual"
        ]):
            return "Yes"

        # Cover letter or additional info
        if any(word in q for word in [
            "cover letter", "additional", "why", "motivation", "tell us",
            "describe", "explain", "reason", "additional information"
        ]):
            return "I am a recent Computer Science graduate with 1 year of hands-on project experience, eager to contribute to your team and grow my career."

        # Default answers
        if field_type == "text":
            if any(word in q for word in ["how many", "number", "count"]):
                return self._get_tech_experience(question_text)
            return "Yes"
        return "Yes"

    # ───────────────────────────────────────────────────────
    async def _get_question_text(self, element) -> str:
        """Extract question text from element"""
        try:
            methods = [
                lambda: element.get_attribute("aria-label"),
                lambda: element.get_attribute("placeholder"),
                lambda: self._get_label_text(element),
                lambda: self._get_parent_text(element)
            ]

            for method in methods:
                try:
                    text = await method()
                    if text and text.strip():
                        return text.strip()
                except:
                    continue

        except Exception:
            pass

        return "Unknown question"

    async def _get_label_text(self, element):
        """Get associated label text"""
        element_id = await element.get_attribute("id")
        if element_id:
            label_elem = self.page.locator(f'label[for="{element_id}"]').first
            if await label_elem.is_visible():
                return await label_elem.text_content()
        return ""

    async def _get_parent_text(self, element):
        """Get text from parent elements"""
        return await element.evaluate("""
            el => {
                let parent = el.parentElement;
                while (parent && parent !== document.body) {
                    const text = parent.textContent;
                    if (text && text.trim().length > 10) {
                        const lines = text.trim().split('\\n').map(l => l.trim()).filter(l => l);
                        for (let line of lines) {
                            if (line.includes('?') || line.length > 15) {
                                return line.substring(0, 200);
                            }
                        }
                    }
                    parent = parent.parentElement;
                }
                return '';
            }
        """)

    # ───────────────────────────────────────────────────────
    async def _manual_india_select(self, select_element, options):
        """Manually scan options for India"""
        for i, option in enumerate(options):
            try:
                text = (await option.text_content() or "").lower()
                value = (await option.get_attribute("value") or "").lower()

                if any(india_word in (text + value) for india_word in ["india", "ind", "in"]):
                    await select_element.select_option(index=i)
                    return True
            except Exception:
                continue
        return False

    async def _handle_save_dialog(self):
        """Handle the 'Save this application?' dialog that appears"""
        try:
            # Check for save dialog
            dialog_selectors = [
                'div:has-text("Save this application?")',
                '[role="dialog"]:has-text("Save this application")',
                '.artdeco-modal:has-text("Save this application")'
            ]
            
            for selector in dialog_selectors:
                try:
                    if await self.page.locator(selector).is_visible():
                        log.info("🚨 Save dialog detected - clicking Discard")
                        
                        # Click Discard button
                        discard_btn = self.page.locator('button:has-text("Discard")').first
                        if await discard_btn.is_visible():
                            await discard_btn.click()
                            await asyncio.sleep(1)
                            log.info("✅ Clicked Discard on save dialog")
                            return True
                        break
                except:
                    continue
                    
        except Exception as e:
            log.debug(f"Error handling save dialog: {e}")
        
        return False


    async def fill_and_submit_modal(
    self,
    user: dict,
    resume_payload: FilePayload | None,
    max_steps: int = 15,
    ) -> bool:

        async def safe_click_modal_button():
            """Safely click Next/Submit buttons within modal only"""
            button_selectors = [
                # Most specific selectors first
                "button[aria-label='Submit application']:not([disabled])",
                "button[aria-label='Review your application']:not([disabled])",
                "button[aria-label*='Continue to next step']:not([disabled])",
                "button[aria-label*='Continue applying']:not([disabled])",
                
                # Text-based selectors with exact matches
                ".artdeco-modal button:has-text('Submit application'):not([disabled])",
                ".artdeco-modal button:has-text('Review'):not([disabled])",
                ".artdeco-modal button:has-text('Next'):not([disabled])",
                ".artdeco-modal button:has-text('Continue'):not([disabled])",
                
                # Fallback to primary buttons only
                ".artdeco-modal button.artdeco-button--primary:not([disabled])"
            ]
            
            for selector in button_selectors:
                try:
                    btn = self.page.locator(selector).first
                    
                    # Check if button exists and is visible
                    if not await btn.count():
                        continue
                        
                    if not await btn.is_visible():
                        continue
                    
                    # Get the actual button text (not the whole dialog)
                    label = (await btn.text_content() or "").strip()
                    
                    # Skip if the text is too long (likely grabbed dialog content)
                    if len(label) > 50:
                        log.debug(f"Skipping - text too long: {label[:50]}...")
                        continue
                    
                    # Skip if text contains unwanted content
                    if any(x in label.lower() for x in ["dialog content", "current value", "additional questions", "application powered"]):
                        log.debug(f"Skipping - contains dialog content")
                        continue
                    
                    log.info(f"➡️ Found button: '{label}' with selector: {selector}")
                    
                    await btn.scroll_into_view_if_needed()
                    await asyncio.sleep(0.5)
                    
                    log.info(f"➡️ Clicking: '{label}'")
                    
                    try:
                        await btn.click(timeout=5000)
                    except:
                        await btn.evaluate("el => el.click()")
                    
                    await asyncio.sleep(2)
                    return label.lower(), True
                except Exception as e:
                    log.debug(f"Error with selector {selector}: {e}")
                    continue
            
            log.warning("⚠️ No valid Next/Submit/Review button found")
            return "", False

        for step in range(max_steps):
            log.info(f"🔄 Wizard step {step + 1}")
            
            # Check for save dialog at start of each step
            await self._handle_save_dialog()

            # Try to upload resume on EVERY step until successful
            if resume_payload and not self._resume_uploaded:
                await self._force_upload_resume(resume_payload)

            # Handle selects and comboboxes FIRST (before text inputs)
            dropdown_roots = await self.page.locator(
                ".artdeco-modal.jobs-easy-apply-modal select, "
                ".artdeco-modal.jobs-easy-apply-modal [role='combobox']"
            ).all()

            for root in dropdown_roots:
                try:
                    # Skip disabled
                    if await root.is_hidden() or (await root.get_attribute("aria-disabled")) == "true":
                        continue
                    
                    # Check if already has a REAL selection (not default)
                    if await root.evaluate("el => el.tagName === 'SELECT'"):
                        current_value = await root.input_value()
                        if current_value and current_value.strip() and current_value.strip() not in ["", "Select an option", "Please make a selection", "Choose"]:
                            log.info(f"Dropdown already has REAL value: '{current_value}', skipping")
                            continue
                    else:
                        current_text = (await root.text_content() or "").strip().lower()
                        if current_text not in ("", "select an option", "select", "choose", "please make a selection"):
                            log.info(f"Combobox already has REAL selection: '{current_text}', skipping")
                            continue

                    question = await self._get_question_text(root)
                    self.collected_questions.append({"type": "dropdown", "text": question})
                    smart_answer = self._get_smart_answer(question, "select")

                    log.info(f"🔽 Processing dropdown: '{question}...' - Answer: '{smart_answer}'")

                    # Evaluate if the smart_answer matches any option value/text
                    options = await root.locator("option").all()
                    match_found = False
                    for i, option in enumerate(options):
                        txt = (await option.text_content() or "").strip().lower()
                        if smart_answer.lower() == txt:
                            await root.select_option(index=i)
                            log.info(f"✅ Selected matching option '{txt}'")
                            match_found = True
                            break
                    
                    # If no match found, select first or second option as fallback
                    if not match_found and len(options) >= 1:
                        await root.select_option(index=1)  #  index=1 to pick second option in list
                        log.info(f"⚠️ No matching option found; selected default first option")

                    # ENHANCED country/residence detection
                    is_country_dropdown = any(keyword in question.lower() for keyword in [
                        "country", "live", "reside", "where do you currently", "current location", 
                        "confirm the country", "which country", "country you currently live",
                        "country in which", "please confirm", "currently reside"
                    ])

                    if is_country_dropdown:
                        log.info(f"🌍 DETECTED COUNTRY DROPDOWN: {question}")
                        
                        # For native select elements
                        if await root.evaluate("el => el.tagName === 'SELECT'"):
                            options = await root.locator("option").all()
                            india_found = False
                            not_listed_index = -1
                            
                            log.info(f"📋 Found {len(options)} options in country dropdown")
                            
                            # First pass: look for India
                            for i, opt in enumerate(options):
                                txt = (await opt.text_content() or "").lower().strip()
                                val = (await opt.get_attribute("value") or "").lower().strip()
                                
                                if "india" in txt or "india" in val:
                                    await root.select_option(index=i)
                                    log.info(f"✅ FOUND AND SELECTED INDIA: {txt}")
                                    india_found = True
                                    break
                            
                            # Second pass: if India not found, look for "Not listed"
                            if not india_found:
                                log.info("🔍 INDIA NOT FOUND - SEARCHING FOR 'NOT LISTED'")
                                for i, opt in enumerate(options):
                                    txt = (await opt.text_content() or "").lower().strip()
                                    
                                    if any(phrase in txt for phrase in ["not listed", "not in list", "other", "others", "not mentioned", "not available", "unlisted"]):
                                        not_listed_index = i
                                        log.info(f"🎯 FOUND 'NOT LISTED' at index {i}: '{txt}'")
                                        break
                                
                                if not_listed_index >= 0:
                                    log.info(f"⚠️ SELECTING 'NOT LISTED' at index {not_listed_index}")
                                    await root.select_option(index=not_listed_index)
                                    await asyncio.sleep(1.0)
                                    
                                    self._country_not_in_list = True
                                    log.info("🚨 FLAG SET: _country_not_in_list = True")
                        continue

                    # Regular dropdown handling
                    else:
                        if await root.evaluate("el => el.tagName === 'SELECT'"):
                            options = await root.locator("option").all()
                            for i, opt in enumerate(options):
                                txt = (await opt.text_content() or "").lower()
                                if smart_answer.lower() in txt:
                                    await root.select_option(index=i)
                                    log.info(f"✅ Selected '{smart_answer}' in select")
                                    break

                except Exception as e:
                    log.debug(f"Dropdown error: {e}")

            # Handle follow-up country field
            if self._country_not_in_list:
                log.info("🔍 LOOKING FOR FOLLOW-UP COUNTRY TEXT FIELD...")
                await asyncio.sleep(0.5)
                
                all_text_inputs = await self.page.locator(
                    ".artdeco-modal.jobs-easy-apply-modal input[type='text'], "
                    ".artdeco-modal.jobs-easy-apply-modal textarea"
                ).all()
                
                for fu in all_text_inputs:
                    try:
                        current_value = (await fu.input_value() or "").strip()
                        if not current_value and self._country_not_in_list:
                            await fu.fill(MY_CURRENT_COUNTRY)
                            log.info(f"✅ FILLED FOLLOW-UP COUNTRY FIELD: {MY_CURRENT_COUNTRY}")
                            self._country_not_in_list = False
                            break
                    except Exception as e:
                        log.debug(f"Follow-up field error: {e}")

            # Fill text inputs
            text_inputs = await self.page.locator(
                ".artdeco-modal.jobs-easy-apply-modal input[type='text'], "
                ".artdeco-modal.jobs-easy-apply-modal input[type='number'], "
                ".artdeco-modal.jobs-easy-apply-modal input[type='email'], "
                ".artdeco-modal.jobs-easy-apply-modal input[type='tel'], "
                ".artdeco-modal.jobs-easy-apply-modal input:not([type]), "
                ".artdeco-modal.jobs-easy-apply-modal textarea"
            ).all()

            for inp in text_inputs:
                try:
                    if await inp.is_disabled():
                        continue

                    current_value = (await inp.input_value()).strip()
                    question = await self._get_question_text(inp)
                    typ = (await inp.get_attribute("type") or "").lower()
                    name = (await inp.get_attribute("name") or "").lower()
                    placeholder = (await inp.get_attribute("placeholder") or "").lower()

                    # Phone number handling - PRIORITY CHECK
                    if (typ == "tel" or 
                        any(phone_word in (name + placeholder + question.lower()) for phone_word in ["phone", "mobile", "contact"]) or
                        "phone number" in question.lower() or
                        "mobile phone" in question.lower()):
                        
                        if not self._phone_filled:
                            if not current_value or current_value.lower() == "yes" or not current_value.replace("+", "").replace("-", "").replace(" ", "").isdigit():
                                answer = user["phone"]
                                await inp.click()
                                await inp.press("Control+A")
                                await inp.press("Delete")
                                await asyncio.sleep(0.2)
                                await inp.fill(answer)
                                log.info(f"📱 Filled phone: {answer}")
                                self._phone_filled = True
                        continue

                    # Location handling
                    elif (any(word in question.lower() for word in ["location", "city", "where do you", "live", "reside"]) and 
                        not any(word in question.lower() for word in ["country"])):
                        
                        if not self._location_filled:
                            success = await self._handle_location_autocomplete(inp, MY_CURRENT_CITY)
                            if success:
                                self._location_filled = True
                        continue

                    # Skip if already filled
                    if current_value:
                        continue

                    # Other field handling
                    if typ == "email" or "email" in name:
                        await inp.fill(user["email"])
                    elif "first" in name:
                        await inp.fill(user["first"])
                    elif "last" in name:
                        await inp.fill(user["last"])
                    elif self._country_not_in_list and any(w in (placeholder + question.lower()) for w in ["country", "specify", "other"]):
                        continue
                    else:
                        answer = self._get_smart_answer(question, "text")
                        await inp.fill(answer)

                        await asyncio.sleep(0.3)  # Wait for validation
            
                        # Check for validation error
                        if any(word in question.lower() for word in ["salary", "ctc", "compensation", "pay"]):
                            try:
                                # Look for validation error message
                                error_found = False
                                error_selectors = [
                                    "span:has-text('minimum')",
                                    "span:has-text('must be')",
                                    "[role='alert']",
                                    ".error-message",
                                    ".validation-error"
                                ]
                                
                                for err_sel in error_selectors:
                                    if await self.page.locator(err_sel).count() > 0:
                                        error_found = True
                                        break
                                
                                # If validation error, retry with 100
                                if error_found or (answer == "0" and typ == "number"):
                                    log.warning(f"⚠️ Salary validation failed with '{answer}', retrying with 100")
                                    await inp.fill("100")
                                    await asyncio.sleep(0.3)
                                    log.info("✅ Filled salary with minimum value: 100")
                                    
                            except Exception:
                                pass

                except Exception as e:
                    log.debug(f"Text input error: {e}")

                if any(word in question.lower() for word in ["experience", "years", "how many years"]):
                    try:
                        int_answer = str(int(float(answer)))
                        await inp.fill(int_answer)
                        log.info(f"⚠️ Retried with integer experience answer: {int_answer}")
                    except Exception as e2:
                        log.debug(f"Fallback integer fill error: {e2}")


            # Handle radio buttons
            radios = await self.page.locator(".artdeco-modal.jobs-easy-apply-modal input[type='radio']").all()
            seen_groups = set()

            for radio in radios:
                try:
                    name = await radio.get_attribute("name") or ""
                    if not name or name in seen_groups:
                        continue
                    seen_groups.add(name)

                    group = self.page.locator(f'input[type="radio"][name="{name}"]')
                    group_radios = await group.all()

                    for r in group_radios:
                        value_attr = (await r.get_attribute("value") or "").lower()
                        rid = await r.get_attribute("id") or ""
                        lbl = self.page.locator(f'label[for="{rid}"]').first
                        lbl_txt = (await lbl.text_content() or "").lower() if await lbl.count() else ""

                        if any(x in (value_attr + lbl_txt) for x in ("yes", "true", "y", "1")):
                            if await lbl.count():
                                await lbl.click()
                            else:
                                await r.check()
                            break

                except Exception as e:
                    log.debug(f"Radio error: {e}")

            # Check for save dialog before clicking buttons
            await self._handle_save_dialog()

            # Scroll modal bottom
            await self._scroll_modal_bottom()
            await asyncio.sleep(1)

            # Safe button click
            label, clicked = await safe_click_modal_button()
            
            if not clicked:
                log.warning("No Next/Submit button found")
                return False

            # Check for save dialog after clicking
            await self._handle_save_dialog()

            # Only mark as success if "Submit application" was clicked (final submission)
            if "submit application" in label:
                log.info("🎉 Application submitted successfully!")
                await asyncio.sleep(2)  # Wait to ensure submission completes
                return True
            
            # If just "Submit" or other buttons, continue to next step
            if any(k in label for k in ("finish", "done")):
                log.info("🎉 Application completed!")
                return True

        log.error("❌ Wizard limit reached without submission")
        return False

    def reset_for_new_job(self):
        """Reset agent state for new job application"""
        self.collected_questions.clear()
        self._resume_uploaded = False
        self._country_not_in_list = False
        self._country_picked = False
        self._phone_filled = False
        self._location_filled = False
        log.info("🔄 Agent state reset for new job")


# ╰──────────────────────────────────────────────────────────╯

# ──────────────────────── HELPERS ─────────────────────────
def make_resume_payload(b64: str) -> FilePayload:
    return FilePayload(
        name= RESUME_FILENAME,
        mimeType= RESUME_MIMETYPE,
        buffer=base64.b64decode(b64),
    )


def normalize_company_name(company_name: str | None) -> str:
    if not company_name:
        return "Unknown company"
    return " ".join(str(company_name).split())

async def login(page: Page, user_id: str|None, password: str| None) -> bool:
    await page.goto(LINKEDIN_LOGIN_URL, wait_until="domcontentloaded")
    await asyncio.sleep(10)
    if "/feed" in page.url:
        log.info("✅ Already logged in")
        return True

    log.info("🔐 Logging in using provided payload credentials...")
    if not user_id or not password:
        log.error("❌ MISSING CREDENTIALS: No saved session found and no LinkedIn credentials provided in payload.")
        return False
        
    await page.fill("#username", user_id)
    await page.fill("#password", password)
    await page.click('button[type="submit"]')

    for _ in range(30):
        await asyncio.sleep(1)
        if "/feed" in page.url:
            log.info("✅ Login successful")
            return True
        if any(x in page.url for x in ("/captcha", "/challenge", "/checkpoint")):
            log.error("❌ Login challenge encountered")
            await asyncio.sleep(200)
            return False

    log.error("❌ Login timeout")
    return False

async def safe_goto(page: Page, url: str, retries: int = 3) -> bool:
    for attempt in range(retries):
        try:
            log.info(f"🌐 Navigating to job page (attempt {attempt + 1})")
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)
            return True
        except Exception as e:
            log.warning(f"Navigation attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                await asyncio.sleep(3)

    log.error(f"❌ Failed to navigate to {url}")
    return False

def extract_text_with_ocr_fallback(pdf_bytes: bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        page_text = page.get_text()
        # Ensure page_text is a string before calling strip()
        if isinstance(page_text, str):
            page_text = page_text
        else:
            page_text = str(page_text) if page_text else ""
        
        if not page_text.strip():
            # Fallback to OCR if no text found
            images = convert_from_bytes(pdf_bytes, first_page=page_num+1, last_page=page_num+1)
            ocr_text = pytesseract.image_to_string(images[0])
            text += ocr_text + "\n\n"
        else:
            text += page_text + "\n\n"
    return text

def parse_pdf(url : str):
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch: {response.status_code}")
    pdf_bytes = response.content
    extracted_text = extract_text_with_ocr_fallback(pdf_bytes)
    if not extracted_text.strip():
        print("Warning: no text extracted from PDF")
    else:
        print(f"Extracted text (preview):\n{extracted_text[:1000]}")
    return extracted_text

def gemini_prompt_builder(resume_text):
    return (
        "You are a professional resume parser. Extract the following information from the resume text below, returning valid JSON only:\n\n"
        "{\n"
        '  "candidate_name": "string with all spaces replaced by underscores",\n'
        '  "location": {\n'
        '    "city": "string or null",\n'
        '    "state": "string or null",\n'
        '    "country": "string or null",\n'
        '    "full_location": "string or null"\n'
        '  },\n'
        '  "user": {\n'
        '    "first": "string first name of the user from resume",\n'
        '    "last": "string last name of the user from the resume",\n'
        '    "email": "string email of the user from the resume",\n'
        '    "phone": "string phone number of the user from the resume"\n'
        '  },\n'
        '  "general_experience_years": "float number representing total professional experience years",\n'
        '  "known_tech_experience_years": "float number representing years of experience on explicitly known technologies in the provided list like personal projects experience",\n'
        '  "unknown_tech_experience_years": "float number representing years on any other tech or unclear mentions or else null",\n'
        '  "current_ctc": "string representing current salary or null if missing",\n'
        '  "expected_ctc": "string representing expected salary or null if missing",\n'
        '  "notice_period": "string representing notice period or null if not present",\n'
        '  "tech_stacks": ["string"],\n'
        '  "tools": ["string"],\n'
        '  "sure_skills": ["string"],\n'
        '  "additional_skills": ["string"]\n'
        "}\n\n"
        "Notes:\n"
        "- Use null for missing strings, [] for empty lists.\n"
        "- Do NOT invent any skills or tools not implied by or found in the resume text.\n"
        "- Focus only on real, clearly stated technical skills. Strictly follow the provided resume text only.\n"
        "- Additional skills must be limited to max 5, relevant to the domain/context suggested by the resume.\n"
        "- Output must be strict JSON only, no explanation or extra text.\n\n"
        "Resume text:\n\"\"\"\n"
        + resume_text +
        "\n\"\"\"\n"
    )


# ─────────────────────────── MAIN ──────────────────────────
async def main(
    jobs_queue: asyncio.Queue = None,
    user_id: str | None = None,
    password: str | None = None,
    resume_url: str | None = None,
    progress_user: str | None = None,
    log_callback = None,
    total_jobs: int = 0,
    jobs_applied_counter: list | None = None,
    user_profile: dict = None
):
    if jobs_applied_counter is None:
        jobs_applied_counter = [0]



    global RESUME_FILENAME, FIRST_NAME, LAST_NAME, EMAIL, PHONE, MY_GENERAL_EXPERIENCE, MY_KNOWN_TECH_EXPERIENCE, MY_UNKNOWN_TECH_EXPERIENCE, MY_CURRENT_CTC, MY_EXPECTED_CTC, MY_NOTICE_PERIOD, MY_CURRENT_CITY, MY_CURRENT_STATE, MY_CURRENT_COUNTRY, MY_FULL_LOCATION ,KNOWN_TECHNOLOGIES
    
    try:    

        if not resume_url:
            raise Exception("resume_url is required")
            
        
        parsed = user_profile or {}
        
        if not parsed:
            raise Exception("No user profile found in DB. Please run job search first to parse resume.")


        if parsed.get("candidate_name"):
            RESUME_FILENAME = parsed["candidate_name"]

        location = parsed.get("location", {})
        if location.get("city"):
            MY_CURRENT_CITY = location["city"]
        if location.get("state"):
            MY_CURRENT_STATE = location["state"]
        if location.get("country"):
            MY_CURRENT_COUNTRY = location["country"]
        if location.get("full_location"):
            MY_FULL_LOCATION = location["full_location"]

        user = parsed.get("user", {})
        if user.get("first"):
            FIRST_NAME = user["first"]
        if user.get("last"):
            LAST_NAME = user["last"]
        if user.get("email"):
            EMAIL = user["email"]
        if user.get("phone"):
            PHONE = user["phone"]

        if parsed.get("general_experience_years") is not None and parsed.get("general_experience_years") >= 0:
            MY_GENERAL_EXPERIENCE = parsed["general_experience_years"]
        else:
            MY_GENERAL_EXPERIENCE = 0.6  # default or fallback

        if parsed.get("known_tech_experience_years") is not None and parsed.get("known_tech_experience_years") >= 0:
            MY_KNOWN_TECH_EXPERIENCE = parsed["known_tech_experience_years"]
        else:
            MY_KNOWN_TECH_EXPERIENCE = 0.6  # default or fallback

        if parsed.get("unknown_tech_experience_years") is not None:
            MY_UNKNOWN_TECH_EXPERIENCE = parsed["unknown_tech_experience_years"]

        if parsed.get("current_ctc") is not None and float(parsed.get("current_ctc")) >= 0:
            MY_CURRENT_CTC = float(parsed["current_ctc"])

        if parsed.get("expected_ctc") is not None and float(parsed.get("expected_ctc")) >= 0:
            MY_EXPECTED_CTC = float(parsed["expected_ctc"])

        if parsed.get("notice_period") is not None:
            MY_NOTICE_PERIOD = float(parsed["notice_period"])

        if parsed.get("tech_stacks") or parsed.get("tools") or parsed.get("sure_skills") or parsed.get("additional_skills"):
            KNOWN_TECHNOLOGIES = (
                parsed.get("tech_stacks", []) + 
                parsed.get("tools", []) + 
                parsed.get("sure_skills", []) + 
                parsed.get("additional_skills", [])
            )
    
    except Exception as e:
        print(f"fetching details from resume failed in applier agent: {e}")
    
 # ── Load jobs ─────────────────────────────────────────────────────────────

    if total_jobs == 0:
        total_jobs = 1

    log.info(f"📋 Loaded {total_jobs} job(s) to process via Queue")

   # ── Browser setup ─────────────────────────────────────────────────────────

    if log_callback:
        log_callback({"progress": 6, "status": "processing", "message": "Connecting to LinkedIn..."})
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(
        headless=True,
        args=[
            '--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu', '--no-zygote', '--disable-extensions', '--disable-background-networking', '--disable-renderer-backgrounding', '--no-first-run', '--mute-audio', '--metrics-recording-only'
        ]        
                                       )

    try:
        db_context = None
        if not progress_user:
            raise Exception("Progress user not found")
        db_context = get_linkedin_context(progress_user)
        
        if db_context:
            print(f"FOUND STORAGE STATE IN DB!")
            print(f"Creating new context with current browser using saved state!")
            context = await browser.new_context(
                storage_state=db_context,
                **LINKEDIN_CONTEXT_OPTIONS,
            )
        else:
            context = await browser.new_context(**LINKEDIN_CONTEXT_OPTIONS)
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)


        if not await login(page, user_id, password):
            return
        if log_callback:
            log_callback({"progress": 8, "status": "processing", "message": "LinkedIn session ready"})

        try:
            save_linkedin_context(progress_user,dict(await context.storage_state()))
        except Exception as e:
            log.warning(f"Could not persist LinkedIn storage state: {e}")

        agent = EasyApplyAgent(page)
        applied = []
        failed = []

        # ── Helper: emit progress after each job outcome ──────────────
        def emit(success: bool, current_url: str | None, company_name: str | None, reason: str =""):
            jobs_applied_counter[0] += 1
            progress = min(int((jobs_applied_counter[0] / total_jobs) * 89) + 11, 99)

            company = normalize_company_name(company_name)

            # Verbose console log for debugging
            if success:
                print(f"[apply] ✅ Applied ({jobs_applied_counter[0]}/{total_jobs}) - {company}")
            else:
                reason_part = f": {reason}" if reason else ""
                print(f"[apply] ❌ Skipped ({jobs_applied_counter[0]}/{total_jobs}) - {company}{reason_part}")

            # User-friendly Redis stream message
            if log_callback:
                if success:
                    msg = f"Applied {jobs_applied_counter[0]}/{total_jobs} - {company}"
                else:
                    reason_part = f": {reason}" if reason else ""
                    msg = f"Skipped {jobs_applied_counter[0]}/{total_jobs} - {company}{reason_part}"
                
                log_callback({
                    "progress": progress,
                    "status":   "applied" if success else "skipped",
                    "message":  msg,
                    "job_url":  current_url,
                    "job_company": company,
                    "success":  success,
                })

        # ── Per-job apply loop ────────────────────────────────────────────────
        while True:
            batch = await jobs_queue.get()
            if batch is None:
                # Poison pill received
                break
            
            for idx, job in enumerate(batch, 1):
                url, b64 = job.get("job_url"), job.get("resume_binary")
                company_name = job.get("company_name")
                if not url or not b64:
                    log.warning(f"Job {idx}: missing data - skipped")
                    emit(False, url, company_name, "incomplete job data") 
                    continue

                log.info(f"\n{'='*60}")
                log.info(f"📍 Processing Job {idx}/{len(batch)}")
                log.info(f"🔗 URL: {url}")
                log.info(f"{'='*60}")
                
                if not await safe_goto(page, url):
                    failed.append(url)
                    emit(False, url, company_name, "page unavailable") 
                    continue
                
                payload = make_resume_payload(b64)
                agent.reset_for_new_job()

                # ── Find Easy Apply button ────────────────────────────────────

                if not await agent.find_and_click_easy_apply():
                    log.warning("No Easy Apply button found - skipping")
                    failed.append(url)
                    emit(False, url, company_name, "direct apply only")
                    continue

                # ── Fill & submit modal ───────────────────────────────────────

                success = await agent.fill_and_submit_modal(
                    user={
                        "first": FIRST_NAME,
                        "last": LAST_NAME,
                        "email": EMAIL,
                        "phone": PHONE,
                    },
                    resume_payload=payload,
                )

                if success:
                    applied.append(url)
                    log.info(f"✅ Job {idx} applied successfully! Total: {applied}")
                else:
                    failed.append(url)
                    log.warning(f"❌ Job {idx} application failed")

                emit(success, url, company_name)

                # Show questions captured
                if agent.collected_questions:
                    print(f"\n📝 Questions captured for Job {idx}:")
                    for q in agent.collected_questions:
                        print(f"  • [{q['type']}] {q['text']}...")

                await asyncio.sleep(3)

        # ── Batch summary log ─────────────────────────────────────────────

        log.info(f"\n{'='*60}")
        log.info(f"🎯 FINAL RESULTS:")
        log.info(f"✅ Successfully applied: {len(applied)}")
        log.info(f"❌ Failed applications: {len(failed)}")
        log.info(f"📊 Success rate: {(len(applied)/(len(applied)+len(failed))*100):.1f}%")
        log.info(f"{'='*60}")


        return {
            "applied": applied,
            "failed": failed,
            "success_rate": round(
                len(applied) / (len(applied) + len(failed)) * 100, 2
            ) if (len(applied) + len(failed)) > 0 else 0,
        }

    finally:
        await context.close()
        await browser.close()
        await pw.stop()

if __name__ == "__main__":
    asyncio.run(main(resume_url="https://uunldfxygooitgmgtcis.supabase.co/storage/v1/object/sign/user-resume/1756181362034_Sai%20%20Balaji%20.Net%20AWS.pdf?token=eyJraWQiOiJzdG9yYWdlLXVybC1zaWduaW5nLWtleV9iZjI4OTBiZS0wYmYxLTRmNTUtOTI3Mi0xZGNiNTRmNzNhYzAiLCJhbGciOiJIUzI1NiJ9.eyJ1cmwiOiJ1c2VyLXJlc3VtZS8xNzU2MTgxMzYyMDM0X1NhaSAgQmFsYWppIC5OZXQgQVdTLnBkZiIsImlhdCI6MTc1NjE4MTM2MywiZXhwIjoxNzU2MjY3NzYzfQ.t1ovmlXr_dpQJSVJFe-6cFsiysReflatBIv3UjlBBUw"))

def run_apply_pipeline(job_id: str, job_data: dict, log_callback):
    """
    Entry point for the apply_jobs Worker.
    Orchestrates the resume parsing and Playwright auto-apply.
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_async_apply_pipeline(job_id, job_data, log_callback))
        finally:
            loop.close()
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise e

async def _async_apply_pipeline(job_id: str, job_data: dict, log_callback):
    from config import supabase
    import json

    user_id = job_data["user_id"]
    input_data = job_data.get("input_data", {})
    output_data = job_data.get("output_data") or {}

    email = input_data.get("user_id") # email is passed
    resume_url = input_data.get("resume_url")
    jobs_to_apply = input_data.get("jobs", [])

    # Extract credentials from payload
    l_email = input_data.get("linkedin_id")
    l_pass = input_data.get("linkedin_password")

    if not jobs_to_apply:
        raise Exception("No jobs provided to apply to")

    log_callback({"progress": 2, "status": "in_progress", "message": "Initializing auto-applier pipeline..."})

    total_jobs = len(jobs_to_apply)

    # Fetch pre-parsed user profile + prior apply history for resume-aware idempotency.
    user_res = supabase.table("User").select("user_data, applied_jobs").eq("id", user_id).execute()
    user_row = user_res.data[0] if user_res.data else {}
    user_profile = user_row.get("user_data", {}) or {}
    history_applied = set(user_row.get("applied_jobs") or [])

    # Resume from any checkpoint already persisted on this session's row.
    applied_so_far = list(output_data.get("applied", []))
    failed_so_far = list(output_data.get("failed", []))

    # Within this job_id: skip jobs already applied OR failed (don't redo work).
    # Across sessions (new job_id): also skip jobs already successfully applied.
    processed = set(applied_so_far) | set(failed_so_far) | history_applied
    remaining = [j for j in jobs_to_apply if j.get("job_url") not in processed]

    # Everything already processed — finalize without launching the browser.
    if not remaining:
        result = {
            "applied": applied_so_far,
            "failed": failed_so_far,
            "total_jobs": total_jobs,
        }
        log_callback({"progress": 100, "status": "done", "message": "All selected jobs already processed."})
        supabase.table("workflow_sessions").update({
            "status": "completed",
            "output_data": result,
        }).eq("id", job_id).execute()
        return

    log_callback({"progress": 5, "status": "in_progress", "message": f"Applying to {len(remaining)} remaining of {total_jobs} jobs..."})

    # ── Durable per-job checkpoint ────────────────────────────────────────
    # Wraps log_callback: forwards every event to Redis, and on each terminal
    # per-job outcome (applied/skipped) persists progress to the DB so a
    # re-triggered worker never re-applies an already-processed job.
    def checkpoint_callback(ev):
        log_callback(ev)
        if not isinstance(ev, dict):
            return
        url = ev.get("job_url")
        status = ev.get("status")
        if not url or status not in ("applied", "skipped"):
            return
        if status == "applied":
            applied_so_far.append(url)
        else:
            failed_so_far.append(url)
        try:
            supabase.table("workflow_sessions").update({
                "output_data": {
                    "applied": applied_so_far,
                    "failed": failed_so_far,
                    "total_jobs": total_jobs,
                }
            }).eq("id", job_id).execute()
            # Persist successful applies to User.applied_jobs immediately so a
            # brand-new job_id (minted after a failed row) also skips them.
            if status == "applied":
                merged = list(history_applied | set(applied_so_far))
                supabase.table("User").update({"applied_jobs": merged}).eq("id", user_id).execute()
        except Exception as e:
            print(f"Checkpoint write failed: {e}")

    jobs_queue = asyncio.Queue()

    # ── Producer function: Batched Tailoring (only the remaining jobs) ──
    async def tailor_producer():
        try:
            from agents.tailor import process_batch, extract_facts, extract_resume_text
            user_data_str = json.dumps(user_profile) if user_profile else None
            # PASS 1 (atomic-fact extraction) is JD-independent — run it ONCE for the whole
            # run instead of once per batch, then thread `facts` into every process_batch.
            # Keeps the run at +1 Gemini call total. If it fails, fall back to facts=None
            # and let each batch self-extract (back-compatible).
            facts = None
            try:
                original_txt = await asyncio.to_thread(extract_resume_text, resume_url)
                facts = await asyncio.to_thread(extract_facts, original_txt)
            except Exception as e:
                print(f"[tailor] PASS 1 hoist failed ({e}); each batch will self-extract")
            # 15 jobs per batch = one Gemini call (RPM-cheap on free tier). process_batch
            # -> tailor_jobs sends all 15 in one structured-output call (max_output_tokens
            # is the model max), and only splits into smaller calls if that truncates.
            batch_size = 15
            remaining_count = len(remaining)
            for i in range(0, remaining_count, batch_size):
                batch_jobs = remaining[i:i+batch_size]
                # Only log to Redis on the first batch to reduce noise
                if i == 0:
                    log_callback({"progress": 10, "status": "tailoring", "message": "Tailoring resumes..."})
                print(f"[tailor] Processing batch {(i//batch_size)+1} of {((remaining_count-1)//batch_size)+1}...")
                # process_batch is synchronous logic running outside loop
                tailored_batch = await asyncio.to_thread(process_batch, resume_url, batch_jobs, user_data_str, 0, facts) # template=0 explicitly
                await jobs_queue.put(tailored_batch)
            # Send poison pill to signal queue exhaustion
            await jobs_queue.put(None)
        except Exception as e:
            print(f"Producer thread died: {e}")
            await jobs_queue.put(None)

    # Launch Producer in background
    producer_task = asyncio.create_task(tailor_producer())

    # Consumer (Playwright Application Loop). The counter is pre-seeded with the
    # number of jobs already accounted for so progress resumes rather than
    # restarting at 0, and the checkpoint callback persists each outcome.
    await main(
        jobs_queue=jobs_queue,
        user_id=l_email,
        password=l_pass,
        progress_user=email,
        resume_url=resume_url,
        log_callback=checkpoint_callback,
        total_jobs=total_jobs,
        jobs_applied_counter=[total_jobs - len(remaining)],
        user_profile=user_profile
    )

    # Await producer to gracefully stop
    await producer_task

    # Build the final result from the durable accumulators (the checkpoint has
    # gathered the full set, including any pre-existing outcomes from a resume).
    total_done = len(applied_so_far) + len(failed_so_far)
    result = {
        "applied": applied_so_far,
        "failed": failed_so_far,
        "total_jobs": total_jobs,
        "success_rate": round(len(applied_so_far) / total_done * 100, 2) if total_done > 0 else 0,
    }

    log_callback({"progress": 100, "status": "done", "message": f"Workflow Complete! Applied: {len(applied_so_far)}, Failed: {len(failed_so_far)}"})

    # Update DB state
    supabase.table("workflow_sessions").update({
        "status": "completed",
        "output_data": result
    }).eq("id", job_id).execute()

    # Final merge into User.applied_jobs (checkpoint already did this incrementally).
    if applied_so_far and user_id:
        try:
            merged = list(history_applied | set(applied_so_far))
            supabase.table("User").update({"applied_jobs": merged}).eq("id", user_id).execute()
        except Exception as e:
            print(f"Failed to update User.applied_jobs: {e}")
