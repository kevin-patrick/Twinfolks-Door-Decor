// Background script for Poshmark Listing Extractor
chrome.runtime.onInstalled.addListener(() => {
  console.log('Poshmark Listing Extractor installed');
});

// Handle messages from content scripts or popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('Background received message:', message);
  
  if (message.action === 'extractData') {
    // Forward to content script if needed
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs[0]) {
        chrome.tabs.sendMessage(tabs[0].id, message, sendResponse);
      }
    });
    return true; // Keep message channel open for async response
  }
});