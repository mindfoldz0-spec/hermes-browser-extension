#!/bin/bash
# Stop the Hermes Browser Extension relay server
# Usage: bash stop-server.sh

# Find process on port 8765
PID=$(netstat -ano 2>/dev/null | grep ":8765.*LISTENING" | awk '{print $5}' | head -1)

if [ -z "$PID" ]; then
    echo "✓ No relay server running on port 8765"
    exit 0
fi

# Kill the process
taskkill /PID $PID /F 2>/dev/null || kill $PID 2>/dev/null

sleep 1

# Verify
if netstat -an 2>/dev/null | grep -q ":8765.*LISTENING"; then
    echo "✗ Failed to stop server (PID: $PID)"
    exit 1
else
    echo "✓ Relay server stopped (was PID: $PID)"
fi
