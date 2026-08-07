document.addEventListener('DOMContentLoaded', () => {
  const statusDot = document.getElementById('status-dot');
  const statusText = document.getElementById('status-text');
  const connectBtn = document.getElementById('connect-btn');
  const stopBtn = document.getElementById('stop-btn');
  const urlInput = document.getElementById('url-input');
  const logDiv = document.getElementById('log-div');
  const clearLogsBtn = document.getElementById('clear-logs-btn');

  // Load saved state from storage
  chrome.storage.local.get(['wsUrl', 'connectionStatus', 'autoConnect', 'logs'], (result) => {
    urlInput.value = result.wsUrl || 'ws://localhost:8765';
    const autoConnect = result.autoConnect !== false; // default true
    if (!autoConnect) {
      updateStatusUI('stopped');
    } else {
      updateStatusUI(result.connectionStatus || 'disconnected');
    }
    if (Array.isArray(result.logs)) {
      renderLogs(result.logs);
    }
  });

  // Save URL on change
  urlInput.addEventListener('change', () => {
    const url = urlInput.value.trim();
    chrome.storage.local.set({ wsUrl: url });
  });

  // Connect button click
  connectBtn.addEventListener('click', () => {
    const url = urlInput.value.trim() || 'ws://localhost:8765';
    chrome.storage.local.set({ wsUrl: url, autoConnect: true });
    updateStatusUI('connecting');
    chrome.runtime.sendMessage({ action: 'start', url }, (response) => {
      if (chrome.runtime.lastError) {
        addLogEntry('Error connecting: ' + chrome.runtime.lastError.message, 'error');
      }
    });
  });

  // Stop button click - disconnect AND prevent auto-reconnect
  stopBtn.addEventListener('click', () => {
    chrome.storage.local.set({ autoConnect: false });
    updateStatusUI('stopped');
    chrome.runtime.sendMessage({ action: 'stop' }, (response) => {
      if (chrome.runtime.lastError) {
        addLogEntry('Error stopping: ' + chrome.runtime.lastError.message, 'error');
      }
    });
  });

  // Clear logs click
  if (clearLogsBtn) {
    clearLogsBtn.addEventListener('click', () => {
      chrome.storage.local.set({ logs: [] });
      logDiv.innerHTML = '';
      addLogEntry('Logs cleared', 'info');
    });
  }

  // Listen for storage changes
  chrome.storage.onChanged.addListener((changes, area) => {
    if (area !== 'local') return;

    if (changes.connectionStatus) {
      const autoConnect = changes.autoConnect ? changes.autoConnect.newValue : true;
      if (!autoConnect) {
        updateStatusUI('stopped');
      } else {
        updateStatusUI(changes.connectionStatus.newValue);
      }
    }

    if (changes.logs) {
      renderLogs(changes.logs.newValue || []);
    }
  });

  function updateStatusUI(status) {
    statusDot.className = 'status-dot';
    if (status === 'connected') {
      statusDot.classList.add('connected');
      statusText.textContent = 'Connected';
      connectBtn.disabled = true;
      stopBtn.disabled = false;
    } else if (status === 'connecting') {
      statusDot.classList.add('connecting');
      statusText.textContent = 'Connecting...';
      connectBtn.disabled = true;
      stopBtn.disabled = false;
    } else if (status === 'stopped') {
      statusDot.className = 'status-dot'; // red dot
      statusText.textContent = 'Stopped';
      connectBtn.disabled = false;
      stopBtn.disabled = true;
    } else {
      statusText.textContent = 'Disconnected';
      connectBtn.disabled = false;
      stopBtn.disabled = true;
    }
  }

  function renderLogs(logs) {
    logDiv.innerHTML = '';
    logs.slice(-20).reverse().forEach(log => {
      const entry = document.createElement('div');
      entry.className = `log-entry ${log.type || 'info'}`;
      entry.innerHTML = `<span class="time">[${log.time}]</span> ${escapeHtml(log.message)}`;
      logDiv.appendChild(entry);
    });
  }

  function addLogEntry(message, type = 'info') {
    const time = new Date().toLocaleTimeString();
    chrome.storage.local.get(['logs'], (res) => {
      const logs = res.logs || [];
      logs.push({ time, message, type });
      chrome.storage.local.set({ logs });
    });
  }

  function escapeHtml(str) {
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
});
