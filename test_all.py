import websocket
import json
import time

def send_cmd(ws, action, params={}):
    cmd = {"action": action, "params": params}
    ws.send(json.dumps(cmd))
    result = json.loads(ws.recv())
    return result

ws = websocket.create_connection("ws://localhost:8765", timeout=10)
ws.send(json.dumps({"type": "cli"}))
print("[1] Registered as CLI\n")

# TEST 1: Navigate
print("=" * 50)
print("TEST 1: Navigate to flipkart.com")
r = send_cmd(ws, "navigate", {"url": "https://www.flipkart.com"})
print(f"  Result: {r}")
time.sleep(3)

# TEST 2: Get all tabs
print("\n" + "=" * 50)
print("TEST 2: Get all tabs")
r = send_cmd(ws, "getTabs")
tabs = r.get("result", [])
print(f"  Found {len(tabs)} tab(s):")
for t in tabs:
    print(f"    - [{t.get('id')}] {t.get('title', 'N/A')[:60]} | {t.get('url', 'N/A')[:60]}")

# TEST 3: Get page text
print("\n" + "=" * 50)
print("TEST 3: Get full page text (first 500 chars)")
r = send_cmd(ws, "getText")
text = r.get("result", "")
print(f"  Text: {str(text)[:500]}")

# TEST 4: Get DOM
print("\n" + "=" * 50)
print("TEST 4: Get DOM (first 500 chars)")
r = send_cmd(ws, "getDOM")
dom = r.get("result", "")
print(f"  DOM: {str(dom)[:500]}")

# TEST 5: Type into search
print("\n" + "=" * 50)
print("TEST 5: Type 'laptop' into search input")
r = send_cmd(ws, "click", {"selector": "input[name='q'], input[title='Search for Products, Brands and More'], .Pke_EE input, form input[type='text']"})
print(f"  Click result: {r}")
time.sleep(0.5)
r = send_cmd(ws, "type", {"selector": "input[name='q'], input[title='Search for Products, Brands and More'], .Pke_EE input, form input[type='text']", "text": "laptop"})
print(f"  Type result: {r}")
time.sleep(0.5)

# TEST 6: Click search button
print("\n" + "=" * 50)
print("TEST 6: Click search button")
r = send_cmd(ws, "click", {"selector": "button[type='submit'], .Pke_EE button, form button"})
print(f"  Click result: {r}")
time.sleep(3)

# TEST 7: Get text after search
print("\n" + "=" * 50)
print("TEST 7: Get page text after search (first 500 chars)")
r = send_cmd(ws, "getText")
text = r.get("result", "")
print(f"  Text: {str(text)[:500]}")

# TEST 8: Scroll down
print("\n" + "=" * 50)
print("TEST 8: Scroll down 500px")
r = send_cmd(ws, "scroll", {"y": 500})
print(f"  Scroll result: {r}")

# TEST 9: Scroll to element
print("\n" + "=" * 50)
print("TEST 9: Scroll to footer")
r = send_cmd(ws, "scroll", {"selector": "footer, [class*='footer'], [id*='footer']"})
print(f"  Scroll to element result: {r}")

ws.close()
print("\n" + "=" * 50)
print("ALL TESTS COMPLETE")
