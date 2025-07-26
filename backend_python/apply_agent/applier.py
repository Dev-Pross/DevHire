import asyncio
import logging
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger("EasyApply")
logging.basicConfig(level=logging.INFO)

class EasyApplyAgent:
    def __init__(self, page: Page):
        self.page = page

    async def find_and_click_easy_apply(self) -> bool:
        try:
            logger.info("Searching for all buttons containing 'Apply'...")
            buttons = await self.page.locator('button:has-text("Apply")').all()
            logger.info(f"Found {len(buttons)} candidate buttons.")
            for idx, btn in enumerate(buttons):
                try:
                    text = (await btn.text_content()) or ""
                    visible, enabled = await btn.is_visible(), await btn.is_enabled()
                    logger.info(f"Button {idx+1}: '{text.strip()}', Visible: {visible}, Enabled: {enabled}")
                    if "Easy Apply" in text and visible and enabled:
                        logger.info(f"Clicking button {idx+1}")
                        await btn.scroll_into_view_if_needed()
                        await self.page.wait_for_timeout(500)
                        try:
                            await btn.click()
                        except Exception:
                            await self.page.evaluate("(el) => el.click()", btn)
                        try:
                            await self.page.wait_for_selector('.jobs-easy-apply-modal', timeout=10000)
                            logger.info("Easy Apply modal appeared!")
                            return True
                        except PlaywrightTimeoutError:
                            logger.error("Modal did not appear after click.")
                            continue
                except Exception as e:
                    logger.error(f"Error with button {idx+1}: {e}")
            logger.error("Could not find or click the Easy Apply button.")
            return False
        except Exception as exc:
            logger.error(f"Exception during Easy Apply button search: {exc}")
            return False

    async def scroll_modal_to_bottom(self):
        await self.page.evaluate('''
            () => {
                const modal = document.querySelector('.jobs-easy-apply-modal');
                if (!modal) return;
                let scrollable = null;
                for (const elem of modal.querySelectorAll('div, form')) {
                    if (elem.scrollHeight > elem.clientHeight + 10) {
                        scrollable = elem;
                        break;
                    }
                }
                if (scrollable) {
                    scrollable.scrollTop = scrollable.scrollHeight;
                } else {
                    modal.scrollTop = modal.scrollHeight;
                }
            }
        ''')
        await asyncio.sleep(0.4)

    async def fill_and_submit_modal(self, user_info=None) -> bool:
        user_info = user_info or {
            "phone": "9999999999",
            "email": "example@example.com",
            "first_name": "First",
            "last_name": "Last"
        }

        for step in range(8):
            # Fill required inputs
            required_inputs = await self.page.locator('input[aria-required="true"]').all()
            for inp in required_inputs:
                val = await inp.input_value() or ""
                if val.strip():
                    continue
                typ = await inp.get_attribute("type") or ""
                name = await inp.get_attribute("name") or ""
                if typ == "tel":
                    await inp.fill(user_info.get("phone", "9999999999"))
                elif typ == "email" or "email" in name.lower():
                    await inp.fill(user_info.get("email", "example@example.com"))
                elif "first" in name.lower():
                    await inp.fill(user_info.get("first_name", "First"))
                elif "last" in name.lower():
                    await inp.fill(user_info.get("last_name", "Last"))
                else:
                    await inp.fill("N/A")

            # Fill selects
            select_fields = await self.page.locator('select[aria-required="true"]').all()
            for sel in select_fields:
                options = await sel.locator('option').all()
                if options and len(options) > 1:
                    val = await options[1].get_attribute("value")
                    await sel.select_option(value=val)

            # Fill radios
            radios = await self.page.locator('input[type="radio"][aria-required="true"]').all()
            for radio in radios:
                await radio.check()

            await self.scroll_modal_to_bottom()
            await asyncio.sleep(0.7)

            # Look for action buttons **only inside modal**, matching your provided class
            button_selector = (
                '.jobs-easy-apply-modal button.artdeco-button.artdeco-button--2.artdeco-button--primary.ember-view:not([disabled])'
            )

            # Get all candidates and try to pick the first enabled/visible
            btns = await self.page.locator(button_selector).all()
            next_btn = None
            for btn in btns:
                if await btn.is_visible():
                    next_btn = btn
                    break

            if next_btn:
                text = (await next_btn.text_content() or "").lower()
                logger.info(f"Clicking modal action button: '{text}' at step {step+1}")
                await next_btn.click()
                await asyncio.sleep(1.2)
                # Stop if it's the final step
                if "submit" in text or "done" in text or "finished" in text:
                    logger.info("Successfully submitted application.")
                    await self.close_modal()
                    return True
                # Otherwise, continue to next step
            else:
                logger.warning("No active modal action button found, stopping.")
                await self.handle_save_popup()  # in case LinkedIn pops save/discard
                await self.close_modal()
                return False

            await self.handle_save_popup()

        logger.error("Failed to complete application flow.")
        await self.close_modal()
        return False

    async def handle_save_popup(self):
        save_popup = self.page.locator('text="Save this application?"')
        if await save_popup.is_visible():
            discard = self.page.locator('button:has-text("Discard")')
            if await discard.is_visible():
                await discard.click()
                await asyncio.sleep(0.3)
                logger.info("Dismissed 'Save this application?' popup.")

    async def close_modal(self):
        try:
            buttons = await self.page.locator(
                '.jobs-easy-apply-modal [aria-label="Dismiss"], .jobs-easy-apply-modal button[aria-label="Close"]'
            ).all()
            for btn in buttons:
                if await btn.is_visible():
                    await btn.click()
                    await asyncio.sleep(0.5)
                    logger.info("Dismissed modal.")
                    break
        except Exception:
            pass
