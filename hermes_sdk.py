#!/usr/bin/env python3
"""
Hermes Python SDK - Optimized Browser Automation Client

Features:
- Clean, intuitive API for browser automation
- Optimized DOM extraction (body-only by default)
- Screenshot support for AI vision models
- SPA handling with waitForSelector
- Command correlation with timeouts
"""

import json
import time
import websocket
from typing import Optional, Dict, Any, List
from contextlib import contextmanager


class HermesClient:
    """Python SDK for Hermes Browser Extension"""
    
    def __init__(self, ws_url: str = 'ws://localhost:8765', timeout: int = 15):
        """
        Initialize Hermes client
        
        Args:
            ws_url: WebSocket server URL (default: ws://localhost:8765)
            timeout: Default command timeout in seconds (default: 15)
        """
        self.ws_url = ws_url
        self.timeout = timeout
        self.ws = None
        self.request_id = 0
    
    def connect(self) -> 'HermesClient':
        """Connect to Hermes server and register as CLI client"""
        self.ws = websocket.create_connection(self.ws_url, timeout=self.timeout)
        self._send({'type': 'cli'})
        
        # Wait for connection acknowledgment
        response = json.loads(self.ws.recv())
        if response.get('action') != 'connected':
            raise RuntimeError(f"Unexpected connection response: {response}")
        
        return self
    
    def disconnect(self):
        """Disconnect from server"""
        if self.ws:
            self.ws.close()
            self.ws = None
    
    def _send(self, data: Dict[str, Any]):
        """Send JSON message to server"""
        if not self.ws:
            raise RuntimeError("Not connected. Call connect() first.")
        self.ws.send(json.dumps(data))
    
    def _request(self, action: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Send command and wait for response with timeout
        
        Args:
            action: Command action name
            params: Command parameters
            
        Returns:
            Response result dictionary
        """
        self.request_id += 1
        msg = {
            'action': action,
            'params': params or {},
            'request_id': self.request_id
        }
        
        self._send(msg)
        self.ws.settimeout(self.timeout)
        
        try:
            response = json.loads(self.ws.recv())
            
            if 'error' in response:
                raise RuntimeError(f"Command failed: {response['error']}")
            
            if response.get('request_id') != self.request_id:
                raise RuntimeError(f"Response ID mismatch: expected {self.request_id}, got {response.get('request_id')}")
            
            return response.get('result', {})
        except websocket.WebSocketTimeoutException:
            raise TimeoutError(f"Command '{action}' timed out after {self.timeout}s")
    
    # === Navigation Commands ===
    
    def navigate(self, url: str, tab_id: Optional[int] = None, 
                 wait_for_selector: Optional[str] = None, timeout: Optional[int] = None) -> Dict:
        """
        Navigate to URL with optional SPA support
        
        Args:
            url: Target URL
            tab_id: Specific tab ID (default: active tab)
            wait_for_selector: CSS selector to wait for after navigation
            timeout: Timeout for selector wait in ms (default: 5000)
            
        Returns:
            Dict with tabId and url
        """
        params = {'url': url}
        if tab_id:
            params['tabId'] = tab_id
        if wait_for_selector:
            params['waitForSelector'] = wait_for_selector
        if timeout:
            params['timeout'] = timeout
        
        return self._request('navigate', params)
    
    def new_tab(self, url: str = 'about:blank') -> Dict:
        """Open new tab and return tab ID"""
        return self._request('newTab', {'url': url})
    
    def get_tabs(self) -> List[Dict]:
        """Get list of all open tabs"""
        return self._request('getTabs')
    
    # === Interaction Commands ===
    
    def click(self, selector: Optional[str] = None, x: Optional[int] = None, 
              y: Optional[int] = None, tab_id: Optional[int] = None) -> Dict:
        """
        Click element by selector or coordinates
        
        Args:
            selector: CSS selector (alternative to x,y)
            x: X coordinate (alternative to selector)
            y: Y coordinate (alternative to selector)
            tab_id: Specific tab ID (default: active tab)
        """
        params = {}
        if selector:
            params['selector'] = selector
        if x is not None:
            params['x'] = x
        if y is not None:
            params['y'] = y
        if tab_id:
            params['tabId'] = tab_id
        
        return self._request('click', params)
    
    def type(self, selector: str, text: str, tab_id: Optional[int] = None) -> Dict:
        """Type text into input field"""
        params = {'selector': selector, 'text': text}
        if tab_id:
            params['tabId'] = tab_id
        return self._request('type', params)
    
    def scroll(self, x: Optional[int] = None, y: Optional[int] = None,
               selector: Optional[str] = None, tab_id: Optional[int] = None) -> Dict:
        """Scroll page or scroll element into view"""
        params = {}
        if x is not None:
            params['x'] = x
        if y is not None:
            params['y'] = y
        if selector:
            params['selector'] = selector
        if tab_id:
            params['tabId'] = tab_id
        return self._request('scroll', params)
    
    # === Data Extraction Commands ===
    
    def get_text(self, selector: Optional[str] = None, tab_id: Optional[int] = None) -> str:
        """
        Extract text content
        
        Args:
            selector: CSS selector (default: entire page body)
            tab_id: Specific tab ID
        """
        params = {}
        if selector:
            params['selector'] = selector
        if tab_id:
            params['tabId'] = tab_id
        return self._request('getText', params).get('text', '')
    
    def get_dom(self, tab_id: Optional[int] = None, full: bool = False) -> str:
        """
        Extract HTML content
        
        Args:
            tab_id: Specific tab ID
            full: If True, return full document; if False (default), return only body.innerHTML
                  This optimization reduces payload size by ~40-50%
        """
        params = {'full': full}
        if tab_id:
            params['tabId'] = tab_id
        return self._request('getDOM', params).get('html', '')
    
    def screenshot(self, tab_id: Optional[int] = None, format: str = 'jpeg', 
                   quality: int = 80) -> str:
        """
        Capture screenshot (NEW FEATURE)
        
        Args:
            tab_id: Specific tab ID (note: tab must be visible)
            format: Image format ('jpeg' or 'png')
            quality: JPEG quality 0-100 (default: 80)
            
        Returns:
            Base64 encoded image data URL
        """
        params = {'format': format, 'quality': quality}
        if tab_id:
            params['tabId'] = tab_id
        return self._request('screenshot', params).get('image', '')
    
    # === Timing & SPA Commands ===
    
    def wait(self, ms: int = 1000) -> Dict:
        """Simple delay (NEW FEATURE)"""
        return self._request('wait', {'ms': ms})
    
    def wait_for_selector(self, selector: str, tab_id: Optional[int] = None, 
                          timeout: int = 5000) -> Dict:
        """
        Wait for element to appear (NEW FEATURE - SPA support)
        
        Args:
            selector: CSS selector to wait for
            tab_id: Specific tab ID
            timeout: Timeout in milliseconds (default: 5000)
        """
        params = {'selector': selector, 'timeout': timeout}
        if tab_id:
            params['tabId'] = tab_id
        return self._request('waitForSelector', params)
    
    def highlight(self, selector: str, tab_id: Optional[int] = None,
                  duration: int = 2000, color: str = '#00ff88') -> Dict:
        """
        Highlight element for visual feedback (NEW FEATURE)
        
        Args:
            selector: CSS selector to highlight
            tab_id: Specific tab ID
            duration: Highlight duration in ms (default: 2000)
            color: Highlight color (default: '#00ff88')
        """
        params = {'selector': selector, 'duration': duration, 'color': color}
        if tab_id:
            params['tabId'] = tab_id
        return self._request('highlight', params)
    
    @contextmanager
    def implicit_wait(self, ms: int):
        """Context manager for implicit waits"""
        try:
            yield
        finally:
            self.wait(ms)


# === Convenience Functions ===

def connect(ws_url: str = 'ws://localhost:8765', timeout: int = 15) -> HermesClient:
    """Quick connect helper"""
    return HermesClient(ws_url, timeout).connect()


if __name__ == '__main__':
    # Example usage
    print("Hermes Python SDK - Demo")
    print("=" * 40)
    
    client = HermesClient().connect()
    
    try:
        # Navigate with SPA support
        print("\n1. Navigating to example.com...")
        client.navigate('https://example.com')
        client.wait(2000)
        
        # Get optimized DOM (body only)
        print("\n2. Getting optimized DOM (body only)...")
        dom = client.get_dom()
        print(f"   DOM length: {len(dom)} chars")
        
        # Get full DOM if needed
        print("\n3. Getting full DOM...")
        full_dom = client.get_dom(full=True)
        print(f"   Full DOM length: {len(full_dom)} chars")
        
        # Take screenshot
        print("\n4. Taking screenshot...")
        screenshot = client.screenshot(format='jpeg', quality=90)
        print(f"   Screenshot length: {len(screenshot)} chars (Base64)")
        
        # Wait for specific element (SPA support)
        print("\n5. Testing waitForSelector...")
        try:
            client.wait_for_selector('h1', timeout=3000)
            print("   ✓ Found h1 element")
        except RuntimeError as e:
            print(f"   ✗ {e}")
        
        # Highlight element
        print("\n6. Highlighting h1 element...")
        client.highlight('h1', duration=2000, color='#00ff88')
        
        # Get text
        print("\n7. Extracting text...")
        text = client.get_text()
        print(f"   Page text preview: {text[:100]}...")
        
        # List tabs
        print("\n8. Listing tabs...")
        tabs = client.get_tabs()
        for tab in tabs:
            print(f"   - Tab {tab['id']}: {tab['title']}")
        
        print("\n✓ All commands executed successfully!")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
    finally:
        client.disconnect()
        print("\nDisconnected.")
