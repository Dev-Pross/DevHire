import { Page, CDPSession } from "playwright";
import { WebSocket } from "ws";
import { db } from "./db";
import { chromium } from "playwright-extra";
import stealth from 'puppeteer-extra-plugin-stealth'

chromium.use(stealth())


export async function handleBrowser(ws: WebSocket, authUser: string, width: number, height: number, dpr: number) {
    console.log(`Starting isolated browser session for user: ${authUser} with DPR: ${dpr}`);

    try {
        const browser = await chromium.launch({
            headless: true,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                `--window-size=${Math.round(width * dpr)},${Math.round(height * dpr)}`
            ]
        })

        const isMobile = width < 1024;

        const desktopUA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36";
        const mobileUA = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1";

        const context = await browser.newContext({
            userAgent: isMobile ? mobileUA : desktopUA,
            viewport: { width: width, height: height },
            deviceScaleFactor: dpr, // Emulate high-DPI screens for crystal clear text
            locale: "en-US",
            timezoneId: "Asia/Calcutta",
            isMobile: isMobile,
            hasTouch: isMobile
        })

        await context.addInitScript((isMobile) => {
            if (window.navigator && window.navigator.credentials) {
                window.navigator.credentials.get = async () => { throw new Error("WebAuthn not supported"); };
                window.navigator.credentials.create = async () => { throw new Error("WebAuthn not supported"); };
            }

            // Google Auth UI Purge CSS style injection
            const injectStyle = () => {
                const style = document.createElement('style');
                style.textContent = 'iframe[src*="google.com/gsi"], iframe[src*="smartlock"], button[data-provider="GOOGLE"], .nsm7Bb-HzV7m-LgbsSe { display: none !important; }';
                if (document.head) {
                    document.head.appendChild(style);
                } else if (document.documentElement) {
                    document.documentElement.appendChild(style);
                } else {
                    setTimeout(injectStyle, 1);
                }
            };
            injectStyle();

            // Mobile viewport retention logic
            if (isMobile) {
                const forceViewport = () => {
                    if (!document.head) return;
                    const meta = document.querySelector('meta[name="viewport"]');
                    const expectedContent = 'width=device-width, initial-scale=1, maximum-scale=1, user-scalable=0';
                    if (!meta || meta.getAttribute('content') !== expectedContent) {
                        if (meta) {
                            meta.remove();
                        }
                        document.head.insertAdjacentHTML('beforeend', '<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=0">');
                    }
                };

                const initViewportMonitor = () => {
                    if (document.head) {
                        forceViewport();
                        const observer = new MutationObserver(forceViewport);
                        observer.observe(document.head, { childList: true, subtree: true, attributes: true });
                    } else {
                        setTimeout(initViewportMonitor, 1);
                    }
                };
                initViewportMonitor();
            }
        }, isMobile);

        let mainPage: Page | null = null;
        let activePage: Page | null = null;
        // Store the CDP session for each page so we can use it for both
        // screencast AND input dispatch without creating new sessions per click
        let activePageCdp: CDPSession | null = null;

        const attachStream = async (targetPage: Page) => {
            const targetClient = await targetPage.context().newCDPSession(targetPage);

            // If this is the active page, store the CDP session for input dispatch
            if (targetPage === activePage || !activePageCdp) {
                activePageCdp = targetClient;
            }

            await targetClient.send('Page.startScreencast', {
                format: 'jpeg',
                maxWidth: Math.round(width * dpr),
                maxHeight: Math.round(height * dpr),
                quality: 100,
                everyNthFrame: 1
            });

            targetClient.on('Page.screencastFrame', async (frameObj) => {
                try {
                    // Only push frames to the client if this is the currently active window
                    if (ws.readyState === ws.OPEN && activePage === targetPage) {
                        ws.send(JSON.stringify({
                            type: 'frame',
                            data: frameObj.data,
                            width: frameObj.metadata.deviceWidth,
                            height: frameObj.metadata.deviceHeight
                        }));
                    }
                    // Acknowledge the frame regardless, otherwise Playwright pauses the stream permanently
                    await targetClient.send('Page.screencastFrameAck', { sessionId: frameObj.sessionId });
                } catch (error) { }
            });

            return targetClient;
        };

        // Set up popup interceptor BEFORE creating the main page to catch any user-initiated popups
        context.on('page', async (popUp) => {
            // Guard clause: If mainPage isn't set yet, or if the emitted page IS the mainPage, ignore it.
            if (!mainPage || popUp === mainPage) return;

            console.log(`OAuth Popup intercepted for ${authUser}. Switching active context.`);
            await popUp.setViewportSize({ width: width, height: height });
            await popUp.waitForLoadState()

            activePage = popUp
            activePageCdp = await attachStream(popUp)

            popUp.on('close', async () => {
                console.log(`Popup closed for ${authUser}. Reverting to main context.`);
                activePage = mainPage;

                if (mainPage) {
                    await mainPage.bringToFront().catch(() => { });
                }
            });
        })

        // Create the initial page (This will fire the 'page' event, but the guard clause will safely ignore it)
        mainPage = await context.newPage();
        activePage = mainPage; // Set initial active page
        activePageCdp = await attachStream(mainPage);

        // Server-side focus detection: after each click, evaluate the actual
        // focused element in the DOM and tell the client whether to show keyboard
        const checkFocusAndNotify = async (page: Page) => {
            try {
                const isInput = await page.evaluate(() => {
                    const el = document.activeElement;
                    if (!el) return false;
                    const tag = el.tagName.toLowerCase();
                    if (tag === 'textarea') return true;
                    if (tag === 'input') {
                        const type = el.getAttribute('type')?.toLowerCase() || 'text';
                        return ['text', 'password', 'email', 'number', 'tel'].includes(type);
                    }
                    return false;
                });
                if (ws.readyState === ws.OPEN) {
                    ws.send(JSON.stringify({ type: 'focus_changed', isInput }));
                }
            } catch (_) { }
        };

        ws.on('message', async (message) => {
            try {
                if (!activePage) return;
                const event = JSON.parse(message.toString());

                if (event.type === 'mouse') {
                    if (isMobile) {
                        // CAPTCHAs are in cross-origin iframes and only respond to mouse clicks.
                        // LinkedIn UI elements are in the main DOM and need touch taps.
                        // We dynamically check if the target is an iframe to pick the correct event.
                        const isIframe = await activePage.evaluate(({x, y}) => {
                            const el = document.elementFromPoint(x, y);
                            return el ? el.tagName.toLowerCase() === 'iframe' : false;
                        }, {x: event.x, y: event.y}).catch(() => false);

                        if (isIframe) {
                            await activePage.mouse.click(event.x, event.y);
                        } else {
                            await activePage.touchscreen.tap(event.x, event.y);
                        }
                    } else {
                        await activePage.mouse.click(event.x, event.y);
                    }

                    // After click settles, check if a text input is now focused
                    await checkFocusAndNotify(activePage);
                } else if (event.type === 'keyboard') {
                    if (event.key && event.key !== 'Unidentified') {
                        try {
                            await activePage.keyboard.press(event.key);
                        } catch (e) {
                            console.log(`Failed to press key: ${event.key}`);
                        }
                    }
                } else if (event.type === 'scroll') {
                    await activePage.mouse.wheel(event.deltaX, event.deltaY);
                }
            }
            catch (error) {
                console.log(`error in middle of the events ${error}`)
            }
        })

        ws.on('close', async () => {
            console.log(`Connection dropped for ${authUser}. Terminating browser.`);
            await browser.close().catch(() => { }); // Catch prevents crash if already closed
        });

        await mainPage.goto('https://www.linkedin.com/login/')

        mainPage.on('framenavigated', async (frame) => {
            const currentUrl = frame.url();

            if (currentUrl.includes('linkedin.com/feed')) {
                console.log(`Login sequence complete for user: ${authUser}. Extracting payload...`);
                try {
                    const sessionState = await context.storageState()

                    await db.query(`UPDATE "User" SET linkedin_context = $1, context_updated_at = NOW() WHERE id = $2`, [sessionState, authUser])

                    console.log(`Session securely saved to PostgreSQL for ${authUser}.`);
                    if (ws.readyState === ws.OPEN) {
                        ws.send(JSON.stringify({ type: 'success' }));
                    }
                    // Terminate the browser session to stop streaming
                    await browser.close().catch(() => { });
                }
                catch (error) {
                    console.log(`error while saving session ${error}`)
                }
            }
        })
    }
    catch (error) {
        console.error(`Fatal browser error for user ${authUser}:`, error);
        if (ws.readyState === ws.OPEN) {
            ws.close();
        }
    }
}