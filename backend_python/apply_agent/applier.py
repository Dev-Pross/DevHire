from loguru import logger
import asyncio

class Applier:
    def __init__(self, navigator):
        self.navigator = navigator

    async def is_application_open(self, page):
        # Check for "No longer accepting applications"
        try:
            closed = await page.locator("text=No longer accepting applications").is_visible()
            if closed:
                logger.warning("Job is closed for applications.")
                return False
            return True
        except Exception as e:
            logger.warning(f"Could not check application status: {e}")
            return True  # Default to try

    async def easy_apply(self, page):
        try:
            await asyncio.sleep(2)
            buttons = await page.locator('button:has-text("Apply")').all()
            logger.info(f"Found {len(buttons)} 'Apply' buttons")
            for btn in buttons:
                try:
                    text = await btn.text_content() or ""
                    if "Easy Apply" in text and await btn.is_visible() and await btn.is_enabled():
                        await btn.scroll_into_view_if_needed()
                        await asyncio.sleep(1)
                        # Simulate mouse movement
                        await page.mouse.move(400, 400)
                        await asyncio.sleep(0.5)
                        await btn.hover()
                        await asyncio.sleep(0.5)
                        await btn.click()
                        logger.info("Clicked Easy Apply!")
                        # Wait for modal/dialog or spinner
                        spinner = page.locator('.artdeco-spinner')
                        try:
                            await page.wait_for_selector('.jobs-easy-apply-modal,.artdeco-spinner', timeout=10000)
                            # If spinner persists for more than 8 seconds, treat as failure
                            if await spinner.is_visible():
                                logger.warning("Spinner detected, waiting up to 8s for it to disappear...")
                                try:
                                    await spinner.wait_for(state='detached', timeout=8000)
                                except Exception:
                                    logger.error("Spinner did not disappear, likely blocked or session failure.")
                                    await page.screenshot(path="spinner_timeout.png")
                                    return False
                            modal = page.locator('.jobs-easy-apply-modal')
                            if await modal.is_visible():
                                logger.info("Easy Apply modal appeared!")
                                return True
                            else:
                                logger.error("Easy Apply modal did not appear.")
                                await page.screenshot(path="modal_missing.png")
                                return False
                        except Exception as e:
                            logger.error(f"Modal/spinner did not resolve: {e}")
                            await page.screenshot(path="modal_spinner_fail.png")
                            return False
                except Exception as e:
                    logger.warning(f"Button examine/click failed: {e}")
            logger.error("No working Easy Apply button found.")
            return False
        except Exception as e:
            logger.error(f"Apply button search failed: {e}")
            return False

    async def fill_and_submit(self, page):
        try:
            await page.wait_for_selector('.jobs-easy-apply-modal', timeout=5000)
            await asyncio.sleep(1)
            inputs = await page.locator('.jobs-easy-apply-modal input').all()
            logger.info(f"Found {len(inputs)} input fields in modal.")
            filled = False
            for i, inp in enumerate(inputs):
                label = await inp.get_attribute("aria-label")
                name = await inp.get_attribute("name")
                value = await inp.input_value()
                logger.info(f"Input {i}: label={label}, name={name}, value={value}")
                if await inp.is_enabled() and (not value or value.strip() == ""):
                    await inp.fill("Test Example")
                    logger.info(f"Filled input {i} (label={label}, name={name})")
                    filled = True

            # Optionally click Next/Submit if needed
            next_btn = page.locator("button:has-text('Next'), button:has-text('Continue')")
            if await next_btn.is_visible():
                await next_btn.click()
                logger.info("Clicked Next/Continue button")
                await asyncio.sleep(2)

            submit_btn = page.locator("button:has-text('Submit application')")
            if await submit_btn.is_visible():
                await submit_btn.click()
                logger.info("Clicked Submit application button!")
            else:
                logger.info("No Submit application button found yet.")

            await asyncio.sleep(2)

        except Exception as e:
            logger.error(f"Failed to fill/submit: {e}")