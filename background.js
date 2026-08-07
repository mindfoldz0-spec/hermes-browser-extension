// Hermes Browser Extension - Service Worker (Background Script)

let ws = null;
let keepAliveInterval = null;
let retryCount = 0;
let explicitDisconnect = false;
let userStopped = false;  // User clicked Stop - don't auto-reconnect
const MAX_RETRY_DELAY = 30000;
const DEFAULT_WS_URL = 'ws://localhost:8765';

// Log to background and storage
function log(message, type = 'info') {
  console.log(`[SW] ${message}`);
  const time = new Date().toLocaleTimeString();
  chrome.storage.local.get(['logs'], (result) => {
    const logs = result.logs || [];
    logs.push({ time, message, type });
    // Keep max 50 log entries
    if (logs.length > 50) logs.shift();
    chrome.storage.local.set({ logs });
  });
}

function updateStatus(status) {
  chrome.storage.local.set({ connectionStatus: status });
}

// Connect to WebSocket server
function connect(customUrl) {
  if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
    log('WebSocket connection already active', 'info');
    return;
  }

  explicitDisconnect = false;
  userStopped = false;  // Reset stopped flag when manually connecting
  updateStatus('connecting');

  chrome.storage.local.get(['wsUrl'], (result) => {
    const targetUrl = customUrl || result.wsUrl || DEFAULT_WS_URL;
    log(`Connecting to ${targetUrl}...`, 'info');

    try {
      ws = new WebSocket(targetUrl);

      ws.onopen = () => {
        log(`WebSocket connected to ${targetUrl}`, 'success');
        retryCount = 0;
        updateStatus('connected');
        ws.send(JSON.stringify({ type: 'browser' }));
        ws.send(JSON.stringify({ action: 'connected', source: 'chrome-extension' }));
        startKeepAlive();
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          handleMessage(msg);
        } catch (e) {
          log(`Failed to parse WebSocket message: ${e.message}`, 'error');
        }
      };

      ws.onclose = (event) => {
        log(`WebSocket closed (code ${event.code})`, 'info');
        stopKeepAlive();
        updateStatus('disconnected');
        ws = null;
        if (!explicitDisconnect && !userStopped) {
          scheduleReconnect();
        }
      };

      ws.onerror = (err) => {
        log('WebSocket error encountered', 'error');
      };
    } catch (e) {
      log(`Connection exception: ${e.message}`, 'error');
      updateStatus('disconnected');
    }
  });
}

function disconnect() {
  explicitDisconnect = true;
  stopKeepAlive();
  if (ws) {
    ws.close();
    ws = null;
  }
  updateStatus('disconnected');
  log('Disconnected by user request', 'info');
}

function stop() {
  userStopped = true;
  explicitDisconnect = true;
  stopKeepAlive();
  if (ws) {
    ws.close();
    ws = null;
  }
  updateStatus('stopped');
  log('Stopped - auto-reconnect disabled', 'info');
}

function start() {
  userStopped = false;
  explicitDisconnect = false;
  retryCount = 0;
  log('Starting - auto-reconnect enabled', 'info');
  connect();
}

function scheduleReconnect() {
  if (userStopped) return;  // Don't reconnect if user stopped
  const delay = Math.min(1000 * Math.pow(2, retryCount), MAX_RETRY_DELAY);
  retryCount++;
  log(`Reconnecting in ${Math.round(delay / 1000)}s (attempt ${retryCount})...`, 'info');
  setTimeout(() => {
    if (!explicitDisconnect && !userStopped) connect();
  }, delay);
}

function startKeepAlive() {
  stopKeepAlive();
  keepAliveInterval = setInterval(() => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ action: 'ping' }));
    }
  }, 25000);
}

function stopKeepAlive() {
  if (keepAliveInterval) {
    clearInterval(keepAliveInterval);
    keepAliveInterval = null;
  }
}

function sendResponse(request_id, result, error) {
  if (!ws || ws.readyState !== WebSocket.OPEN) return;
  const msg = error ? { request_id, error } : { request_id, result };
  ws.send(JSON.stringify(msg));
}

// Command Handler
async function handleMessage(msg) {
  const { action, params, request_id } = msg;
  log(`Command received: ${action}`, 'info');

  try {
    let result;
    switch (action) {
      case 'navigate':
        result = await cmdNavigate(params || {});
        break;
      case 'getTabs':
        result = await cmdGetTabs();
        break;
      case 'click':
        result = await cmdClick(params || {});
        break;
      case 'type':
        result = await cmdType(params || {});
        break;
      case 'getText':
        result = await cmdGetText(params || {});
        break;
      case 'getDOM':
        result = await cmdGetDOM(params || {});
        break;
      case 'scroll':
        result = await cmdScroll(params || {});
        break;
      case 'newTab':
        result = await cmdNewTab(params || {});
        break;
      default:
        throw new Error(`Unknown action: ${action}`);
    }
    sendResponse(request_id, result);
    log(`Command '${action}' succeeded`, 'success');
  } catch (e) {
    log(`Command '${action}' failed: ${e.message}`, 'error');
    sendResponse(request_id, null, e.message);
  }
}

// Helpers to identify scriptable target tab
async function getTargetTab(tabId) {
  if (tabId) {
    const tab = await chrome.tabs.get(tabId);
    if (!tab) throw new Error(`Tab ${tabId} not found`);
    return tab;
  }
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tabs.length || !tabs[0].id) throw new Error('No active tab available');
  return tabs[0];
}

function assertScriptableUrl(url) {
  if (url && (url.startsWith('chrome://') || url.startsWith('chrome-extension://') || url.startsWith('about:'))) {
    throw new Error(`Cannot execute scripts on restricted page: ${url}`);
  }
}

// Command implementations
async function cmdNavigate(params) {
  const { url, tabId } = params;
  if (!url) throw new Error('URL parameter is required');

  const tab = await getTargetTab(tabId);
  const updatedTab = await chrome.tabs.update(tab.id, { url });
  return { tabId: updatedTab.id, url: updatedTab.url };
}

async function cmdGetTabs() {
  const tabs = await chrome.tabs.query({});
  return tabs.map(t => ({ id: t.id, url: t.url, title: t.title, active: t.active }));
}

async function cmdClick(params) {
  const { selector, x, y, tabId } = params;
  const tab = await getTargetTab(tabId);
  assertScriptableUrl(tab.url);

  await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: (sel, px, py) => {
      let targetEl = null;
      if (sel) {
        targetEl = document.querySelector(sel);
        if (!targetEl) throw new Error(`Element not found for selector: ${sel}`);
      } else {
        targetEl = document.elementFromPoint(px, py);
        if (!targetEl) throw new Error(`Element not found at point (${px}, ${py})`);
      }

      targetEl.scrollIntoView({ behavior: 'auto', block: 'center' });
      targetEl.click();
      return { clicked: sel || { x: px, y: py } };
    },
    args: [selector || null, x || 0, y || 0],
  });

  // Highlight action via content script
  try {
    chrome.tabs.sendMessage(tab.id, { action: 'highlight', selector, color: '#00ff88' });
  } catch (e) {
    // Ignore content script message errors
  }

  return { success: true };
}

async function cmdType(params) {
  const { selector, text, tabId } = params;
  if (text === undefined || text === null) throw new Error('Text parameter is required');

  const tab = await getTargetTab(tabId);
  assertScriptableUrl(tab.url);

  await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: (sel, txt) => {
      const el = sel ? document.querySelector(sel) : document.activeElement;
      if (!el) throw new Error('No target element to type into');

      el.scrollIntoView({ behavior: 'auto', block: 'center' });
      el.focus();

      if ('value' in el) {
        el.value = txt;
      } else {
        el.textContent = txt;
      }

      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
      return { typed: txt.length };
    },
    args: [selector || null, String(text)],
  });

  try {
    chrome.tabs.sendMessage(tab.id, { action: 'highlight', selector, color: '#00fff5' });
  } catch (e) {
    // Ignore content script message errors
  }

  return { success: true };
}

async function cmdGetText(params) {
  const { selector, tabId } = params;
  const tab = await getTargetTab(tabId);
  assertScriptableUrl(tab.url);

  const results = await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: (sel) => {
      if (sel) {
        const el = document.querySelector(sel);
        return el ? el.innerText : null;
      }
      return document.body ? document.body.innerText : '';
    },
    args: [selector || null],
  });
  return results[0]?.result;
}

async function cmdGetDOM(params) {
  const { tabId } = params;
  const tab = await getTargetTab(tabId);
  assertScriptableUrl(tab.url);

  const results = await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: () => document.documentElement.outerHTML,
  });
  return results[0]?.result;
}

async function cmdScroll(params) {
  const { x, y, selector, tabId } = params;
  const tab = await getTargetTab(tabId);
  assertScriptableUrl(tab.url);

  await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: (px, py, sel) => {
      if (sel) {
        const el = document.querySelector(sel);
        if (!el) throw new Error(`Element not found for selector: ${sel}`);
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        return { scrolled: sel };
      }
      window.scrollBy(px || 0, py || 0);
      return { scrolled: { x: px, y: py } };
    },
    args: [x || 0, y || 0, selector || null],
  });
  return { success: true };
}

async function cmdNewTab(params) {
  const { url } = params;
  const tab = await chrome.tabs.create({ url: url || 'about:blank', active: true });
  return { tabId: tab.id, url: tab.url };
}

// Runtime message listener for Popup UI
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'start' || request.action === 'connect') {
    start();
    sendResponse({ success: true });
  } else if (request.action === 'stop') {
    stop();
    sendResponse({ success: true });
  } else if (request.action === 'disconnect') {
    disconnect();
    sendResponse({ success: true });
  } else if (request.action === 'getStatus') {
    sendResponse({
      connected: ws !== null && ws.readyState === WebSocket.OPEN,
      wsState: ws ? ws.readyState : -1,
      stopped: userStopped
    });
  }
  return true;
});

// Auto connect on startup (unless user previously stopped)
chrome.storage.local.get(['autoConnect'], (result) => {
  const autoConnect = result.autoConnect !== false; // default true
  if (autoConnect) {
    connect();
  } else {
    userStopped = true;
    log('Auto-connect disabled by user', 'info');
  }
});
