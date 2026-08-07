import websocket
import json
import time

def send_cmd(ws, action, params={}, timeout=30):
    cmd = {"action": action, "params": params}
    ws.send(json.dumps(cmd))
    ws.settimeout(timeout)
    result = json.loads(ws.recv())
    return result

ws = websocket.create_connection("ws://localhost:8765", timeout=10)
ws.send(json.dumps({"type": "cli"}))
print("[OK] Registered as CLI\n")

# Navigate to a simple page
print("=" * 50)
print("TEST 1: Navigate to example.com")
r = send_cmd(ws, "navigate", {"url": "https://example.com"}, timeout=15)
print(f"  Result: {r}")
time.sleep(2)

# Get tabs
print("\n" + "=" * 50)
print("TEST 2: Get all tabs")
r = send_cmd(ws, "getTabs")
tabs = r.get("result", [])
print(f"  Found {len(tabs)} tab(s):")
for t in tabs:
    print(f"    - [{t.get('id')}] {t.get('title', 'N/A')[:50]} | {t.get('url', 'N/A')[:50]}")

# Get text
print("\n" + "=" * 50)
print("TEST 3: Get page text")
r = send_cmd(ws, "getText")
text = r.get("result", "")
if isinstance(text, str):
    print(f"  Text ({len(text)} chars): {text[:300]}")
else:
    print(f"  Result: {text}")

# Get DOM
print("\n" + "=" * 50)
print("TEST 4: Get DOM (first 300 chars)")
r = send_cmd(ws, "getDOM")
dom = r.get("result", "")
if isinstance(dom, str):
    print(f"  DOM: {dom[:300]}")
else:
    print(f"  Result: {dom}")

# Type into search (on example.com there's no input, so let's navigate to Flipkart)
print("\n" + "=" * 50)
print("TEST 5: Navigate to flipkart.com")
r = send_cmd(ws, "navigate", {"url": "https://www.flipkart.com"}, timeout=15)
print(f"  Result: {r}")
time.sleep(3)

# Get tabs again
print("\n" + "=" * 50)
print("TEST 6: Get all tabs")
r = send_cmd(ws, "getTabs")
tabs = r.get("result", [])
print(f"  Found {len(tabs)} tab(s):")
for t in tabs:
    print(f"    - [{t.get('id')}] {t.get('title', 'N/A')[:50]} | {t.get('url', 'N/A')[:50]}")

# Click search input
print("\n" + "=" * 50)
print("TEST 7: Click search input")
r = send_cmd(ws, "click", {"selector": "input[name='q']"}, timeout=15)
print(f"  Result: {r}")

# Type into search
print("\n" + "=" * 50)
print("TEST 8: Type 'laptop' into search")
r = send_cmd(ws, "type", {"selector": "input[name='q']", "text": "laptop"}, timeout=15)
print(f"  Result: {r}")

# Scroll
print("\n" + "=" * 50)
print("TEST 9: Scroll down 300px")
r = send_cmd(ws, "scroll", {"y": 300}, timeout=15)
print(f"  Result: {r}")

# Final get text
print("\n" + "=" * 50)
print("TEST 10: Get text after search")
r = send_cmd(ws, "getText", {}, timeout=15)
text = r.get("result", "")
if isinstance(text, str):
    print(f"  Text ({len(text)} chars): {text[:300]}")
else:
    print(f"  Result: {text}")

ws.close()
print("\n" + "=" * 50)
print("ALL TESTS COMPLETE")
