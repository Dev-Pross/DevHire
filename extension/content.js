console.log("DevHire content.js loaded!");

// Listen for storage fetch request
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === "FETCH_STORAGE") {
    try {
      console.log("FETCH_STORAGE requested");
      const localStorageData = { ...window.localStorage };
      const sessionStorageData = { ...window.sessionStorage };

      console.log("LocalStorage keys:", Object.keys(localStorageData));
      console.log("SessionStorage keys:", Object.keys(sessionStorageData));

      sendResponse({
        localStorage: localStorageData,
        sessionStorage: sessionStorageData,
      });
    } catch (error) {
      console.error("Error fetching storage:", error);
      sendResponse({ localStorage: {}, sessionStorage: {} });
    }
    // Keep the message channel open for async response
    return true;
  }
});
