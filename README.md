# 🔌 Hermes Browser Extension

**Browser automation via WebSocket relay — control your browser from any CLI or AI agent.**

A lightweight Manifest V3 Chrome/Edge extension paired with a Python WebSocket relay server, enabling programmatic browser control for AI agents, automation scripts, and custom tooling.

---

## 🏗️ Architecture

```
┌──────────────┐     WebSocket      ┌─────────────────┐     WebSocket      ┌──────────────┐
│   CLI Client  │ ◄══════════════► │   Relay Server   │ ◄══════════════► │   Extension   │
│  (Python/JS)  │    ws://8765      │    (server.py)   │    ws://8765      │  (background) │
└──────────────┘                    └─────────────────┘                    └──────────────┘
                                                                                    │
                                                                           chrome.tabs API
                                                                                    │
                                                                              ┌─────▼─────┐
                                                                              │  Web Page  │
                                                                              └───────────┘
```

- **Relay Server** (`server.py`) — Async Python WebSocket server that bridges CLI clients and browser extension clients on `localhost:8765`
- **Browser Extension** (`background.js` + `content.js`) — Manifest V3 service worker that connects to the relay and executes commands in the active browser tab
- **CLI Client** — Any WebSocket client (Python, Node.js, etc.) that sends commands and receives structured responses

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔗 **WebSocket Bridge** | Bidirectional relay between CLI and browser |
| 🌐 **Tab Management** | Navigate, open new tabs, list all tabs |
| 🖱️ **DOM Interaction** | Click, type, scroll, extract text and HTML |
| 📊 **Command Logging** | In-extension log viewer with timestamps |
| 🔄 **Auto-Reconnect** | Intelligent reconnection with exponential backoff |
| 🎮 **Manual Controls** | Start / Stop / Connect buttons in popup UI |
| ⚡ **Manifest V3** | Modern extension architecture, no deprecated APIs |
| 🐍 **Python Server** | Async `websockets` library, clean and minimal |

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+** with `websockets` package
- **Chrome** or **Microsoft Edge** (Chromium-based)

### 1. Install dependencies

```bash
pip install websockets
```

### 2. Start the relay server

```bash
cd hermes-browser-extension
python server.py
```

The server starts on `ws://localhost:8765`.

### 3. Load the extension

1. Open `edge://extensions/` or `chrome://extensions/`
2. Enable **Developer mode**
3. Click **Load unpacked** → select the `hermes-browser-extension/` directory
4. Click the extension icon → click **Connect**

The status dot turns green when connected. ✅

### 4. Send commands

```python
import websocket, json, time

ws = websocket.create_connection('ws://localhost:8765', timeout=10)
ws.send(json.dumps({'type': 'cli'}))

def send_cmd(action, params=None, timeout=15):
    ws.send(json.dumps({'action': action, 'params': params or {}}))
    ws.settimeout(timeout)
    return json.loads(ws.recv())

# Navigate and read page content
send_cmd('navigate', {'url': 'https://example.com'})
time.sleep(3)
result = send_cmd('getText')
print(result.get('result', ''))

ws.close()
```

---

## 📦 Supported Commands

| Action | Parameters | Description |
|--------|-----------|-------------|
| `navigate` | `url`, `tabId?` | Navigate active tab to a URL |
| `newTab` | `url` | Open a new tab and return its ID |
| `getTabs` | — | List all open browser tabs |
| `click` | `selector?`, `x?`, `y?`, `tabId?` | Click by CSS selector or coordinates |
| `type` | `selector?`, `text`, `tabId?` | Type text into an element |
| `getText` | `selector?`, `tabId?` | Extract `innerText` of element or full page |
| `getDOM` | `tabId?` | Get full `outerHTML` of the page |
| `scroll` | `x?`, `y?`, `selector?`, `tabId?` | Scroll by pixels or scroll element into view |

---

## 🔧 Extension Controls

The popup UI provides three modes:

| Button | Behavior |
|--------|----------|
| **Connect** | Manually connect to the relay server |
| **Stop** | Disconnect AND disable auto-reconnect (server can be off) |
| **Start** | Re-enable auto-connect behavior |

The extension auto-connects on browser startup. Use **Stop** when you want it completely quiet.

---

## 🧪 Example: Multi-Tab Price Comparison

```python
import websocket, json, time

ws = websocket.create_connection('ws://localhost:8765', timeout=10)
ws.send(json.dumps({'type': 'cli'}))

def cmd(action, params=None):
    ws.send(json.dumps({'action': action, 'params': params or {}}))
    ws.settimeout(15)
    return json.loads(ws.recv())

# Open parallel search tabs
cmd('newTab', {'url': 'https://www.flipkart.com/search?q=samsung+under+30000'})
time.sleep(3)
cmd('newTab', {'url': 'https://www.flipkart.com/search?q=oppo+under+30000'})
time.sleep(3)

# Read results from each tab
tabs = cmd('getTabs').get('result', [])
for tab in tabs:
    if 'flipkart.com/search' in tab.get('url', ''):
        result = cmd('getText', {'tabId': tab['id']})
        print(f"--- {tab['url']} ---")
        print(result.get('result', '')[:2000])

ws.close()
```

---

## 📁 Project Structure

```
hermes-browser-extension/
├── manifest.json          # Manifest V3 extension config
├── background.js          # Service worker — WebSocket client + command handler
├── content.js             # Content script — visual highlighting
├── popup.html             # Extension popup UI (dark theme)
├── popup.js               # Popup logic — connection management + logs
├── server.py              # Python WebSocket relay server
├── start-server.sh        # Start the relay server (background)
├── stop-server.sh         # Stop the relay server
├── status-server.sh       # Check if the server is running
├── test_all.py            # Test suite
├── icons/                 # Extension icons (16, 48, 128px)
├── .gitignore
├── LICENSE                # MIT
└── README.md
```

---

## ⚠️ Pitfalls & Tips

| Issue | Solution |
|-------|----------|
| Extension won't load — `_` filename error | Delete `__pycache__/` from the extension directory |
| `ERR_CONNECTION_REFUSED` in console | Normal when server is off. Start it or click **Stop** to silence |
| `getText` returns stale content | Add `time.sleep(3-4)` after `navigate` for page load |
| Extension shows "Disconnected" | Click **Connect** in the popup, or restart the server |
| Service worker won't reload after edits | Manually reload from `edge://extensions/` — MV3 doesn't hot-reload |
| `websocket` import error in Python | Install: `pip install websockets` (not `websocket-client`) |

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 👤 Author

**Mayuresh** — [GitHub](https://github.com/mindfoldz0-spec) · [Email](mailto:mindfoldz0@gmail.com)
