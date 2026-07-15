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
import asyncio, json, logging, base64, mimetypes, re, os, random, math
from pathlib import Path
import fitz
from playwright.async_api import (
    FilePayload,
    async_playwright,
    Page,
    TimeoutError as PlaywrightTimeoutError,
)

from database.linkedin_context import get_linkedin_context, save_linkedin_context, clear_linkedin_context
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
    "java", "python", "javascript", "js", "typescript",
    # Web Technologies (MERN Stack)
    "mongodb", "mongo", "express", "expressjs", "react", "reactjs",
    "node", "nodejs", "html", "css", "bootstrap", "json", "xml", "next.js", "next",
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

    def __init__(self, page: Page, user_id: str = None, user_profile: dict = None):
        self.page = page
        self.user_id = user_id
        self.user_profile = user_profile or {}
        self.collected_questions: list[dict] = []
        self._resume_uploaded = False
        self._country_not_in_list = False
        self._country_picked = False
        self._phone_filled = False
        self._location_filled = False
        self._field_attempts = {}
        self._scouted_unknowns = []
        self.active_modal_sel = ".artdeco-modal"

    # ───────────────────────────────────────────────────────
    async def find_and_click_easy_apply(self) -> bool:
        """Better Easy Apply button detection with more selectors and retries"""
        await self.page.wait_for_load_state("domcontentloaded")
        await asyncio.sleep(2)

        # Smart dismiss of page-load blocking dialogs
        try:
            blocking_dialogs = await self.page.locator('div[role="dialog"], .artdeco-modal').all()
            for dlg in blocking_dialogs:
                if await dlg.is_visible():
                    log.info("⌨️ Blocking page-load dialog detected. Pressing Escape to dismiss...")
                    await self.page.keyboard.press("Escape")
                    await asyncio.sleep(0.5)
                    break
        except Exception as esc_e:
            log.debug(f"Smart Escape key press failed: {esc_e}")

        # Check if job is no longer accepting applications
        try:
            not_accepting = await self.page.locator('text="No longer accepting applications"').count()
            if not_accepting > 0:
                log.warning("⚠️ Job is no longer accepting applications.")
                raise Exception("NO_LONGER_ACCEPTING")
        except Exception as e:
            if str(e) == "NO_LONGER_ACCEPTING":
                raise e
            log.debug(f"Error checking for not accepting status: {e}")

        # Check if already applied (using class-free, regex-based text matching to prevent LinkedIn selector breakage)
        try:
            import re
            # Regex patterns for already applied status texts (e.g. "Applied", "Applied 3 days ago", "Application submitted")
            # This strictly excludes job titles like "Applied Scientist" or "Applied Mathematics"
            applied_pattern = re.compile(
                r'^(applied|application submitted)(\s+on\s+.*|\s+yesterday|\s+\d+\s+(day|week|month|year|hour|minute)s?\s+ago)?$',
                re.IGNORECASE
            )
            
            # Find all text elements on the page that start with "applied" or "application" (case-insensitive)
            # using Playwright's text selectors which match any element
            has_applied = False
            for text_query in ["Applied status", "Application submitted"]:
                loc = self.page.locator(f'text="{text_query}"')
                count = await loc.count()
                for i in range(count):
                    el = loc.nth(i)
                    if await el.is_visible():
                        txt = (await el.text_content() or "").strip()
                        # Verify the text matches our strict pattern and is short
                        if len(txt) < 50 and applied_pattern.match(txt):
                            log.info(f"✅ Already applied to this job in the past. Found text: '{txt}'")
                            has_applied = True
                            break
                if has_applied:
                    break
            
            if has_applied:
                raise Exception("ALREADY_APPLIED")
        except Exception as e:
            if str(e) == "ALREADY_APPLIED":
                raise e
            log.debug(f"Error checking for already applied status: {e}")

        selectors = [
            'button[aria-label*="Easy Apply"]',
            'a[aria-label*="Easy Apply to this job"]',
            'button:has-text("Easy Apply")',
            'a[data-view-name="job-apply-button"]:has-text("Easy Apply")',
            '.jobs-apply-button--top-card button:has-text("Easy Apply")',
            '.jobs-apply-button button:has-text("Easy Apply")',
            'button:has-text("Apply"):has-text("Easy")'
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

                        if "easy apply" in text.lower():
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

                            # --- Evidence-Based Modal Detection ---
                            modal_selectors = [
                                "div[role='dialog']",
                                ".artdeco-modal",
                                "[aria-labelledby='dialog-header']",
                                ".jobs-easy-apply-modal"
                            ]
                            
                            app_modal_found = False
                            for attempt in range(8):
                                current_modal = None
                                # Try to find any visible modal
                                for modal_sel in modal_selectors:
                                    try:
                                        modals = await self.page.locator(modal_sel).all()
                                        for m in modals:
                                            if await m.is_visible():
                                                current_modal = m
                                                self.active_modal_sel = modal_sel
                                                break
                                        if current_modal:
                                            break
                                    except:
                                        continue
                                
                                if current_modal:
                                    # We found a modal. Let's gather evidence.
                                    dlg_text = (await current_modal.text_content() or "").lower()
                                    
                                    # 1. Is it the Safety Reminder?
                                    if any(x in dlg_text for x in ["safety reminder", "research the company", "suspicious jobs", "job search safety"]):
                                        log.info("🛡️ Job search safety reminder detected. Looking for Continue applying button...")
                                        btns = await current_modal.locator('button, a, span, [role="button"]').all()
                                        for b in btns:
                                            if await b.is_visible():
                                                b_text = (await b.text_content() or "").strip().lower()
                                                b_href = ""
                                                try:
                                                    b_href = (await b.get_attribute("href") or "").lower()
                                                except:
                                                    pass
                                                
                                                if "continue" in b_text or "/apply" in b_href:
                                                    log.info(f"🎯 Clicking button on safety reminder (text: '{b_text}', href: '{b_href}')")
                                                    try:
                                                        await b.click()
                                                    except:
                                                        await self.page.evaluate("(b)=>b.click()", b)
                                                    
                                                    # Actively wait for it to disappear
                                                    for _ in range(5):
                                                        if not await current_modal.is_visible():
                                                            break
                                                        await asyncio.sleep(0.5)
                                                    break
                                        await asyncio.sleep(1)
                                        continue # Go to next attempt to find the REAL modal
                                    
                                    # 2. Is it an Intermediate Resume/Unsubmitted Dialog?
                                    if any(x in dlg_text for x in ["resume", "unsubmitted"]) and any(x in dlg_text for x in ["application", "apply", "continue"]):
                                        log.info("🕵️ Intermediate dialog detected. Checking buttons...")
                                        btns = await current_modal.locator('button').all()
                                        for b in btns:
                                            if await b.is_visible() and await b.is_enabled():
                                                b_text = (await b.text_content() or "").strip().lower()
                                                if any(x in b_text for x in ["continue", "resume", "start new"]):
                                                    log.info(f"🎯 Clicking intermediate dialog button: '{b_text}'")
                                                    await b.click()
                                                    for _ in range(5):
                                                        if not await current_modal.is_visible():
                                                            break
                                                        await asyncio.sleep(0.5)
                                                    break
                                        await asyncio.sleep(1)
                                        continue # Go to next attempt
                                        
                                    # 3. Is it the actual Application Modal?
                                    # We default to True as long as it's not a safety reminder or intermediate resume dialog,
                                    # ensuring high resilience against dynamic copy updates on LinkedIn.
                                    log.info("✅ Verified Application Modal (assumed valid as not a safety/resume intermediate dialog)")
                                    app_modal_found = True
                                    break
                                
                                await asyncio.sleep(2)
                                
                            if not app_modal_found:
                                log.warning("❌ Application Modal did not appear or could not be verified.")
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
            (selector) => {
                const modal = document.querySelector(selector);
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
            """, self.active_modal_sel
        )
        await asyncio.sleep(0.4)

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
                await self.page.click(self.active_modal_sel, timeout=1000)
            except:
                # Fallback: click on body
                await self.page.click("body", timeout=1000)
            
            await asyncio.sleep(0.5)
            
        except Exception as e:
            log.debug(f"Error dismissing overlays: {e}")

# ───────────────────────────────────────────────────────
    async def _force_upload_resume(self, payload: FilePayload):
        """More aggressive resume upload - tries everything on every step"""
        if getattr(self, '_resume_uploaded', False):
            return

        log.info("🔍 Searching for resume upload...")

        # Strategy 1: Find ANY file input and try it
        try:
            all_file_inputs = await self.page.locator("input[type='file']").all()
            log.info(f"Found {len(all_file_inputs)} file inputs total")

            for fi in all_file_inputs:
                try:
                    is_visible = await fi.is_visible()
                    input_id = await fi.get_attribute("id") or ""
                    input_name = await fi.get_attribute("name") or ""

                    log.info(f"File input: visible={is_visible}, id='{input_id}', name='{input_name}'")

                    # Skip cover letter inputs
                    if any(word in (input_id + input_name).lower() for word in ["cover", "letter"]):
                        log.info("⏭️ Skipping cover letter input")
                        continue

                    # Try to upload regardless of visibility
                    for upload_attempt in range(2):
                        try:
                            await fi.set_input_files(payload, timeout=3000)
                            log.info("📎 ✅ Resume uploaded successfully!")
                            self._resume_uploaded = True
                            await asyncio.sleep(2) # let LinkedIn process
                            return
                        except Exception as up_e:
                            if upload_attempt == 1:
                                log.warning("⚠️ Resume upload failed twice, moving on anyway.")
                                self._resume_uploaded = True
                                return
                            log.warning("⚠️ Resume upload failed, retrying...")
                            await asyncio.sleep(1)

                except Exception as e:
                    log.debug(f"File input attempt failed: {e}")
                    continue

        except Exception as e:
            log.debug(f"File input search failed: {e}")

        # Strategy 2: Look for 'Upload resume' buttons that trigger file choosers
        if not getattr(self, '_resume_uploaded', False):
            try:
                upload_buttons = await self.page.locator(
                    f"{self.active_modal_sel} button:has-text('Upload'), "
                    f"{self.active_modal_sel} button[aria-label*='upload' i], "
                    f"{self.active_modal_sel} [data-test-upload-button]"
                ).all()
                
                for btn in upload_buttons:
                    try:
                        if not await btn.is_visible() or not await btn.is_enabled():
                            continue
                        
                        log.info(f"Clicking upload button: {(await btn.text_content() or '').strip()}")
                        await btn.click(timeout=3000)
                        await asyncio.sleep(2) # Give filechooser time to be intercepted
                        
                        if getattr(self, '_resume_uploaded', False):
                            return
                    except Exception as btn_e:
                        log.debug(f"Upload button click failed: {btn_e}")
                        
            except Exception as strat2_e:
                log.debug(f"Strategy 2 search failed: {strat2_e}")

        log.debug("No resume upload found this step - will try next step")

    # ───────────────────────────────────────────────────────
    def _get_tech_experience(self, question_text: str) -> str:
        """Check if question contains known technologies"""
        q = question_text.lower()
        import math

        for tech in KNOWN_TECHNOLOGIES:
            if tech in q:
                log.info(f"🔧 Found known technology '{tech}' in question")
                try:
                    val = float(MY_KNOWN_TECH_EXPERIENCE)
                    return "0" if val < 1 else str(int(math.floor(val)))
                except Exception:
                    return str(MY_KNOWN_TECH_EXPERIENCE)

        log.info("❌ Unknown technology in question")
        return None

    # ───────────────────────────────────────────────────────
    def _get_smart_answer(self, question_text: str, field_type: str = "text") -> str:
        """Smart answering with technology-specific experience and location handling"""
        q = question_text.lower()
        print(f"Question : '{q}'")
        
        # ── Smart Hardcoding (Bypass AI entirely) ──
        # ECTC / Expected Salary
        if any(word in q for word in [
            "ectc", "expected ctc", "expected fixed component", "expected salary",
            "expectation", "desired salary", "target salary", "compensation expectation"
        ]):
            return "Negotiable"

        # Serving/On Notice Period Yes/No
        if any(word in q for word in ["serving your notice", "serving notice", "serving a notice", "on notice period", "on notice"]):
            return "No"

        # Notice Period
        if any(word in q for word in [
            "notice period", "how soon can you join",
            "available to join", "join immediately"
        ]):
            return "Immediate"
            
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

        if "middle name" in q:
            return ""

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
            if tech_experience is not None:
                return tech_experience
            elif any(word in q for word in ["total", "overall", "general", "programming", "development", "software"]):
                try:
                    import math
                    val = float(MY_GENERAL_EXPERIENCE)
                    return "0" if val < 1 else str(int(math.floor(val)))
                except Exception:
                    return str(MY_GENERAL_EXPERIENCE)
            else:
                return None

        # Salary related questions
        if any(word in q for word in [
            "salary", "ctc", "current ctc", "expected ctc", "compensation",
            "package", "current salary", "expected salary", "pay", "wage",
            "expectations", "expectation"
        ]):
            if field_type == "number":
                if any(word in q for word in ["current", "present", "existing"]):
                    return str(int(MY_CURRENT_CTC))
                elif any(word in q for word in ["expected", "expect", "desired", "target"]):
                    return str(int(MY_EXPECTED_CTC))
                return str(int(MY_CURRENT_CTC))
            else:
                if any(word in q for word in ["current", "present", "existing"]):
                    return str(MY_CURRENT_CTC)
                elif any(word in q for word in ["expected", "expect", "desired", "target"]):
                    return "Negotiable"
                return str(MY_CURRENT_CTC)

        # Notice period / availability / joining timeline
        if any(word in q for word in [
            "notice", "notice period", "joining", "available", "availability",
            "when can you join", "start date", "how soon", "takes to join",
            "take you to join", "how long", "joining timeline", "earliest start",
            "time to join", "earliest join", "days to start", "days notice",
            "weeks notice", "months notice"
        ]):
            try:
                days = int(float(MY_NOTICE_PERIOD))
            except:
                days = 0

            # If it's a number field or specifically asks for number of days/weeks/months
            if field_type == "number" or any(x in q for x in ["days", "weeks", "months", "how many", "number"]):
                if "month" in q:
                    months = round(days / 30)
                    return str(max(1 if days > 0 else 0, months))
                if "week" in q:
                    weeks = round(days / 7)
                    return str(max(1 if days > 0 else 0, weeks))
                return str(days)
            # If it's a Yes/No question about serving notice period
            if "serving" in q or "are you on notice" in q:
                if days == 0:
                    return "No"
                else:
                    return "Yes"
            
            # Text or dropdown
            if days == 0:
                if field_type in ["radio", "select"]:
                    return "Immediate"
                return "Immediate"
            else:
                return f"{days} days"

        # Authorization/Visa questions
        if any(word in q for word in [
            "authorized", "authorised", "visa", "permit", "eligibility", "eligible",
            "legal", "legally", "work authorization", "work permit", "right to work",
            "sponsor", "sponsorship"
        ]):
            # Detect if it's asking about a foreign country
            foreign_country_pattern = r'\b(u\.s\.?|us|united states|u\.k\.?|uk|united kingdom|canada|australia|europe|eu|germany|new zealand|usa)\b'
            mentions_foreign_country = bool(re.search(foreign_country_pattern, q))
            mentions_my_country = MY_CURRENT_COUNTRY.lower() in q
            
            is_foreign = mentions_foreign_country and not mentions_my_country
            
            # Sponsorship vs Authorization
            is_sponsorship_q = any(word in q for word in ["sponsor", "sponsorship", "require visa"])
            
            if is_foreign:
                # If foreign job: Not authorized (usually), and DO require sponsorship
                return "Yes" if is_sponsorship_q else "No"
            else:
                # If domestic job (or no country mentioned): Authorized, and NO sponsorship needed
                return "No" if is_sponsorship_q else "Yes"

        # Default answers - return None for unknown so Groq is triggered
        if field_type == "text":
            if any(word in q for word in ["how many", "number", "count"]):
                tech_exp = self._get_tech_experience(question_text)
                return tech_exp if tech_exp is not None else None
            return None
        return None

    def _get_fallback_guess(self, question_text: str, field_type: str = "text") -> str:
        """Fallback guesswork for when the Groq API hits rate limits or fails"""
        q = question_text.lower()
        
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

        # Default fallback answers
        if field_type == "text":
            if any(word in q for word in ["how many", "number", "count", "years", "experience"]):
                return "0"
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
                f"{self.active_modal_sel}:has-text('Save this application')"
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

    async def _ask_groq_batch(self, questions: list[str]) -> dict:
        """Batch ask Groq for unknown questions, cache them in Supabase"""
        if not questions:
            return {}
            
        log.info(f"🧠 Asking Groq for {len(questions)} unknown questions...")
        
        prompt = f"""
You are an expert AI filling out a job application for this user.
Answer the following questions based strictly on the user profile below.
Return ONLY a valid JSON object mapping the exact question string to the answer string.
For numeric questions (like years of experience), return a single number string (e.g. "2" not "2 years").
For Yes/No questions, return "Yes" or "No".
Explicitly extract matching keywords and technologies from the profile to answer specific experience questions.
If the profile doesn't have the info, make a reasonable, professional guess.
Do NOT ask to confirm user details or output conversational text. Output ONLY valid JSON.

User Profile:
{json.dumps(self.user_profile, indent=2)}

Questions:
{json.dumps(questions, indent=2)}
"""
        try:
            completion = await asyncio.to_thread(
                client.chat.completions.create,
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that outputs only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            response_text = completion.choices[0].message.content
            new_answers = json.loads(response_text)
            
            # Update cache in memory
            if "cached_answers" not in self.user_profile:
                self.user_profile["cached_answers"] = {}
                
            self.user_profile["cached_answers"].update(new_answers)
            
            # Persist cache to DB immediately to avoid data loss
            if self.user_id:
                try:
                    from config import supabase
                    # Use the email column as requested by user
                    existing = supabase.table("User").select("user_data").eq("email", self.user_id).single().execute()
                    current_data = existing.data.get("user_data") or {}
                    current_data["cached_answers"] = self.user_profile["cached_answers"]
                    supabase.table("User").update({"user_data": current_data}).eq("email", self.user_id).execute()
                    log.info(f"💾 Incremental cache persisted to Supabase for {self.user_id}")
                except Exception as e:
                    log.warning(f"Incremental cache save failed: {e}")
            # Supabase is updated once at the end of the entire pipeline.
            return new_answers
            
        except Exception as e:
            log.error(f"Groq API error or rate limit hit: {e}. Using fallback guesswork.")
            fallback_answers = {}
            for q in questions:
                fallback_answers[q] = self._get_fallback_guess(q, "text")
                
            if "cached_answers" not in self.user_profile:
                self.user_profile["cached_answers"] = {}
            self.user_profile["cached_answers"].update(fallback_answers)
            
            return fallback_answers

    def _get_cached_or_smart_answer(self, question: str, field_type: str = "text") -> str:
        # 1. Regex check
        ans = self._get_smart_answer(question, field_type)
        if ans is not None:
            return ans
            
        # 2. Cache check
        cached = self.user_profile.get("cached_answers", {})
        if question in cached:
            log.info(f"🧠 Retrieved '{question}' from cache")
            return str(cached[question])
            
        # 3. Last resort fallback
        if field_type == "text":
            if any(word in question.lower() for word in ["how many", "number", "count", "years", "experience"]):
                return "0"
            return "Yes"
        return "Yes"



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
                f"{self.active_modal_sel} button:has-text('Submit application'):not([disabled])",
                f"{self.active_modal_sel} button:has-text('Review'):not([disabled])",
                f"{self.active_modal_sel} button:has-text('Next'):not([disabled])",
                f"{self.active_modal_sel} button:has-text('Continue'):not([disabled])",
                
                # Fallback to primary buttons only
                f"{self.active_modal_sel} button.artdeco-button--primary:not([disabled])"
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
                    
                    # ── SCOUT MODE: End of form detection ──
                    label_lower = label.lower()
                    if any(x in label_lower for x in ["review", "submit", "finish", "done", "apply"]):
                        if self._scouted_unknowns:
                            pass # removed local import
                            log.info(f"🕵️ Scout Mode: Reached end of form ({label}). Deferring job to get answers for {len(self._scouted_unknowns)} questions.")
                            raise Exception(f"DEFER_JOB:{json.dumps(self._scouted_unknowns)}")
                    
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

            # Dismiss overlay dialogs if multiple dialogs are visible (e.g. intermediate confirmation popup)
            try:
                dialog_elements = await self.page.locator('div[role="dialog"], .artdeco-modal').all()
                visible_dialogs = []
                for d in dialog_elements:
                    if await d.is_visible():
                        visible_dialogs.append(d)
                
                if len(visible_dialogs) > 1:
                    overlay = visible_dialogs[-1]
                    log.info("🚨 Multiple dialogs detected. Handling overlay dialog...")
                    btns = await overlay.locator('button').all()
                    for b in btns:
                        if await b.is_visible() and await b.is_enabled():
                            b_text = (await b.text_content() or "").strip().lower()
                            if any(x in b_text for x in ["continue", "resume", "start new", "keep", "yes", "confirm"]):
                                log.info(f"🎯 Clicking button in overlay dialog: '{b_text}'")
                                await b.click()
                                await asyncio.sleep(1.5)
                                break
            except Exception as overlay_e:
                log.debug(f"Error handling multi-dialog overlay: {overlay_e}")

            # GLOBAL FILE CHOOSER INTERCEPTOR
            # Safely blocks OS dialogs triggered by hidden buttons
            if resume_payload and not self._resume_uploaded:
                async def _handle_chooser(file_chooser):
                    try:
                        log.info("📂 File chooser intercepted — injecting resume programmatically")
                        await file_chooser.set_files([{
                            "name": resume_payload["name"],
                            "mimeType": resume_payload["mimeType"],
                            "buffer": resume_payload["buffer"],
                        }])
                        self._resume_uploaded = True
                        log.info("✅ Resume injected via file chooser interceptor")
                        self.page.remove_listener("filechooser", _handle_chooser)
                    except Exception as e:
                        log.error(f"File chooser interception failed: {e}")
                
                # Only register if not already registered (avoid memory leak)
                if not getattr(self, '_chooser_registered', False):
                    self.page.on("filechooser", _handle_chooser)
                    self._chooser_registered = True
                    
            # Try to upload resume directly via hidden inputs
            if resume_payload and not self._resume_uploaded:
                await self._force_upload_resume(resume_payload)

            # --- PASS 1: PRE-SCAN & BATCH UNKNOWNS TO GROQ ---
            try:
                all_inputs = await self.page.locator(
                    f"{self.active_modal_sel} select, "
                    f"{self.active_modal_sel} [role='combobox'], "
                    f"{self.active_modal_sel} input[type='text'], "
                    f"{self.active_modal_sel} input[type='number'], "
                    f"{self.active_modal_sel} input[type='email'], "
                    f"{self.active_modal_sel} input[type='tel'], "
                    f"{self.active_modal_sel} input:not([type]), "
                    f"{self.active_modal_sel} textarea, "
                    f"{self.active_modal_sel} input[type='radio'], "
                    f"{self.active_modal_sel} [role='radio']"
                ).all()
                
                unknowns_to_batch = []
                for inp in all_inputs:
                    if await inp.is_visible():
                        q_text = await self._get_question_text(inp)
                        if q_text and q_text != "Unknown question":
                            if self._get_smart_answer(q_text, "text") is None:
                                cached = self.user_profile.get("cached_answers", {})
                                if q_text not in cached and q_text not in unknowns_to_batch:
                                    unknowns_to_batch.append(q_text)
                
                if unknowns_to_batch:
                    # Scout mode: Add to tracked unknowns instead of immediately deferring
                    for u in unknowns_to_batch:
                        if u not in self._scouted_unknowns:
                            self._scouted_unknowns.append(u)
                    log.info(f"🕵️ Scout Mode: Tracked {len(unknowns_to_batch)} new unknown questions. Proceeding to next step with dummy answers.")
            except Exception as e:
                if str(e).startswith("DEFER_JOB:"):
                    raise e # Re-raise to break out of modal loop
                log.debug(f"Pre-scan batching error: {e}")
            # -------------------------------------------------

            # Handle selects and comboboxes FIRST (before text inputs)
            dropdown_roots = await self.page.locator(
                f"{self.active_modal_sel} select, "
                f"{self.active_modal_sel} [role='combobox']"
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
                    smart_answer = self._get_cached_or_smart_answer(question, "select")

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
                    f"{self.active_modal_sel} input[type='text'], "
                    f"{self.active_modal_sel} textarea"
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
                f"{self.active_modal_sel} input[type='text'], "
                f"{self.active_modal_sel} input[type='number'], "
                f"{self.active_modal_sel} input[type='email'], "
                f"{self.active_modal_sel} input[type='tel'], "
                f"{self.active_modal_sel} input:not([type]), "
                f"{self.active_modal_sel} textarea"
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
                                await inp.fill("")
                                await asyncio.sleep(0.1)
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

                    # Check for validation errors early
                    error_found = False
                    if current_value:
                        try:
                            error_found = await inp.evaluate("""el => {
                                const container = el.closest('.jobs-easy-apply-form-element') || 
                                                  el.closest('.fb-dash-form-element') || 
                                                  el.closest('.artdeco-text-input--container') || 
                                                  el.parentElement.parentElement;
                                if (!container) return false;
                                return container.querySelectorAll('.artdeco-inline-feedback--error, [role="alert"], p[id*="error"]').length > 0;
                            }""")
                        except Exception:
                            pass
                            
                        # If it has a value AND no error, it's valid, so skip it!
                        if not error_found:
                            continue

                    # Other field handling
                    if typ == "email" or "email" in name:
                        await inp.fill(user["email"])
                    elif "first" in name:
                        await inp.fill(user["first"])
                    elif "middle" in name.lower() or "middle" in question.lower():
                        await inp.fill("")
                        continue
                    elif "last" in name:
                        await inp.fill(user["last"])
                    elif self._country_not_in_list and any(w in (placeholder + question.lower()) for w in ["country", "specify", "other"]):
                        continue
                    else:
                        answer = self._get_cached_or_smart_answer(question, "text")
                        
                        # Scout mode dummy answers
                        if question in self._scouted_unknowns:
                            for dummy in ["0", "1", "Yes"]:
                                await inp.fill(dummy)
                                await inp.dispatch_event("input")
                                await inp.dispatch_event("change")
                                await asyncio.sleep(0.5)
                                try:
                                    error = await inp.evaluate("""el => {
                                        const c = el.closest('.jobs-easy-apply-form-element') || 
                                                  el.closest('.fb-dash-form-element') || 
                                                  el.parentElement?.parentElement;
                                        return c ? c.querySelectorAll('.artdeco-inline-feedback--error, [role="alert"], p[id*="error"]').length > 0 : false;
                                    }""")
                                except Exception:
                                    error = False
                                if not error:
                                    break
                            continue
                            
                        original_answer = str(answer).strip() if answer is not None else ""
                        
                        # Handle null/None/empty
                        if not original_answer or original_answer.lower() == "null" or original_answer.lower() == "none":
                            val = "0"
                        else:
                            # Try parsing as float first to handle decimals like 0.8
                            try:
                                numeric = float(original_answer)
                                val = str(int(math.floor(numeric))) if numeric >= 0 else "0"
                            except ValueError:
                                # It's not a direct number. Let's see if the field is numeric or expects a number
                                input_type = (await inp.get_attribute("type") or "").lower()
                                input_mode = (await inp.get_attribute("inputmode") or "").lower()
                                is_numeric_field = (
                                    input_type == "number" or
                                    input_mode in ["numeric", "decimal"] or
                                    any(word in question.lower() for word in [
                                        "ctc", "salary", "fixed component", "experience", "years", 
                                        "notice period", "days", "months", "c fixed", "exp", "notice",
                                        "compensation", "joining", "how soon"
                                    ])
                                )
                                
                                if is_numeric_field:
                                    ans_lower = original_answer.lower()
                                    if ans_lower in ["negotiable", "immediate"]:
                                        if any(x in question.lower() for x in ["expected ctc", "expected salary", "expected fixed", "desired salary", "ectc"]):
                                            val = MY_EXPECTED_CTC
                                        else:
                                            val = "0"
                                    else:
                                        # Extract the first digits from string (e.g. "30 days" -> 30)
                                        match = re.search(r'\d+', original_answer)
                                        val = match.group(0) if match else "0"
                                else:
                                    val = original_answer
                            
                        await inp.fill(val)
                        await inp.dispatch_event("input")
                        await inp.dispatch_event("change")
                        await asyncio.sleep(0.5)
                        
                        # In-place dynamic validation retry loop
                        for _retry in range(3):
                            try:
                                error_now = await inp.evaluate("""el => {
                                    const c = el.closest('.jobs-easy-apply-form-element') || 
                                              el.closest('.fb-dash-form-element') || 
                                              el.parentElement?.parentElement;
                                    return c ? c.querySelectorAll('.artdeco-inline-feedback--error, [role="alert"], p[id*="error"]').length > 0 : false;
                                }""")
                            except Exception:
                                error_now = False
                                
                            if not error_now:
                                break
                                
                            log.warning(f"⚠️ Retry {_retry+1}: invalid value '{val}' for '{question}'")
                            
                            if _retry == 0:
                                val = "0"
                            elif _retry == 1:
                                val = "1"
                            else:
                                val = original_answer
                                
                            await inp.fill(val)
                            await inp.dispatch_event("input")
                            await inp.dispatch_event("change")
                            await asyncio.sleep(0.5)

                except Exception as e:
                    log.error(f"Text input error for '{question}': {e}")


            # Handle radio buttons
            radios = await self.page.locator(f"{self.active_modal_sel} input[type='radio']").all()
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
                        if not await r.is_visible(): continue
                        question = await self._get_question_text(r)
                        if question: break
                    else:
                        question = ""

                    if question:
                        smart_answer = self._get_cached_or_smart_answer(question, "radio").lower()
                        log.info(f"🔘 Processing radio: '{question}' - Answer: '{smart_answer}'")
                        
                        match_found = False
                        for r in group_radios:
                            value_attr = (await r.get_attribute("value") or "").lower()
                            rid = await r.get_attribute("id") or ""
                            lbl = self.page.locator(f'label[for="{rid}"]').first
                            lbl_txt = (await lbl.text_content() or "").lower() if await lbl.count() else ""

                            if smart_answer in value_attr or smart_answer in lbl_txt or (smart_answer == "yes" and "true" in value_attr):
                                if await lbl.count():
                                    await lbl.click()
                                else:
                                    await r.check()
                                log.info(f"✅ Selected radio button matching '{smart_answer}'")
                                match_found = True
                                break
                        
                        if not match_found:
                            log.warning(f"⚠️ Could not find exact match for '{smart_answer}', falling back...")
                            # Fallback if no match is found
                            fallback_success = False
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
                                    log.warning("✅ Fallback to Yes/True")
                                    fallback_success = True
                                    break
                                    
                            if not fallback_success and len(group_radios) > 0:
                                log.warning("⚠️ No Yes/True found, selecting the first option as a last resort")
                                r = group_radios[0]
                                rid = await r.get_attribute("id") or ""
                                lbl = self.page.locator(f'label[for="{rid}"]').first
                                if await lbl.count():
                                    await lbl.click()
                                else:
                                    await r.check()

                except Exception as e:
                    log.debug(f"Radio error: {e}")

            # Handle ARIA custom radio buttons (LinkedIn's new UI)
            try:
                radio_groups = await self.page.locator(f"{self.active_modal_sel} [role='radiogroup']").all()
                for group in radio_groups:
                    try:
                        aria_radios = await group.locator("[role='radio']").all()
                        if not aria_radios: continue
                        
                        question = await self._get_question_text(aria_radios[0])
                        smart_answer = self._get_cached_or_smart_answer(question, "radio").lower() if question else "yes"
                        log.info(f"🔘 Processing ARIA radio: '{question}' - Answer: '{smart_answer}'")
                        
                        match_found = False
                        for r in aria_radios:
                            txt = await r.evaluate('el => el.parentElement ? el.parentElement.textContent : el.textContent')
                            txt = (txt or "").lower()
                            value_attr = (await r.get_attribute("value") or "").lower()
                            
                            if smart_answer in value_attr or smart_answer in txt or (smart_answer == "yes" and "true" in value_attr):
                                try:
                                    await r.click(timeout=2000)
                                except:
                                    await r.evaluate('el => el.click()')
                                log.info(f"✅ Selected ARIA radio button matching '{smart_answer}'")
                                await asyncio.sleep(0.3)
                                match_found = True
                                break
                        
                        if not match_found:
                            fallback_success = False
                            for r in aria_radios:
                                txt = await r.evaluate('el => el.parentElement ? el.parentElement.textContent : el.textContent')
                                txt = (txt or "").lower()
                                value_attr = (await r.get_attribute("value") or "").lower()
                                
                                if any(x in (value_attr + txt) for x in ("yes", "true", "y", "1")):
                                    try:
                                        await r.click(timeout=2000)
                                    except:
                                        await r.evaluate('el => el.click()')
                                    log.info(f"✅ Fallback ARIA radio button (Yes/True)")
                                    await asyncio.sleep(0.3)
                                    fallback_success = True
                                    break
                                    
                            if not fallback_success and len(aria_radios) > 0:
                                log.warning("⚠️ No Yes/True found, selecting the first ARIA option as a last resort")
                                r = aria_radios[0]
                                try:
                                    await r.click(timeout=2000)
                                except:
                                    await r.evaluate('el => el.click()')
                                await asyncio.sleep(0.3)
                    except Exception as e:
                        log.debug(f"ARIA radio group error: {e}")
            except Exception as e:
                log.debug(f"ARIA radio finding error: {e}")

            # Check for save dialog before clicking buttons
            await self._handle_save_dialog()

            # Scroll modal bottom
            await self._scroll_modal_bottom()
            await asyncio.sleep(1)

            # Safe button click
            label, clicked = await safe_click_modal_button()
            
            if not clicked:
                if self._scouted_unknowns:
                    pass # removed local import
                    log.info(f"🕵️ Scout Mode: Next button not clickable or not found, but we have {len(self._scouted_unknowns)} scouted unknowns. Deferring job.")
                    raise Exception(f"DEFER_JOB:{json.dumps(self._scouted_unknowns)}")
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
        if self._scouted_unknowns:
            pass # removed local import
            log.info(f"🕵️ Scout Mode: Wizard limit reached, but we have {len(self._scouted_unknowns)} scouted unknowns. Deferring job.")
            raise Exception(f"DEFER_JOB:{json.dumps(self._scouted_unknowns)}")
        return False

    def reset_for_new_job(self):
        """Reset agent state for new job application"""
        self.collected_questions.clear()
        self._resume_uploaded = False
        self._country_not_in_list = False
        self._country_picked = False
        self._phone_filled = False
        self._location_filled = False
        self._scouted_unknowns.clear()
        self._chooser_registered = False
        self.active_modal_sel = ".artdeco-modal"
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
    try:
        log.info("🌐 Checking session login status...")
        await page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=20000)
        await asyncio.sleep(10)
    except Exception as e:
        log.warning(f"Initial feed check failed: {e}")

    if "login" not in page.url:
        log.info("✅ Already logged in")
        return True

    log.info("🔐 Logging in using provided payload credentials...")
    if not user_id or not password:
        log.error("❌ MISSING CREDENTIALS: No saved session found and no credentials provided in payload.")
        return False
        
    if "login" not in page.url:
        await page.goto(LINKEDIN_LOGIN_URL, wait_until="domcontentloaded", timeout=20000)
        await asyncio.sleep(2)
        
    await page.fill('input[type="email"]:visible', user_id)
    await page.fill('input[type="password"]:visible', password)
    await page.click('button:has-text("Sign in"):not(:has-text("Apple")):not(:has-text("Microsoft")):visible, button:has-text("Log in"):not(:has-text("Apple")):not(:has-text("Microsoft")):visible, button[type="submit"]:visible')

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
    # ── Diagnostic: verify cookies are alive before navigation ──
    try:
        ctx = page.context
        cookies = await ctx.cookies(["https://www.linkedin.com"])
        li_at = [c for c in cookies if c["name"] == "li_at"]
        jsession = [c for c in cookies if c["name"] == "JSESSIONID"]
        log.info(f"🍪 PRE-NAV cookie check: li_at={'YES' if li_at else '⚠️ MISSING'}, JSESSIONID={'YES' if jsession else '⚠️ MISSING'}, total={len(cookies)}")
        if not li_at:
            log.error("❌ li_at cookie is MISSING before navigation - session was lost!")
            raise Exception("Session connection lost (cookie missing).")
    except Exception as diag_e:
        if "session connection lost" in str(diag_e):
            raise diag_e
        log.warning(f"Cookie diagnostic failed: {diag_e}")

    for attempt in range(retries):
        try:
            log.info(f"🌐 Navigating to job page (attempt {attempt + 1})")
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)
            
            # ── Diagnostic: check if we landed on a logged-out page ──
            current_url = page.url
            if "/login" in current_url or "signup" in current_url:
                log.error(f"❌ POST-NAV: redirected to login page! URL={current_url}")
                raise Exception("Session connection lost (redirected to login).")
            
            return True
        except Exception as e:
            if "session connection lost" in str(e):
                raise e
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
    user_profile: dict = None,
    pw = None,
    browser = None,
    context = None,
    page = None
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
            if not RESUME_FILENAME.lower().endswith(".pdf"):
                RESUME_FILENAME += ".pdf"

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

    if not browser:
        if log_callback:
            log_callback({"progress": 6, "status": "processing", "message": "Connecting to server..."})
        pw = await async_playwright().start()
        launch_kwargs = {
            "headless": True,
            
            "args": [
                '--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu', '--no-zygote', '--disable-extensions', '--disable-background-networking', '--disable-renderer-backgrounding', '--no-first-run', '--mute-audio', '--metrics-recording-only'
            ]
        }
        
        browser = await pw.chromium.launch(**launch_kwargs)
        
        db_context = None
        if not progress_user:
            raise Exception("Progress user not found")
        db_context = get_linkedin_context(progress_user)
        
        if db_context:
            print(f"FOUND STORAGE STATE IN DB!")
            print(f"Creating new context with current browser using saved state!")
            
            context = await browser.new_context(
                storage_state=db_context,
                **LINKEDIN_CONTEXT_OPTIONS
            )
        else:
            context = await browser.new_context(**LINKEDIN_CONTEXT_OPTIONS)
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)

        if not await login(page, user_id, password):
            raise Exception("Session login failed or credentials missing.")

    try:
        if log_callback:
            log_callback({"progress": 8, "status": "processing", "message": "Server connected"})

        # ── Diagnostic: baseline cookie check after login ──
        try:
            baseline_cookies = await context.cookies(["https://www.linkedin.com"])
            li_at_baseline = [c for c in baseline_cookies if c["name"] == "li_at"]
            log.info(f"🍪 BASELINE after login: li_at={'YES' if li_at_baseline else '⚠️ MISSING'}, total={len(baseline_cookies)}, page_url={page.url}")
        except Exception as diag_e:
            log.warning(f"Baseline cookie diagnostic failed: {diag_e}")

        try:
            state = await context.storage_state()
            save_linkedin_context(progress_user, dict(state))
        except Exception as e:
            log.warning(f"Could not persist session storage state: {e}")

        agent = EasyApplyAgent(page, user_id=progress_user, user_profile=user_profile)
        applied = []
        failed = []

        # ── Helper: emit progress after each job outcome ──────────────
        def emit(success: bool, current_url: str | None, company_name: str | None, reason: str ="", is_already_applied: bool = False):
            jobs_applied_counter[0] += 1
            progress = min(int((jobs_applied_counter[0] / total_jobs) * 89) + 11, 99)

            company = normalize_company_name(company_name)

            # Verbose console log for debugging
            if is_already_applied:
                print(f"[apply] ✅ Already Applied ({jobs_applied_counter[0]}/{total_jobs}) - {company}")
            elif success:
                print(f"[apply] 📎 Applied ({jobs_applied_counter[0]}/{total_jobs}) - {company}")
            else:
                reason_part = f": {reason}" if reason else ""
                print(f"[apply] ❌ Skipped ({jobs_applied_counter[0]}/{total_jobs}) - {company}{reason_part}")

            # User-friendly Redis stream message
            if log_callback:
                if is_already_applied:
                    msg = f"Already Applied {jobs_applied_counter[0]}/{total_jobs} - {company}"
                    status = "already applied"
                elif success:
                    msg = f"Applied {jobs_applied_counter[0]}/{total_jobs} - {company}"
                    status = "applied"
                else:
                    reason_part = f": {reason}" if reason else ""
                    msg = f"Skipped {jobs_applied_counter[0]}/{total_jobs} - {company}{reason_part}"
                    status = "skipped"
                
                log_callback({
                    "progress": progress,
                    "status":   status,
                    "message":  msg,
                    "job_url":  current_url,
                    "job_company": company,
                    "success":  success,
                })

        # ── Per-job apply loop & Rolling API Architecture ───────────────────
        deferred_jobs = []
        retry_queue = asyncio.Queue()
        questions_buffer = []
        questions_buffer_lock = asyncio.Lock()
        api_tasks = []
        job_tracker = {} # url -> list of questions

        async def flush_questions_buffer(force=False):
            async with questions_buffer_lock:
                if len(questions_buffer) >= 15 or (force and len(questions_buffer) > 0):
                    batch_q = list(questions_buffer)
                    questions_buffer.clear()
                    if not batch_q: return
                    
                    async def _call_groq_and_push(questions_chunk):
                        # log_callback removed as requested by user to keep UI clean
                        await agent._ask_groq_batch(questions_chunk)
                        
                        # Find jobs that are now ready and push to retry_queue
                        for d_job in list(deferred_jobs):
                            d_url = d_job.get("job_url")
                            if d_url in job_tracker:
                                q_list = job_tracker[d_url]
                                cached = agent.user_profile.get("cached_answers", {})
                                if all(q in cached for q in q_list):
                                    await retry_queue.put(d_job)
                                    deferred_jobs.remove(d_job)
                                    del job_tracker[d_url]
                    
                    api_tasks.append(asyncio.create_task(_call_groq_and_push(batch_q)))

        async def process_job(job, idx, is_retry=False):
            url, b64 = job.get("job_url"), job.get("resume_binary")
            company_name = job.get("company_name")
            if not url or not b64:
                log.warning(f"Job {idx}: missing data - skipped")
                emit(False, url, company_name, "incomplete job data") 
                return

            log.info(f"\n{'='*60}")
            log.info(f"📍 Processing Job {idx} {'(RETRY)' if is_retry else ''}")
            log.info(f"🔗 URL: {url}")
            log.info(f"{'='*60}")
            
            if not await safe_goto(page, url):
                failed.append(url)
                emit(False, url, company_name, "page unavailable") 
                return
            
            payload = make_resume_payload(b64)
            agent.reset_for_new_job()

            try:
                if not await agent.find_and_click_easy_apply():
                    log.warning("No Easy Apply button found - skipping")
                    failed.append(url)
                    emit(False, url, company_name, "direct apply only")
                    return
            except Exception as e:
                if str(e) == "NO_LONGER_ACCEPTING":
                    log.warning("Job is no longer accepting applications - skipping")
                    failed.append(url)
                    emit(False, url, company_name, "not accepting applications")
                    return
                elif str(e) == "ALREADY_APPLIED":
                    log.info("Job already applied - marking as success/applied")
                    applied.append(url)
                    emit(True, url, company_name, is_already_applied=True)
                    return
                raise e

            try:
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
            except Exception as e:
                if str(e).startswith("DEFER_JOB:"):
                    # We hit an unknown question
                    unknowns = json.loads(str(e).replace("DEFER_JOB:", ""))
                    log.info(f"⏳ Deferring Job {idx} due to {len(unknowns)} unknown questions.")
                    
                    # Track this job
                    deferred_jobs.append(job)
                    job_tracker[url] = unknowns
                    
                    # Add to buffer and flush if needed
                    async with questions_buffer_lock:
                        for uq in unknowns:
                            if uq not in questions_buffer:
                                questions_buffer.append(uq)
                    await flush_questions_buffer(force=False)
                    return
                else:
                    # Check if we have scouted unknowns
                    if getattr(agent, '_scouted_unknowns', []):
                        pass # removed local import
                        unknowns = list(agent._scouted_unknowns)
                        log.info(f"⏳ Deferring Job {idx} due to {len(unknowns)} scouted unknowns after modal error: {e}")
                        
                        # Track this job
                        deferred_jobs.append(job)
                        job_tracker[url] = unknowns
                        
                        # Add to buffer and flush if needed
                        async with questions_buffer_lock:
                            for uq in unknowns:
                                if uq not in questions_buffer:
                                    questions_buffer.append(uq)
                        await flush_questions_buffer(force=False)
                        return
                    failed.append(url)
                    log.error(f"❌ Job {idx} modal error: {e}")
                    emit(False, url, company_name)
            
            await asyncio.sleep(3)

        # ── Pass 1: Initial Processing ───────────────────────────────────────
        idx_counter = 0
        while True:
            batch = await jobs_queue.get()
            if batch is None:
                break
            
            for job in batch:
                idx_counter += 1
                await process_job(job, idx_counter)

        # ── Pass 2: Retry Deferred Jobs (Parallel Pipeline) ───────────────────
        if deferred_jobs or questions_buffer:
            await flush_questions_buffer(force=True)
            if deferred_jobs and log_callback:
                log_callback({"progress": 60, "status": "retrying", "message": f"Retrying {len(deferred_jobs)} deferred jobs with AI answers..."})
                
            # Process as they come into retry_queue, OR if API tasks finish, flush remainder
            while True:
                try:
                    d_job = retry_queue.get_nowait()
                    idx_counter += 1
                    await process_job(d_job, idx_counter, is_retry=True)
                except asyncio.QueueEmpty:
                    # check if api_tasks are done
                    if all(t.done() for t in api_tasks):
                        # Force process remaining deferred_jobs
                        for d_job in list(deferred_jobs):
                            idx_counter += 1
                            await process_job(d_job, idx_counter, is_retry=True)
                            deferred_jobs.remove(d_job)
                        break
                    await asyncio.sleep(1)

        # ── Batch summary log ─────────────────────────────────────────────

        log.info(f"\n{'='*60}")
        log.info(f"🎯 FINAL RESULTS:")
        log.info(f"✅ Successfully applied: {len(applied)}")
        log.info(f"❌ Failed applications: {len(failed)}")
        log.info(f"📊 Success rate: {(len(applied)/(len(applied)+len(failed))*100):.1f}%")
        log.info(f"{'='*60}")

        # ── Delayed DB Write ─────────────────────────────────────────────
        if user_id and agent.user_profile:
            from config import supabase
            try:
                # Use email for update as per instructions
                user_email = agent.user_profile.get("email", "")
                if user_email:
                    supabase.table("User").update({"user_data": agent.user_profile}).eq("email", user_email).execute()
                    log.info("💾 Saved all new AI answers to Supabase permanent cache")
            except Exception as db_e:
                log.error(f"Failed to update Supabase cache: {db_e}")

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

async def setup_and_login(progress_user, user_id, password, log_callback=None):
    if log_callback:
        log_callback({"progress": 6, "status": "processing", "message": "Connecting to server..."})
    pw = await async_playwright().start()
    launch_kwargs = {
        "headless": True,
        "args": [
            '--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu', '--no-zygote', '--disable-extensions', '--disable-background-networking', '--disable-renderer-backgrounding', '--no-first-run', '--mute-audio', '--metrics-recording-only'
        ]
    }
    browser = await pw.chromium.launch(**launch_kwargs)
    try:
        db_context = get_linkedin_context(progress_user)
        if db_context:
            print(f"FOUND STORAGE STATE IN DB!")
            print(f"Creating new context with current browser using saved state!")
            context = await browser.new_context(
                storage_state=db_context,
                **LINKEDIN_CONTEXT_OPTIONS
            )
        else:
            context = await browser.new_context(**LINKEDIN_CONTEXT_OPTIONS)
        
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        if not await login(page, user_id, password):
            raise Exception("Session login failed or credentials missing.")
            
        return pw, browser, context, page
    except Exception as e:
        try:
            await browser.close()
            await pw.stop()
        except:
            pass
        raise e

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
    pass # removed local import

    user_id = job_data["user_id"]
    input_data = job_data.get("input_data", {})
    output_data = job_data.get("output_data") or {}

    email = input_data.get("user_id") # email is passed
    resume_url = input_data.get("resume_url")
    jobs_to_apply = input_data.get("jobs", [])

    # Extract credentials from payload
    l_email = input_data.get("linkedin_id")
    l_pass = input_data.get("linkedin_password")

    # Pre-check credentials early to fail fast and save Gemini calls
    db_context = get_linkedin_context(email)
    if not db_context and (not l_email or not l_pass):
        raise Exception("MISSING CREDENTIALS: No saved session found and no credentials provided in payload.")

    if not jobs_to_apply:
        raise Exception("No jobs provided to apply to")

    log_callback({"progress": 2, "status": "in_progress", "message": "Initializing auto-applier pipeline..."})

    total_jobs = len(jobs_to_apply)

    # Fetch pre-parsed user profile + prior apply history for resume-aware idempotency.
    user_res = supabase.table("User").select("user_data, applied_jobs").eq("email", email).execute()
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

    # Safety-net: guarantee applied + failed == total_jobs. Any selected job that never
    # produces an applied/skipped event — one filtered out as already-applied, or dropped
    # by a producer-level abort — is recorded as failed here so no job silently vanishes.
    def reconcile_unaccounted(reason: str = "not processed"):
        accounted = set(applied_so_far) | set(failed_so_far)
        for j in jobs_to_apply:
            ju = j.get("job_url")
            if not ju or ju in accounted:
                continue
            accounted.add(ju)
            company = normalize_company_name(j.get("company_name"))
            if ju in history_applied:
                # Applied in a prior run — count it as applied (truthful), not failed,
                # so the success metric isn't penalised for a job that did succeed.
                applied_so_far.append(ju)
                log_callback({
                    "progress": 99, "status": "applied", "success": True,
                    "message": f"Applied (already applied) - {company}",
                    "job_url": ju, "job_company": company,
                })
            else:
                # Genuinely never processed — failed.
                failed_so_far.append(ju)
                log_callback({
                    "progress": 99, "status": "skipped", "success": False,
                    "message": f"Skipped ({reason}) - {company}",
                    "job_url": ju, "job_company": company,
                })

    # Everything already processed — finalize without launching the browser.
    if not remaining:
        reconcile_unaccounted()
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

    already_applied_count = total_jobs - len(remaining)
    if already_applied_count > 0:
        log_callback({"progress": 5, "status": "in_progress", "message": f"{already_applied_count} out of {total_jobs} jobs were already applied. Proceeding with remaining {len(remaining)} jobs..."})
    else:
        log_callback({"progress": 5, "status": "in_progress", "message": f"Applying to all {total_jobs} jobs..."})

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
                supabase.table("User").update({"applied_jobs": merged}).eq("email", email).execute()
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
                # Isolate each batch: a single tailoring failure must NOT abandon the
                # remaining batches. On failure, enqueue the jobs with no resume_binary
                # so the consumer still emits a 'skipped' event and they stay counted.
                try:
                    tailored_batch = await asyncio.to_thread(process_batch, resume_url, batch_jobs, user_data_str, 0, facts) # template=0 explicitly
                except Exception as be:
                    print(f"[tailor] Batch {(i//batch_size)+1} failed ({be}); enqueueing as skipped")
                    tailored_batch = [
                        {"job_url": j.get("job_url"), "resume_binary": "", "company_name": j.get("company_name")}
                        for j in batch_jobs
                    ]
                await jobs_queue.put(tailored_batch)
            # Send poison pill to signal queue exhaustion
            await jobs_queue.put(None)
        except Exception as e:
            print(f"Producer thread died: {e}")
            await jobs_queue.put(None)

    pw_instance = None
    browser_instance = None

    try:
        # Phase 1: Setup browser and verify login to fail fast and save Gemini calls
        pw_check, browser_check, context_check, page_check = await setup_and_login(email, l_email, l_pass, log_callback)
        # Close check browser completely to save resources during tailoring
        try:
            await browser_check.close()
            await pw_check.stop()
        except:
            pass

        # Phase 2: Launch Producer (tailoring task) in background
        producer_task = asyncio.create_task(tailor_producer())

        # Wait until the producer pushes the first batch before launching the browser
        # This eliminates the idle time where the browser sits open waiting for Gemini
        while jobs_queue.empty() and not producer_task.done():
            await asyncio.sleep(1)

        # Once tailoring completes/starts producing batches, we relaunch Playwright for application
        pw_instance, browser_instance, context_instance, page_instance = await setup_and_login(email, l_email, l_pass, log_callback)

        try:
            # Phase 3: Consumer (Playwright Application Loop)
            await main(
                jobs_queue=jobs_queue,
                user_id=l_email,
                password=l_pass,
                progress_user=email,
                resume_url=resume_url,
                log_callback=checkpoint_callback,
                total_jobs=total_jobs,
                jobs_applied_counter=[total_jobs - len(remaining)],
                user_profile=user_profile,
                pw=pw_instance,
                browser=browser_instance,
                context=context_instance,
                page=page_instance
            )
        finally:
            if not producer_task.done():
                producer_task.cancel()
                try:
                    await producer_task
                except asyncio.CancelledError:
                    pass
            # Cleanup main browser instance
            try:
                await browser_instance.close()
                await pw_instance.stop()
            except:
                pass

        # Reconcile any remaining unaccounted jobs on normal completion
        reconcile_unaccounted("not processed")

        # Build final success metrics
        total_done = len(applied_so_far) + len(failed_so_far)
        result = {
            "applied": applied_so_far,
            "failed": failed_so_far,
            "total_jobs": total_jobs,
            "success_rate": round(len(applied_so_far) / total_done * 100, 2) if total_done > 0 else 0,
        }
        log_callback({"progress": 100, "status": "done", "message": f"Workflow Complete! Applied: {len(applied_so_far)}, Failed: {len(failed_so_far)}"})

        # Update DB to completed status
        supabase.table("workflow_sessions").update({
            "status": "completed",
            "output_data": result
        }).eq("id", job_id).execute()

    except Exception as run_error:
        log.error(f"❌ Autoplay Pipeline Failed: {run_error}")
        
        # Cleanup any dangling browser processes
        try:
            if browser_instance:
                await browser_instance.close()
            if pw_instance:
                await pw_instance.stop()
        except:
            pass

        # Clear the LinkedIn session from PostgreSQL ONLY since it is invalid/expired (session lost or login failed)
        if any(x in str(run_error).lower() for x in ["session connection lost", "login failed", "credentials missing", "unauthorized"]):
            try:
                clear_linkedin_context(email)
                log.info(f"🧹 Successfully cleared invalid LinkedIn session for {email}")
            except Exception as clear_err:
                print(f"Failed to clear linkedin context: {clear_err}")
        else:
            log.info("⚠️ Error is not session-related. Keeping LinkedIn session context intact.")

        # Reconcile all remaining jobs as failed due to connection loss
        reconcile_unaccounted("connection lost")

        # Build final partial results
        total_done = len(applied_so_far) + len(failed_so_far)
        result = {
            "applied": applied_so_far,
            "failed": failed_so_far,
            "total_jobs": total_jobs,
            "success_rate": round(len(applied_so_far) / total_done * 100, 2) if total_done > 0 else 0,
        }
        log_callback({"progress": 100, "status": "failed", "message": f"Pipeline Aborted! Connection Lost. Applied: {len(applied_so_far)}, Failed: {len(failed_so_far)}"})

        # Update DB to failed status with the partial data
        supabase.table("workflow_sessions").update({
            "status": "failed",
            "output_data": result
        }).eq("id", job_id).execute()

        # Re-raise error to bubble up
        raise run_error
