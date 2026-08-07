// Hermes Browser Extension - Content Script
// Handles page-level DOM helpers and visual feedback for AI automation actions

(() => {
  if (window.__hermesContentScriptLoaded) return;
  window.__hermesContentScriptLoaded = true;

  console.log('[Hermes Content Script] Active on page:', window.location.href);

  // Helper to visually highlight elements interacting with the agent
  function highlightElement(element, color = '#00fff5', duration = 1500) {
    if (!element || !(element instanceof HTMLElement)) return;
    
    const originalOutline = element.style.outline;
    const originalBoxShadow = element.style.boxShadow;
    const originalTransition = element.style.transition;

    element.style.transition = 'all 0.2s ease-in-out';
    element.style.outline = `3px solid ${color}`;
    element.style.boxShadow = `0 0 12px ${color}`;

    setTimeout(() => {
      element.style.outline = originalOutline;
      element.style.boxShadow = originalBoxShadow;
      element.style.transition = originalTransition;
    }, duration);
  }

  // Listen for messages from background service worker
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    try {
      if (message.action === 'highlight') {
        const el = message.selector ? document.querySelector(message.selector) : document.activeElement;
        if (el) {
          highlightElement(el, message.color || '#00fff5');
          sendResponse({ success: true });
        } else {
          sendResponse({ success: false, error: 'Element not found' });
        }
      } else if (message.action === 'ping') {
        sendResponse({ status: 'alive', url: window.location.href });
      }
    } catch (err) {
      sendResponse({ success: false, error: err.message });
    }
    return true;
  });
})();
