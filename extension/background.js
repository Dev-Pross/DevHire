const BACKEND_URL = "http://127.0.0.1:8000/api/store-cookie";

// Helper: Extract Storage from all frames in a tab (including cross-origin iframes)
async function extractStorageFromTab(tabId) {
  return new Promise((resolve) => {
    chrome.scripting.executeScript(
      {
        target: { tabId: tabId, allFrames: true },
        func: () => {
          try {
            // Get localStorage as array of key/value objects
            const ls = [];
            for (let i = 0; i < localStorage.length; i++) {
              const key = localStorage.key(i);
              ls.push({ name: key, value: localStorage.getItem(key) });
            }

            // Get sessionStorage as array of key/value objects
            const ss = [];
            for (let i = 0; i < sessionStorage.length; i++) {
              const key = sessionStorage.key(i);
              ss.push({ name: key, value: sessionStorage.getItem(key) });
            }

            return {
              origin: window.location.origin,
              localStorage: ls,
              sessionStorage: ss
            };
          } catch (e) {
            // Might fail for cross-origin frames without correct permissions
            return null;
          }
        },
      },
      (results) => {
        if (chrome.runtime.lastError) {
          console.error("❌ extractStorageFromTab error:", chrome.runtime.lastError.message);
          resolve([]);
          return;
        }
        if (!results) {
          console.error("❌ extractStorageFromTab: No results returned");
          resolve([]);
          return;
        }

        // Filter out nulls and format exactly like db_li_context.json
        const origins = [];
        for (const frameResult of results) {
          if (frameResult.result && frameResult.result.origin !== "null") {
            origins.push({
              origin: frameResult.result.origin,
              localStorage: frameResult.result.localStorage,
              sessionStorage: frameResult.result.sessionStorage
            });
          }
        }
        resolve(origins);
      }
    );
  });
}

// Fetch user ID from Dev-Hire frontend (localhost:3000)
async function fetchDevHireUserId() {
  return new Promise((resolve) => {
    chrome.tabs.query({ url: "*://localhost/*" }, async (tabs) => {
      // Filter tabs by port 3000 if necessary, or just take the first one
      const devHireTabs = tabs.filter(t => t.url && t.url.includes(":3000"));
      let tabId;
      let createdTab = false;
      
      if (!devHireTabs.length) {
        // Open DevHire aggressively in the background if not open
        console.log("Opening DevHire in background to fetch UserId...");
        const tab = await chrome.tabs.create({ url: "http://localhost:3000/", active: false });
        tabId = tab.id;
        createdTab = true;
        // Wait for it to load
        await new Promise(r => setTimeout(r, 2000));
      } else {
        tabId = devHireTabs[0].id;
      }

      chrome.scripting.executeScript(
        {
          target: { tabId: tabId },
          func: () => {
            // First check sessionStorage for 'email' or 'id' which DevHire frontend uses
            const sessionEmail = sessionStorage.getItem("email");
            const sessionId = sessionStorage.getItem("id");
            if (sessionEmail) return sessionEmail;
            if (sessionId) return sessionId;

            // Fallback: Look for Supabase auth tokens in localStorage
            for (let i = 0; i < localStorage.length; i++) {
              const key = localStorage.key(i);
              if (key.includes('supabase.auth.token')) {
                try {
                  const data = JSON.parse(localStorage.getItem(key));
                  return data.user.email || data.user.id;
                } catch (e) { }
              }
            }

            // Fallback: Check cookies for sb-*-auth-token
            const cookies = document.cookie.split(';');
            for (let c of cookies) {
              if (c.trim().startsWith('sb-') && c.includes('auth-token')) {
                try {
                  const tokenStr = decodeURIComponent(c.split('=')[1].trim());
                  const parsed = JSON.parse(tokenStr);
                  if (parsed && parsed[0] && parsed[0].user) {
                    return parsed[0].user.id;
                  }
                } catch (e) { }
              }
            }

            return null;
          },
        },
        (results) => {
          if (createdTab) {
            chrome.tabs.remove(tabId); // Clean up the aggressively opened tab
          }
          if (chrome.runtime.lastError || !results || !results[0].result) {
            resolve(null);
          } else {
            resolve(results[0].result);
          }
        }
      );
    });
  });
}

// Ensure LinkedIn is open and extract all data
async function fetchLinkedInDataAggressively(allowCreateTab = true) {
  return new Promise((resolve) => {
    chrome.tabs.query({ url: "*://*.linkedin.com/*" }, async (tabs) => {
      // Filter out discarded (sleeping) tabs which can't run scripts
      const activeTabs = tabs.filter(t => !t.discarded);
      
      let tabId;
      let createdTab = false;

      if (!activeTabs.length) {
        console.log("Opening LinkedIn in minimized background window to fetch session...");
        const win = await chrome.windows.create({
          url: "https://www.linkedin.com/feed/",
          type: "popup",
          state: "minimized"
        });
        tabId = win.tabs[0].id;
        createdTab = true;
        
        // Wait for tab to fully load instead of just waiting 5 seconds
        await new Promise(r => {
           let timeout = setTimeout(() => {
              chrome.tabs.onUpdated.removeListener(listener);
              r();
           }, 10000); // 10s max wait
           
           function listener(tId, info) {
              if (tId === tabId && info.status === 'complete') {
                  clearTimeout(timeout);
                  chrome.tabs.onUpdated.removeListener(listener);
                  setTimeout(r, 2000); // give it 2 extra seconds after complete
              }
           }
           chrome.tabs.onUpdated.addListener(listener);
        });
      } else {
        tabId = activeTabs[0].id;
      }

      // 1. Extract Storage from all frames
      const origins = await extractStorageFromTab(tabId);

      // 2. Extract Fingerprint
      const fingerprint = await new Promise(res => {
        chrome.scripting.executeScript(
          {
            target: { tabId: tabId },
            func: () => {
              return {
                userAgent: navigator.userAgent,
                platform: navigator.platform,
                language: navigator.language,
                languages: navigator.languages,
                timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                hardwareConcurrency: navigator.hardwareConcurrency || null,
                deviceMemory: navigator.deviceMemory || null,
                screen: { width: screen.width, height: screen.height, pixelRatio: window.devicePixelRatio, colorDepth: screen.colorDepth },
                viewport: { width: window.innerWidth, height: window.innerHeight }
              };
            }
          },
          (results) => {
            if (chrome.runtime.lastError) {
                console.error("❌ fingerprint error:", chrome.runtime.lastError.message);
                res({});
            } else if (!results || !results[0].result) {
                console.error("❌ fingerprint: No results");
                res({});
            } else {
                res(results[0].result);
            }
          }
        );
      });

      if (createdTab) {
        // Find the window this tab belongs to and close the entire window
        chrome.tabs.get(tabId, (tab) => {
           if (tab && tab.windowId) {
               chrome.windows.remove(tab.windowId);
           }
        });
      }

      // 3. Dynamically fetch cookies for all unique origins we discovered
      let allCookies = [];
      try {
        const cookieDomains = new Set([".linkedin.com", "www.linkedin.com"]);
        for (const org of origins) {
          try {
            const url = new URL(org.origin);
            cookieDomains.add("." + url.hostname);
          } catch (e) { }
        }

        const cookiePromises = Array.from(cookieDomains).map(domain =>
          chrome.cookies.getAll({ domain: domain })
        );

        const cookieArrays = await Promise.all(cookiePromises);

        const cookieMap = {};
        cookieArrays.flat().forEach(cookie => {
          cookieMap[cookie.name] = cookie;
        });
        allCookies = Object.values(cookieMap);
      } catch (e) {
        console.error("Cookie extraction error", e);
      }

      // Cache the extracted origins and fingerprint so we can sync silently next time
      chrome.storage.local.set({ 
        cachedOrigins: origins, 
        cachedFingerprint: fingerprint 
      });

      resolve({ origins, fingerprint, cookies: allCookies });
    });
  });
}

// Send collected data to backend
async function sendDataToBackend(payload) {
  try {
    const response = await fetch(BACKEND_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (response.ok) {
      console.log("✅ Successfully synced LinkedIn data to backend");
    } else {
      console.error("❌ Backend error:", response.status);
    }
  } catch (err) {
    console.error("❌ Failed to send data to backend:", err);
  }
}

let isSyncing = false;

// Main function: fetch all data and send to backend
async function syncAllLinkedInData() {
  if (isSyncing) {
      console.log("⏳ Sync already in progress, skipping...");
      return;
  }
  isSyncing = true;
  try {
    console.log("🔍 Fetching ALL LinkedIn cookies, storage, and fingerprint...");

    const userId = await fetchDevHireUserId();
    if (!userId) {
      console.log("ℹ️ User not logged into DevHire. Cannot sync to backend yet.");
      return;
    }

    const { origins, fingerprint, cookies } = await fetchLinkedInDataAggressively();

    if (!cookies.length) {
      console.log("ℹ️ No LinkedIn cookies found");
      return;
    }

    // Map cookies to the shape Playwright expects
    const cookiesData = cookies.map((cookie) => ({
      name: cookie.name,
      value: cookie.value,
      domain: cookie.domain,
      path: cookie.path,
      secure: cookie.secure,
      httpOnly: cookie.httpOnly,
      sameSite: cookie.sameSite,
      expirationDate: cookie.expirationDate || null,
      // session can be managed by absence of expirationDate
    }));

    const payload = {
      user_id: userId,
      cookies: cookiesData,
      origins: origins,
      fingerprint,
      timestamp: Date.now()
    };

    await sendDataToBackend(payload);
  } catch (err) {
    console.error("❌ Failed to sync LinkedIn data:", err);
  } finally {
    isSyncing = false;
  }
}

// Debounced automatic sync (max once every 2 minutes) to prevent continuous requests
let syncTimeout = null;
let lastSyncTime = 0;
const SYNC_COOLDOWN_MS = 2 * 60 * 1000; // 2 minutes

chrome.cookies.onChanged.addListener((changeInfo) => {
  if (changeInfo.cookie.domain.includes("linkedin.com")) {
    const now = Date.now();
    
    // Clear any pending timeout
    if (syncTimeout) {
      clearTimeout(syncTimeout);
    }
    
    // If we haven't synced recently, schedule one shortly
    if (now - lastSyncTime > SYNC_COOLDOWN_MS) {
      syncTimeout = setTimeout(() => {
        lastSyncTime = Date.now();
        syncAllLinkedInData();
      }, 5000);
    } else {
      // Otherwise, schedule it for when the cooldown expires
      const remainingCooldown = SYNC_COOLDOWN_MS - (now - lastSyncTime);
      syncTimeout = setTimeout(() => {
        lastSyncTime = Date.now();
        syncAllLinkedInData();
      }, remainingCooldown);
    }
  }
});

// Sync on extension install/startup
chrome.runtime.onStartup.addListener(syncAllLinkedInData);
chrome.runtime.onInstalled.addListener(syncAllLinkedInData);



// Periodic sync every 2 minutes
setInterval(syncAllLinkedInData, 2 * 60 * 1000);

// Initial sync immediately
syncAllLinkedInData();
