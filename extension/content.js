console.log("DevHire content.js loaded!");

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === 'FETCH_STORAGE') {
    sendResponse({
      localStorage: {...window.localStorage},
      sessionStorage: {...window.sessionStorage}
    });
  }
  return true;
});