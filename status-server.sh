#!/bin/bash
# Check status of Hermes Browser Extension relay server
# Usage: bash status-server.sh

echo "=== Hermes Browser Extension Status ==="
echo ""

# Check server
if netstat -an 2>/dev/null | grep -q ":8765.*LISTENING"; then
    PID=$(netstat -ano 2>/dev/null | grep ":8765.*LISTENING" | awk '{print $5}' | head -1)
    echo "✓ Relay Server: RUNNING (PID: $PID)"
    echo "  URL: ws://localhost:8765"
else
    echo "✗ Relay Server: STOPPED"
fi

echo ""

# Check extension connection (quick WebSocket test)
/c/Users/mayuresh/AppData/Local/Programs/Python/Python313/python.exe -c "
import websocket, json
try:
    ws = websocket.create_connection('ws://localhost:8765', timeout=3)
    ws.send(json.dumps({'type': 'cli'}))
    ws.send(json.dumps({'action': 'getTabs'}))
    ws.settimeout(3)
    r = json.loads(ws.recv())
    tabs = r.get('result', [])
    print(f'✓ Extension: CONNECTED ({len(tabs)} tabs open)')
    for t in tabs[:5]:
        print(f'  - {t[\"title\"][:40]} | {t[\"url\"][:40]}')
    ws.close()
except Exception as e:
    print(f'✗ Extension: NOT CONNECTED ({e})')
" 2>/dev/null || echo "✗ Extension: UNKNOWN (websocket-client not installed)"
