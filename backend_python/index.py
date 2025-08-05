#!/usr/bin/env python3
"""
LinkedIn Easy-Apply AUTO-APPLIER - ENHANCED VERSION
──────────────────────────────────────────────────
• Added city/country/location handling
• Fixed resume upload issue
• Added known technologies database
• Improved Easy Apply button detection
"""

import asyncio, json, logging, base64, mimetypes, re
from pathlib import Path
from playwright.async_api import (
    async_playwright,
    Page,
    TimeoutError as PlaywrightTimeoutError,
)
from playwright_stealth.stealth import Stealth
from config import LINKEDIN_ID, LINKEDIN_PASSWORD

# ────────────────────────── CONSTANTS ──────────────────────────
LINKEDIN_LOGIN_URL = "https://www.linkedin.com/login"
RESUME_FILENAME = "SRINIVAS_SAI_SARAN_TEJA.pdf"
RESUME_MIMETYPE = mimetypes.guess_type(RESUME_FILENAME)[0] or "application/pdf"
SHORT_TO = 8_000

# Profile settings
MY_GENERAL_EXPERIENCE = "1"
MY_KNOWN_TECH_EXPERIENCE = "0.6"
MY_UNKNOWN_TECH_EXPERIENCE = "0"
MY_CURRENT_CTC = "0"
MY_EXPECTED_CTC = "600000"  # 6 LPA for better opportunities
MY_NOTICE_PERIOD = "0"

# Personal location details - UPDATE THESE WITH YOUR INFO
MY_CURRENT_CITY = "Visakhapatnam, Andhra Pradesh"
MY_CURRENT_STATE = "Andhra Pradesh"
MY_CURRENT_COUNTRY = "India"
MY_FULL_LOCATION = f"{MY_CURRENT_CITY}, {MY_CURRENT_COUNTRY}"

# Known technologies database
KNOWN_TECHNOLOGIES = {
    # Programming Languages
    "java", "python", "javascript", "js", "c",
    # Web Technologies (MERN Stack)
    "mongodb", "mongo", "express", "expressjs", "react", "reactjs",
    "node", "nodejs", "html", "css", "bootstrap", "json", "xml",
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
}

# ─────────────────────────── LOGGING ───────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("EasyApply")

# ╭─────────────────── EasyApplyAgent ───────────────────╮
class EasyApplyAgent:
    NEXT_BTN_SEL = (
        ".jobs-easy-apply-modal "
        "button.artdeco-button--2.artdeco-button--primary.ember-view:not([disabled])"
    )
    PRIMARY_BTN_SEL = (
        ".jobs-easy-apply-modal button.artdeco-button--primary:not([disabled])"
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
            'button[aria-label*="Easy Apply"]',
            'button:has-text("Easy Apply")',
            '.jobs-apply-button--top-card button:has-text("Apply")',
            '.jobs-s-apply button:has-text("Apply")',
            '.jobs-apply-button button:has-text("Easy Apply")',
            'button[data-control-name="apply"]',
            '.jobs-apply-button button[aria-label*="Apply"]',
            'button:has-text("Apply"):has-text("Easy")',
            'button:has-text("Apply")',
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
                            await self.page.wait_for_timeout(500)

                            try:
                                await btn.click()
                            except Exception:
                                await self.page.evaluate("(b)=>b.click()", btn)

                            for attempt in range(3):
                                try:
                                    await self.page.wait_for_selector(
                                        ".jobs-easy-apply-modal", timeout=5000
                                    )
                                    log.info("🪟 Easy-Apply modal opened successfully")
                                    return True
                                except PlaywrightTimeoutError:
                                    if attempt < 2:
                                        log.warning(f"Modal not found, retry {attempt + 1}")
                                        await asyncio.sleep(1)
                                    else:
                                        log.warning("Modal did not appear after 3 attempts")

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
                const modal = document.querySelector('.jobs-easy-apply-modal');
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
            for char in city_only:
                await input_element.type(char, delay=100)
            
            await asyncio.sleep(1.5)

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
                await self.page.click(".jobs-easy-apply-modal", timeout=1000)
            except:
                # Fallback: click on body
                await self.page.click("body", timeout=1000)
            
            await asyncio.sleep(0.5)
            
        except Exception as e:
            log.debug(f"Error dismissing overlays: {e}")

# ───────────────────────────────────────────────────────
    async def _force_upload_resume(self, payload: dict):
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
                    await fi.set_input_files(payload, timeout=3000, force=True)
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
                return MY_KNOWN_TECH_EXPERIENCE

        log.info("❌ Unknown technology in question")
        return MY_UNKNOWN_TECH_EXPERIENCE

    # ───────────────────────────────────────────────────────
    def _get_smart_answer(self, question_text: str, field_type: str = "text") -> str:
        """Smart answering with technology-specific experience and location handling"""
        q = question_text.lower()

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
                return MY_GENERAL_EXPERIENCE
            else:
                return tech_experience

        # Salary related questions
        if any(word in q for word in [
            "salary", "ctc", "current ctc", "expected ctc", "compensation",
            "package", "current salary", "expected salary", "pay", "wage",
            "expectations", "expectation"
        ]):
            if any(word in q for word in ["current", "present", "existing"]):
                return MY_CURRENT_CTC
            elif any(word in q for word in ["expected", "expect", "desired", "target"]):
                return MY_EXPECTED_CTC
            return MY_CURRENT_CTC

        # Notice period
        if any(word in q for word in [
            "notice", "notice period", "joining", "available", "availability",
            "when can you join", "start date", "how soon"
        ]):
            return MY_NOTICE_PERIOD

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
    resume_payload: dict | None,
    max_steps: int = 15,
    ) -> bool:

        async def safe_click_modal_button():
            """Safely click Next/Submit buttons within modal only"""
            button_selectors = [
                ".jobs-easy-apply-modal button:has-text('Next'):not([disabled])",
                ".jobs-easy-apply-modal button:has-text('Submit'):not([disabled])",
                ".jobs-easy-apply-modal button:has-text('Continue'):not([disabled])",
                self.NEXT_BTN_SEL,
                self.PRIMARY_BTN_SEL
            ]
            
            for selector in button_selectors:
                try:
                    btn = self.page.locator(selector).first
                    if await btn.is_visible() and await btn.is_enabled():
                        await btn.scroll_into_view_if_needed()
                        await asyncio.sleep(0.5)
                        
                        label = (await btn.text_content() or "").strip().lower()
                        log.info(f"➡️ Clicking: '{label}'")
                        
                        try:
                            await btn.click(timeout=5000)
                        except:
                            await btn.evaluate("el => el.click()")
                        
                        await asyncio.sleep(2)
                        return label, True
                except:
                    continue
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
                ".jobs-easy-apply-modal select, "
                ".jobs-easy-apply-modal [role='combobox']"
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

                    log.info(f"🔽 Processing dropdown: '{question[:50]}...' - Answer: '{smart_answer}'")

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
                    ".jobs-easy-apply-modal input[type='text'], "
                    ".jobs-easy-apply-modal textarea"
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
                ".jobs-easy-apply-modal input[type='text'], "
                ".jobs-easy-apply-modal input[type='number'], "
                ".jobs-easy-apply-modal input[type='email'], "
                ".jobs-easy-apply-modal input[type='tel'], "
                ".jobs-easy-apply-modal input:not([type]), "
                ".jobs-easy-apply-modal textarea"
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

                except Exception as e:
                    log.debug(f"Text input error: {e}")

            # Handle radio buttons
            radios = await self.page.locator(".jobs-easy-apply-modal input[type='radio']").all()
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

            if any(k in label for k in ("submit", "finish", "done")):
                log.info("🎉 Application submitted successfully!")
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
def make_resume_payload(b64: str) -> dict:
    return {
        "name": RESUME_FILENAME,
        "mimeType": RESUME_MIMETYPE,
        "buffer": base64.b64decode(b64),
    }

async def login(page: Page) -> bool:
    await page.goto(LINKEDIN_LOGIN_URL, wait_until="networkidle")
    if "/feed" in page.url:
        log.info("✅ Already logged in")
        return True

    log.info("🔐 Logging in...")
    await page.fill("#username", LINKEDIN_ID)
    await page.fill("#password", LINKEDIN_PASSWORD)
    await page.click('button[type="submit"]')

    for _ in range(30):
        await asyncio.sleep(1)
        if "/feed" in page.url:
            log.info("✅ Login successful")
            return True
        if any(x in page.url for x in ("/captcha", "/challenge", "/checkpoint")):
            log.error("❌ Login challenge encountered")
            return False

    log.error("❌ Login timeout")
    return False

async def safe_goto(page: Page, url: str, retries: int = 3) -> bool:
    for attempt in range(retries):
        try:
            log.info(f"🌐 Navigating to job page (attempt {attempt + 1})")
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await asyncio.sleep(2)
            return True
        except Exception as e:
            log.warning(f"Navigation attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                await asyncio.sleep(3)

    log.error(f"❌ Failed to navigate to {url}")
    return False

# ─────────────────────────── MAIN ──────────────────────────
async def main():
    with open("tailored_resumes_batch_kv.json", encoding="utf-8") as f:
        raw = json.load(f)

    jobs = (
        [raw]
        if isinstance(raw, dict) and "job_url" in raw
        else list(raw.values()) if isinstance(raw, dict) else raw
    )
    log.info(f"📋 Loaded {len(jobs)} job(s) to process")

    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=False)
    context = await browser.new_context()
    page = await context.new_page()
    await Stealth().apply_stealth_async(page)

    try:
        if not await login(page):
            return

        agent = EasyApplyAgent(page)
        applied = 0
        failed = 0

        for idx, job in enumerate(jobs, 1):
            url, b64 = job.get("job_url"), job.get("resume_binary")
            if not url or not b64:
                log.warning(f"⚠️ Job {idx}: missing data - skipped")
                continue

            log.info(f"\n{'='*60}")
            log.info(f"📍 Processing Job {idx}/{len(jobs)}")
            log.info(f"🔗 URL: {url}")
            log.info(f"{'='*60}")

            if not await safe_goto(page, url):
                failed += 1
                continue

            payload = make_resume_payload(b64)
            agent.reset_for_new_job()

            if not await agent.find_and_click_easy_apply():
                log.warning("❌ No Easy Apply button found - skipping")
                failed += 1
                continue

            success = await agent.fill_and_submit_modal(
                user={
                    "first": "SRINIVAS",
                    "last": "SAI SARAN TEJA",
                    "email": "example@example.com",
                    "phone": "7993027519",
                },
                resume_payload=payload,
            )

            if success:
                applied += 1
                log.info(f"✅ Job {idx} applied successfully! Total: {applied}")
            else:
                failed += 1
                log.warning(f"❌ Job {idx} application failed")

            # Show questions captured
            if agent.collected_questions:
                print(f"\n📝 Questions captured for Job {idx}:")
                for q in agent.collected_questions[-5:]:
                    print(f"  • [{q['type']}] {q['text'][:80]}...")

            await asyncio.sleep(3)

        log.info(f"\n{'='*60}")
        log.info(f"🎯 FINAL RESULTS:")
        log.info(f"✅ Successfully applied: {applied}")
        log.info(f"❌ Failed applications: {failed}")
        log.info(f"📊 Success rate: {(applied/(applied+failed)*100):.1f}%")
        log.info(f"{'='*60}")

    finally:
        await context.close()
        await browser.close()
        await pw.stop()

if __name__ == "__main__":
    asyncio.run(main())
