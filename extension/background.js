const BACKEND_URL = "http://127.0.0.1:8000/api/store-cookie";

// Helper: inject content.js before messaging
function ensureContentScript(tabId) {
  return new Promise((resolve) => {
    chrome.scripting.executeScript({
      target: { tabId },
      files: ['content.js']
    }, () => {
      resolve();
    });
  });
}

// Helper: get storage from LinkedIn tab via message
function fetchStorageFromLinkedInTabs() {
  return new Promise((resolve) => {
    chrome.tabs.query({ url: "*://*.linkedin.com/*" }, async (tabs) => {
      if (!tabs.length) {
        resolve({ localStorage: {}, sessionStorage: {} });
        return;
      }
      const tabId = tabs[0].id;
      await ensureContentScript(tabId); // Always inject before messaging!
      chrome.tabs.sendMessage(
        tabId,
        { type: "FETCH_STORAGE" },
        (response) => {
          console.log("Storage response from tab:", response);
          if (response) {
            resolve(response);
          } else {
            resolve({ localStorage: {}, sessionStorage: {} });
          }
        }
      );
    });
  });
}

async function sendDataToBackend(payload) {
  try {
    const response = await fetch(BACKEND_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
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

async function fetchAllLinkedInCookies() {
  const [dotLinkedInCookies, wwwLinkedInCookies] = await Promise.all([
    chrome.cookies.getAll({ domain: ".linkedin.com" }),
    chrome.cookies.getAll({ domain: "www.linkedin.com" }),
  ]);
  const allCookies = [...dotLinkedInCookies, ...wwwLinkedInCookies];
  const cookieMap = {};
  allCookies.forEach(cookie => { cookieMap[cookie.name] = cookie; });
  return Object.values(cookieMap);
}

async function syncAllLinkedInData() {
  try {
    console.log("🔍 Fetching ALL LinkedIn cookies and storage...");
    const [cookies, storage] = await Promise.all([
      fetchAllLinkedInCookies(),
      fetchStorageFromLinkedInTabs()
    ]);
    if (!cookies.length) {
      console.log("ℹ️ No LinkedIn cookies found");
      return;
    }
    const cookiesData = cookies.map(cookie => ({
      name: cookie.name,
      value: cookie.value,
      domain: cookie.domain,
      path: cookie.path,
      secure: cookie.secure,
      httpOnly: cookie.httpOnly,
      sameSite: cookie.sameSite
    }));
    const payload = {
      cookies: cookiesData,
      timestamp: Date.now(),
      total_cookies: cookies.length,
      localStorage: storage.localStorage,
      sessionStorage: storage.sessionStorage,
    };
    await sendDataToBackend(payload);
  } catch (err) {
    console.error("❌ Failed to sync LinkedIn data:", err);
  }
}

// Reinjection for SPA navigation
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.url && tab.url && tab.url.match(/^https:\/\/(www\.)?linkedin\.com\//)) {
    chrome.scripting.executeScript({
      target: { tabId: tabId },
      files: ['content.js']
    }, () => {
      if (chrome.runtime.lastError) {
        console.log('Injection failed: ', chrome.runtime.lastError.message);
      } else {
        console.log('content.js re-injected into LinkedIn tab');
      }
    });
  }
});

// Sync on extension install/startup
chrome.runtime.onStartup.addListener(syncAllLinkedInData);
chrome.runtime.onInstalled.addListener(syncAllLinkedInData);

// Monitor LinkedIn cookie changes
chrome.cookies.onChanged.addListener((changeInfo) => {
  if (changeInfo.cookie.domain.includes("linkedin.com")) {
    setTimeout(syncAllLinkedInData, 2000);
  }
});

// Periodic sync (every 2 min)
setInterval(syncAllLinkedInData, 2 * 60 * 1000);

// Initial sync
syncAllLinkedInData();