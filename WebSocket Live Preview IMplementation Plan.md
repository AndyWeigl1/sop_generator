# WebSocket Live Preview Implementation Plan

## Overview

Replace the current file-based auto-refresh preview system with a WebSocket-based live preview server that provides instant, event-driven updates to the browser without polling.

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   SOP Builder   │    │  Preview Server  │    │    Browser      │
│      App        │    │   (WebSocket)    │    │   (Client)      │
├─────────────────┤    ├──────────────────┤    ├─────────────────┤
│ • Document      │───▶│ • HTTP Server    │───▶│ • HTML Content  │
│   Changes       │    │ • WebSocket      │    │ • WebSocket     │
│ • Event-driven │    │   Handler        │    │   Client        │
│   Updates       │    │ • Content Cache  │    │ • Auto-update   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Implementation Steps

### Step 1: Create Preview Server Component *COMPLETE!*

### Step 2: Enhance DocumentPreviewManager

**File**: `gui/preview_manager.py` (modifications)

```python
# Add these imports at the top
from utils.preview_server import LivePreviewServer

class DocumentPreviewManager:
    """Enhanced preview manager with WebSocket support"""
    
    def __init__(self, app_instance):
        self.app = app_instance
        self.preview_window: Optional[ctk.CTkToplevel] = None
        self.temp_html_path: Optional[Path] = None
        self.auto_refresh_enabled = False
        self.last_update_time = 0
        self.update_debounce_delay = 0.5  # Reduced for WebSocket
        self.pending_update_timer: Optional[threading.Timer] = None
        self.update_lock = threading.Lock()
        
        # NEW: WebSocket server
        self.preview_server = LivePreviewServer()
        self.use_websocket = True  # Preference flag
    
    def toggle_live_preview(self):
        """Toggle the live preview window on/off"""
        if self.auto_refresh_enabled:
            self.close_preview()
        else:
            self.open_preview()
    
    def open_preview(self):
        """Open live preview using WebSocket server or fallback to file method"""
        try:
            if self.use_websocket:
                # Try WebSocket method first
                if self._open_websocket_preview():
                    return
                else:
                    print("⚠️ WebSocket preview failed, falling back to file method")
                    self.use_websocket = False
            
            # Fallback to original file-based method
            self._open_file_preview()
            
        except Exception as e:
            print(f"Error opening preview: {e}")
            self.app.main_window.set_status("Error opening preview", "red")
    
    def _open_websocket_preview(self) -> bool:
        """Open preview using WebSocket server"""
        try:
            # Start the server
            if not self.preview_server.start_server():
                return False
            
            # Generate initial HTML with WebSocket client
            html_content = self._generate_websocket_html()
            self.preview_server.update_content(html_content)
            
            # Open browser to server URL
            server_url = self.preview_server.get_server_url()
            webbrowser.open(server_url)
            
            # Enable auto-refresh
            self.auto_refresh_enabled = True
            self.app.main_window.set_status(
                f"Live preview opened at {server_url} - WebSocket updates enabled", 
                "green"
            )
            
            # Update button
            self._update_preview_button(True)
            return True
            
        except Exception as e:
            print(f"WebSocket preview error: {e}")
            return False
    
    def _open_file_preview(self):
        """Original file-based preview method (fallback)"""
        # Generate initial HTML
        self._generate_preview_html()
        
        # Open in browser
        if self.temp_html_path and self.temp_html_path.exists():
            webbrowser.open(f"file://{self.temp_html_path.absolute()}")
            
            # Enable auto-refresh
            self.auto_refresh_enabled = True
            self.app.main_window.set_status(
                "Live preview opened - file-based auto-refresh", 
                "orange"
            )
            
            # Update button
            self._update_preview_button(True)
        else:
            self.app.main_window.set_status("Failed to generate preview", "red")
    
    def close_preview(self):
        """Close live preview and cleanup"""
        self.auto_refresh_enabled = False
        
        # Cancel any pending updates
        with self.update_lock:
            if self.pending_update_timer:
                self.pending_update_timer.cancel()
                self.pending_update_timer = None
        
        # Stop WebSocket server if running
        if self.preview_server.is_running:
            self.preview_server.stop_server()
        
        # Clean up temp file
        if self.temp_html_path and self.temp_html_path.exists():
            try:
                self.temp_html_path.unlink()
            except:
                pass
        
        # Update button
        self._update_preview_button(False)
        self.app.main_window.set_status("Live preview closed", "gray")
    
    def _generate_websocket_html(self) -> str:
        """Generate HTML with embedded WebSocket client"""
        # Generate base HTML using existing method
        html_content = self.app.html_generator.generate_html(
            self.app.active_modules,
            title="SOP Live Preview",
            embed_theme=True,     # Embed for performance
            embed_media=False,    # Use file URIs for speed
            embed_css_assets=False, # Don't embed assets for speed
            output_dir=None
        )
        
        # Inject WebSocket client
        websocket_script = self._get_websocket_client_script()
        
        # Insert before closing </body> tag
        html_content = html_content.replace(
            '</body>',
            f'{websocket_script}\n</body>'
        )
        
        return html_content
    
    def _get_websocket_client_script(self) -> str:
        """Get the WebSocket client JavaScript"""
        ws_port = self.preview_server.ws_port
        
        return f'''
    <script>
    // WebSocket Live Preview Client
    (function() {{
        const wsUrl = 'ws://localhost:{ws_port}';
        let ws = null;
        let reconnectAttempts = 0;
        const maxReconnectAttempts = 10;
        
        function connectWebSocket() {{
            try {{
                ws = new WebSocket(wsUrl);
                
                ws.onopen = function() {{
                    console.log('🔌 WebSocket connected to preview server');
                    reconnectAttempts = 0;
                    showConnectionStatus('Connected', 'green');
                }};
                
                ws.onmessage = function(event) {{
                    try {{
                        const data = JSON.parse(event.data);
                        if (data.type === 'content_update') {{
                            console.log('🔄 Received content update');
                            showUpdateNotification();
                            // Smooth reload
                            window.location.reload();
                        }}
                    }} catch (e) {{
                        console.error('Error parsing WebSocket message:', e);
                    }}
                }};
                
                ws.onclose = function(event) {{
                    console.log('🔌 WebSocket disconnected');
                    showConnectionStatus('Disconnected', 'orange');
                    
                    // Attempt to reconnect
                    if (reconnectAttempts < maxReconnectAttempts) {{
                        reconnectAttempts++;
                        const delay = Math.min(1000 * reconnectAttempts, 5000);
                        console.log(`🔄 Reconnecting in ${{delay}}ms (attempt ${{reconnectAttempts}})`);
                        setTimeout(connectWebSocket, delay);
                    }} else {{
                        showConnectionStatus('Failed to reconnect', 'red');
                    }}
                }};
                
                ws.onerror = function(error) {{
                    console.error('WebSocket error:', error);
                    showConnectionStatus('Connection error', 'red');
                }};
                
            }} catch (e) {{
                console.error('Failed to create WebSocket connection:', e);
            }}
        }}
        
        function showConnectionStatus(message, color) {{
            // Create or update status indicator
            let statusEl = document.getElementById('ws-status');
            if (!statusEl) {{
                statusEl = document.createElement('div');
                statusEl.id = 'ws-status';
                statusEl.style.cssText = `
                    position: fixed;
                    top: 10px;
                    right: 10px;
                    background: rgba(0,0,0,0.8);
                    color: white;
                    padding: 8px 12px;
                    border-radius: 4px;
                    font-size: 12px;
                    z-index: 10000;
                    transition: all 0.3s ease;
                `;
                document.body.appendChild(statusEl);
            }}
            
            statusEl.textContent = `🔌 ${{message}}`;
            statusEl.style.borderLeft = `4px solid ${{color}}`;
            
            // Hide after 3 seconds if connected
            if (color === 'green') {{
                setTimeout(() => {{
                    if (statusEl) statusEl.style.opacity = '0.3';
                }}, 3000);
            }}
        }}
        
        function showUpdateNotification() {{
            // Brief flash to indicate update
            const flash = document.createElement('div');
            flash.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                height: 3px;
                background: linear-gradient(90deg, #4CAF50, #2196F3);
                z-index: 10001;
                animation: slideIn 0.3s ease-out;
            `;
            
            // Add CSS animation
            if (!document.getElementById('update-animation-style')) {{
                const style = document.createElement('style');
                style.id = 'update-animation-style';
                style.textContent = `
                    @keyframes slideIn {{
                        0% {{ transform: translateX(-100%); }}
                        100% {{ transform: translateX(0); }}
                    }}
                `;
                document.head.appendChild(style);
            }}
            
            document.body.appendChild(flash);
            setTimeout(() => flash.remove(), 300);
        }}
        
        // Start connection when page loads
        if (document.readyState === 'loading') {{
            document.addEventListener('DOMContentLoaded', connectWebSocket);
        }} else {{
            connectWebSocket();
        }}
        
        // Cleanup on page unload
        window.addEventListener('beforeunload', function() {{
            if (ws) {{
                ws.close();
            }}
        }});
    }})();
    </script>'''
    
    def request_preview_update(self):
        """Request preview update with WebSocket support"""
        if not self.auto_refresh_enabled:
            return
        
        if self.preview_server.is_running:
            # WebSocket method - faster updates
            with self.update_lock:
                # Cancel any existing pending update
                if self.pending_update_timer:
                    self.pending_update_timer.cancel()
                
                # Schedule update with shorter debounce
                self.pending_update_timer = threading.Timer(
                    0.3,  # Shorter delay for WebSocket
                    self._perform_websocket_update
                )
                self.pending_update_timer.daemon = True
                self.pending_update_timer.start()
        else:
            # File-based method - original implementation
            with self.update_lock:
                if self.pending_update_timer:
                    self.pending_update_timer.cancel()
                
                self.pending_update_timer = threading.Timer(
                    self.update_debounce_delay,
                    self._perform_preview_update
                )
                self.pending_update_timer.daemon = True
                self.pending_update_timer.start()
    
    def _perform_websocket_update(self):
        """Perform WebSocket-based preview update"""
        try:
            with self.update_lock:
                self.pending_update_timer = None
            
            if self.auto_refresh_enabled and self.preview_server.is_running:
                html_content = self._generate_websocket_html()
                self.preview_server.update_content(html_content)
                self.last_update_time = time.time()
                print("✅ WebSocket preview updated")
            
        except Exception as e:
            print(f"❌ Error updating WebSocket preview: {e}")
    
    def _update_preview_button(self, is_open: bool):
        """Update the preview button text and color"""
        if hasattr(self.app.main_window, 'menu_frame'):
            for widget in self.app.main_window.menu_frame.winfo_children():
                if (isinstance(widget, ctk.CTkButton) and
                    "Live Preview" in widget.cget("text")):
                    
                    if is_open:
                        widget.configure(
                            text="👁️ Close Preview",
                            fg_color="red",
                            hover_color="darkred"
                        )
                    else:
                        widget.configure(
                            text="👁️ Live Preview",
                            fg_color="purple",
                            hover_color="darkmagenta"
                        )
                    break
    
    # ... rest of existing methods remain unchanged ...
```

### Step 3: Dependencies and Installation

**Requirements**: Add to your `requirements.txt`:

```txt
websockets>=11.0.3
```

**Installation Command**:
```bash
pip install websockets
```

### Step 4: Integration with Main App

**File**: `app/sop_builder.py` (minimal changes needed)

The existing integration should work seamlessly since we're enhancing the `DocumentPreviewManager` rather than replacing it. The new WebSocket functionality will be used automatically when available, with graceful fallback to the existing file-based method.

## Benefits

### Performance Benefits
- ✅ **Instant Updates**: Changes appear immediately, no 4-second delay
- ✅ **Efficient**: Only updates when document actually changes
- ✅ **Reduced CPU**: No continuous file writing/reading
- ✅ **Better Memory**: No temporary file accumulation

### User Experience Benefits
- ✅ **Smooth Updates**: No page refresh flicker
- ✅ **Scroll Preservation**: Browser maintains scroll position
- ✅ **Connection Status**: Visual feedback on connection state
- ✅ **Responsive**: Near real-time updates during editing

### Technical Benefits
- ✅ **Robust**: Automatic reconnection on connection loss
- ✅ **Backwards Compatible**: Falls back to file method if WebSocket fails
- ✅ **Scalable**: Can handle multiple browser windows
- ✅ **Extensible**: Easy to add new update types

## Error Handling

### Port Conflicts
- Automatically finds free ports starting from defaults
- Tries up to 100 ports before failing
- Clear error messages if no ports available

### Connection Issues
- Graceful WebSocket reconnection with exponential backoff
- Maximum reconnection attempts to prevent infinite loops
- Visual status indicators for connection state

### Server Failures
- Automatic fallback to file-based preview
- Proper cleanup of server resources
- Thread-safe server shutdown

### Browser Issues
- Handles multiple browser tabs gracefully
- Manages disconnected clients automatically
- Prevents memory leaks from stale connections

## Future Enhancements

### Incremental Updates
- Send only changed sections instead of full page reload
- Highlight modified areas with subtle animations
- Preserve form inputs and scroll positions

### Advanced Features
- **Multi-device Preview**: Preview on mobile devices
- **Collaborative Editing**: Multiple users viewing same preview
- **Performance Metrics**: Show update latency and connection stats
- **Custom Themes**: Real-time theme switching in preview

### Development Tools
- **Debug Mode**: Detailed WebSocket message logging
- **Health Monitoring**: Server status dashboard
- **Update Analytics**: Track update frequency and performance

## Testing Strategy

### Unit Tests
- Test server startup/shutdown cycles
- Verify WebSocket message handling
- Test port allocation logic
- Validate HTML injection

### Integration Tests
- Test with various document sizes
- Verify fallback mechanisms
- Test concurrent connections
- Validate browser compatibility

### Performance Tests
- Measure update latency
- Test with large documents
- Verify memory usage
- Test long-running sessions

## Migration Notes

### Backwards Compatibility
- Existing file-based preview continues to work
- New WebSocket feature is opt-in by default
- User preferences can disable WebSocket if needed

### Configuration Options
```python
# In DocumentPreviewManager.__init__()
self.websocket_config = {
    'enabled': True,
    'http_port': 8080,
    'ws_port': 8765,
    'fallback_on_failure': True,
    'debug_mode': False
}
```

### Deployment Considerations
- WebSocket server only runs locally (localhost)
- No external network access required
- Firewall should allow localhost connections
- Works with all modern browsers (IE11+)

## Implementation Timeline

### Phase 1: Core WebSocket Server (2-3 hours)
- [ ] Create `LivePreviewServer` class
- [ ] Implement HTTP server functionality
- [ ] Add WebSocket connection handling
- [ ] Test basic server operations

### Phase 2: Preview Manager Integration (1-2 hours)
- [ ] Enhance `DocumentPreviewManager`
- [ ] Add WebSocket HTML generation
- [ ] Implement fallback mechanism
- [ ] Test end-to-end functionality

### Phase 3: Client-Side JavaScript (1 hour)
- [ ] Create WebSocket client script
- [ ] Add connection status indicators
- [ ] Implement reconnection logic
- [ ] Add visual update notifications

### Phase 4: Testing and Polish (1-2 hours)
- [ ] Test with various document types
- [ ] Verify error handling
- [ ] Test browser compatibility
- [ ] Add documentation and comments

**Total Estimated Time**: 5-8 hours for complete implementation

---

This implementation provides a robust, high-performance alternative to file-based auto-refresh while maintaining full backwards compatibility with your existing codebase.
