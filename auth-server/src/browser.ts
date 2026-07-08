import { Page, CDPSession, BrowserContext, Browser } from "playwright";
import { WebSocket } from "ws";
import { db } from "./db";
import { chromium } from "playwright-extra";
import stealth from 'puppeteer-extra-plugin-stealth'
import Redis from "ioredis";

chromium.use(stealth())

const GRACE_PERIOD_MS = 60_000; // 60 seconds before killing browser on disconnect

export interface BrowserSession {
    browser: Browser;
    context: BrowserContext;
    mainPage: Page | null;
    activePage: Page | null;
    activePageCdp: CDPSession | null;
    authUser: string;
    ws: WebSocket | null;
    gracePeriodTimer: ReturnType<typeof setTimeout> | null;
    attachStream: (targetPage: Page) => Promise<CDPSession>;
    checkFocusAndNotify: (page: Page) => Promise<void>;
    width: number;
    height: number;
    dpr: number;
    isMobile: boolean;
}

// In-memory map: token → active browser session
export const activeSessions = new Map<string, BrowserSession>();


/**
 * Reattach a new WebSocket to an existing browser session (reconnect after mobile background)
 */
export function reattachSession(session: BrowserSession, newWs: WebSocket, redis: Redis, token: string, authUser: string) {
    // Cancel the grace period timer — user is back
    if (session.gracePeriodTimer) {
        clearTimeout(session.gracePeriodTimer);
        session.gracePeriodTimer = null;
        console.log(`Grace period cancelled for ${authUser}. User reconnected.`);
    }

    // Replace the WebSocket reference
    session.ws = newWs;

    // Reattach the screencast stream to push frames to the new WebSocket
    if (session.activePage) {
        session.attachStream(session.activePage).then((cdp) => {
            session.activePageCdp = cdp;
        }).catch((err) => {
            console.error(`Failed to reattach stream for ${authUser}:`, err);
        });
    }

    // Set up close handler for the new WebSocket
    newWs.on('close', () => {
        handleWsClose(session, redis, token);
    });

    // Set up message handler for the new WebSocket
    setupMessageHandler(newWs, session);
}


/**
 * Handle WebSocket close with a 60-second grace period
 */
function handleWsClose(session: BrowserSession, redis: Redis, token: string) {
    console.log(`Connection dropped for ${session.authUser}. Starting ${GRACE_PERIOD_MS / 1000}s grace period...`);
    session.ws = null;

    session.gracePeriodTimer = setTimeout(async () => {
        console.log(`Grace period expired for ${session.authUser}. Terminating browser.`);

        // Clean up Redis tokens so user can initiate a new session
        try {
            await redis.del(`stream_token:${token}`);
            await redis.del(`stream_token_user:${session.authUser}`);
        } catch (e) {
            console.error(`Failed to clean up Redis tokens for ${session.authUser}:`, e);
        }

        // Clean up browser
        await session.browser.close().catch(() => { });
        activeSessions.delete(token);
    }, GRACE_PERIOD_MS);
}


/**
 * Set up mouse/keyboard/scroll message handling on a WebSocket
 */
function setupMessageHandler(ws: WebSocket, session: BrowserSession) {
    ws.on('message', async (message) => {
        try {
            if (!session.activePage) return;
            const event = JSON.parse(message.toString());

            if (event.type === 'mouse') {
                if (session.isMobile) {
                    // CAPTCHAs are in cross-origin iframes and only respond to mouse clicks.
                    // LinkedIn UI elements are in the main DOM and need touch taps.
                    // We dynamically check if the target is an iframe to pick the correct event.
                    const isIframe = await session.activePage.evaluate(({x, y}) => {
                        const el = document.elementFromPoint(x, y);
                        return el ? el.tagName.toLowerCase() === 'iframe' : false;
                    }, {x: event.x, y: event.y}).catch(() => false);

                    if (isIframe) {
                        await session.activePage.mouse.click(event.x, event.y);
                    } else {
                        await session.activePage.touchscreen.tap(event.x, event.y);
                    }
                } else {
                    await session.activePage.mouse.click(event.x, event.y);
                }

                // After click settles, check if a text input is now focused
                await session.checkFocusAndNotify(session.activePage);
            } else if (event.type === 'keyboard') {
                if (event.key && event.key !== 'Unidentified') {
                    try {
                        await session.activePage.keyboard.press(event.key);
                    } catch (e) {
                        console.log(`Failed to press key: ${event.key}`);
                    }
                }
            } else if (event.type === 'scroll') {
                await session.activePage.mouse.wheel(event.deltaX, event.deltaY);
            }
        }
        catch (error) {
            console.log(`error in middle of the events ${error}`)
        }
    })
}


export async function handleBrowser(ws: WebSocket, authUser: string, width: number, height: number, dpr: number, redis: Redis, token: string) {
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

        // Create the session object
        const session: BrowserSession = {
            browser,
            context,
            mainPage: null,
            activePage: null,
            activePageCdp: null,
            authUser,
            ws,
            gracePeriodTimer: null,
            width,
            height,
            dpr,
            isMobile,
            attachStream: async () => null as any, // placeholder, set below
            checkFocusAndNotify: async () => {},    // placeholder, set below
        };

        const attachStream = async (targetPage: Page): Promise<CDPSession> => {
            const targetClient = await targetPage.context().newCDPSession(targetPage);

            // If this is the active page, store the CDP session for input dispatch
            if (targetPage === session.activePage || !session.activePageCdp) {
                session.activePageCdp = targetClient;
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
                    // and the WebSocket is open
                    if (session.ws && session.ws.readyState === session.ws.OPEN && session.activePage === targetPage) {
                        session.ws.send(JSON.stringify({
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
                if (session.ws && session.ws.readyState === session.ws.OPEN) {
                    session.ws.send(JSON.stringify({ type: 'focus_changed', isInput }));
                }
            } catch (_) { }
        };

        // Assign the real functions to the session
        session.attachStream = attachStream;
        session.checkFocusAndNotify = checkFocusAndNotify;

        // Set up popup interceptor BEFORE creating the main page to catch any user-initiated popups
        context.on('page', async (popUp) => {
            // Guard clause: If mainPage isn't set yet, or if the emitted page IS the mainPage, ignore it.
            if (!session.mainPage || popUp === session.mainPage) return;

            console.log(`OAuth Popup intercepted for ${authUser}. Switching active context.`);
            await popUp.setViewportSize({ width: width, height: height });
            await popUp.waitForLoadState()

            session.activePage = popUp
            session.activePageCdp = await attachStream(popUp)

            popUp.on('close', async () => {
                console.log(`Popup closed for ${authUser}. Reverting to main context.`);
                session.activePage = session.mainPage;

                if (session.mainPage) {
                    await session.mainPage.bringToFront().catch(() => { });
                }
            });
        })

        // Create the initial page (This will fire the 'page' event, but the guard clause will safely ignore it)
        session.mainPage = await context.newPage();
        session.activePage = session.mainPage; // Set initial active page
        session.activePageCdp = await attachStream(session.mainPage);

        // Register the session in the active sessions map
        activeSessions.set(token, session);

        // Set up message handler for this WebSocket
        setupMessageHandler(ws, session);

        // Set up close handler with grace period
        ws.on('close', () => {
            handleWsClose(session, redis, token);
        });

        await session.mainPage.goto('https://www.linkedin.com/login/')

        session.mainPage.on('framenavigated', async (frame) => {
            const currentUrl = frame.url();

            if (currentUrl.includes('linkedin.com/feed')) {
                console.log(`Login sequence complete for user: ${authUser}. Extracting payload...`);
                try {
                    const sessionState = await context.storageState()

                    await db.query(`UPDATE "User" SET linkedin_context = $1, context_updated_at = NOW() WHERE id = $2`, [sessionState, authUser])

                    console.log(`Session securely saved to PostgreSQL for ${authUser}.`);
                    if (session.ws && session.ws.readyState === session.ws.OPEN) {
                        session.ws.send(JSON.stringify({ type: 'success' }));
                    }

                    // Clean up Redis tokens
                    try {
                        await redis.del(`stream_token:${token}`);
                        await redis.del(`stream_token_user:${authUser}`);
                    } catch (e) {
                        console.error(`Failed to clean up Redis tokens:`, e);
                    }

                    // Terminate the browser session and clean up
                    activeSessions.delete(token);
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
        // Clean up Redis tokens on fatal error
        try {
            await redis.del(`stream_token:${token}`);
            await redis.del(`stream_token_user:${authUser}`);
        } catch (e) { }
        activeSessions.delete(token);
        if (ws.readyState === ws.OPEN) {
            ws.close();
        }
    }
}