#!/bin/bash
# Start the Hermes Browser Extension relay server in background
# Usage: bash start-server.sh

cd "$(dirname "$0")"

# Check if already running
if netstat -an 2>/dev/null | grep -q ":8765.*LISTENING"; then
    echo "✓ Relay server already running on port 8765"
    exit 0
fi

# Start server in background
nohup /c/Users/mayuresh/AppData/Local/Programs/Python/Python313/python.exe server.py > server.log 2>&1 &
SERVER_PID=$!

# Wait a moment and verify
sleep 2
if kill -0 $SERVER_PID 2>/dev/null; then
    echo "✓ Relay server started (PID: $SERVER_PID)"
    echo "✓ Listening on ws://localhost:8765"
    echo "✓ Logs: $(pwd)/server.log"
else
    echo "✗ Failed to start server. Check server.log"
    exit 1
fi
