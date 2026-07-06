import { Page } from "playwright";
import { WebSocket } from "ws";
import { db } from "./db";
import { chromium } from "playwright-extra";
import stealth from 'puppeteer-extra-plugin-stealth'

chromium.use(stealth())


export async function handleBrowser(ws: WebSocket, authUser: string, width: number, height: number) {
    console.log(`Starting isolated browser session for user: ${authUser}`);

    try {
        const browser = await chromium.launch({
            headless: true,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                `--window-size=${width},${height}`
            ]
        })

        const isMobile = width < 1024

        const desktopUA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36";
        const mobileUA = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1";

        const context = await browser.newContext({
            userAgent: isMobile ? mobileUA : desktopUA,
            viewport: { width: width, height: height },
            locale: "en-US",
            timezoneId: "Asia/Calcutta",
            isMobile: isMobile,
            hasTouch: isMobile
        })

        await context.addInitScript(() => {
            if (window.navigator && window.navigator.credentials) {
                window.navigator.credentials.get = async () => { throw new Error("WebAuthn not supported"); };
                window.navigator.credentials.create = async () => { throw new Error("WebAuthn not supported"); };
            }
        });

        let mainPage: Page | null = null;
        let activePage: Page | null = null;

        const attachStream = async (targetPage: Page) => {
            const targetClient = await targetPage.context().newCDPSession(targetPage);

            await targetClient.send('Page.startScreencast', {
                format: 'jpeg',
                quality: 80, // 100 causes heavy network latency; 80 is the sweet spot
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
        };

        // Set up popup interceptor BEFORE creating the main page to catch any user-initiated popups
        context.on('page', async (popUp) => {
            // Guard clause: If mainPage isn't set yet, or if the emitted page IS the mainPage, ignore it.
            if (!mainPage || popUp === mainPage) return;

            console.log(`OAuth Popup intercepted for ${authUser}. Switching active context.`);
            await popUp.setViewportSize({ width: width, height: height });
            await popUp.waitForLoadState()

            activePage = popUp
            await attachStream(popUp)

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
        await attachStream(mainPage);

        ws.on('message', async (message) => {
            try {
                if (!activePage) return;
                const event = JSON.parse(message.toString());

                if (event.type === 'mouse') {
                    await activePage.mouse.click(event.x, event.y);
                } else if (event.type === 'keyboard') {
                    await activePage.keyboard.press(event.key);
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