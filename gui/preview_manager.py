# gui/preview_manager.py - ENHANCED to handle user-selected files
"""
Document Preview Manager

Handles live preview functionality for the SOP Builder.
Supports both full document preview and module-level preview.
Now uses event-driven updates and properly handles user-selected files.
"""

import customtkinter as ctk
import webbrowser
import tempfile
import threading
from pathlib import Path
from typing import Optional, List
import time
import tkinter as tk
from utils.preview_server import LivePreviewServer


class DocumentPreviewManager:
    """Manages document preview functionality with event-driven updates and user file support"""

    def __init__(self, app_instance):
        self.app = app_instance
        self.preview_window: Optional[ctk.CTkToplevel] = None
        self.temp_html_path: Optional[Path] = None
        self.auto_refresh_enabled = False
        self.last_update_time = 0
        self.update_debounce_delay = 0.5  # Reduced for WebSocket
        self.pending_update_timer: Optional[threading.Timer] = None
        self.update_lock = threading.Lock()
        self.server_lock = threading.Lock()  # For WebSocket server operations

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

    def _register_user_files_with_server(self, modules: List) -> dict:
        """
        Register all user-selected files with the preview server

        Args:
            modules: List of modules to scan for user files

        Returns:
            Dictionary mapping original paths to HTTP URLs
        """
        if not self.preview_server.is_running:
            return {}

        # Collect all media references
        from utils.media_discovery import MediaDiscoveryService
        media_discovery = MediaDiscoveryService()
        discovered_media = media_discovery.discover_all_media(modules)

        path_mapping = {}

        for original_path, media_info in discovered_media.items():
            if media_info.exists and original_path:
                # Check if this is a user-selected file (not in assets folder)
                path_obj = Path(original_path)
                assets_folder = Path.cwd() / "assets"

                try:
                    # If the file is not in the assets folder, it's a user-selected file
                    path_obj.resolve().relative_to(assets_folder.resolve())
                    # If we get here, the file IS in the assets folder, so it's a project asset
                    # We'll let the regular asset serving handle this
                    continue
                except ValueError:
                    # File is NOT in the assets folder, so it's a user-selected file
                    # Register it with the preview server
                    http_url = self.preview_server.register_user_file(original_path)
                    path_mapping[original_path] = http_url
                    print(f"📎 Registered user file: {Path(original_path).name}")

        return path_mapping

    def _generate_websocket_html(self) -> str:
        """Generate HTML with embedded WebSocket client and proper file handling"""
        # First, register user-selected files with the preview server
        user_file_mapping = self._register_user_files_with_server(self.app.active_modules)

        # Generate base HTML content
        html_content = self.app.html_generator.generate_html(
            self.app.active_modules,
            title="SOP Live Preview",
            embed_theme=True,  # Embed CSS for better performance
            embed_media=False,  # Don't embed media, use HTTP URLs
            embed_css_assets=False,  # Don't embed CSS assets, use HTTP URLs
            output_dir=None
        )

        # Convert file URIs to appropriate HTTP URLs
        html_content = self._convert_file_uris_to_http_urls(html_content, user_file_mapping)

        # Inject WebSocket client
        websocket_script = self._get_websocket_client_script()

        # Insert before closing </body> tag
        html_content = html_content.replace(
            '</body>',
            f'{websocket_script}\n</body>'
        )

        return html_content

    def _convert_file_uris_to_http_urls(self, html_content: str, user_file_mapping: dict) -> str:
        """Convert file:// URIs to appropriate HTTP URLs"""
        import re
        import urllib.parse
        from pathlib import Path

        def replace_file_uri(match):
            file_uri = match.group(1)
            if file_uri.startswith('file:///'):
                try:
                    # Decode the file URI to get the actual path
                    decoded_path = urllib.parse.unquote(file_uri)
                    file_path_str = decoded_path.replace('file:///', '')

                    # Normalize the path
                    if file_path_str.startswith('/') and len(file_path_str) > 1 and file_path_str[1] == ':':
                        # Windows path like /C:/Users/... -> C:/Users/...
                        file_path_str = file_path_str[1:]

                    file_path = Path(file_path_str)

                    # Check if this file was registered as a user file
                    for original_path, http_url in user_file_mapping.items():
                        if Path(original_path).resolve() == file_path.resolve():
                            print(f"🔗 Converted user file: {file_path.name} -> HTTP URL")
                            return f'"{http_url}"'

                    # If not a user file, treat as project asset
                    filename = file_path.name
                    http_url = f"http://localhost:{self.preview_server.http_port}/assets/{filename}"
                    print(f"🔗 Converted asset: {filename} -> HTTP URL")
                    return f'"{http_url}"'

                except Exception as e:
                    print(f"⚠️ Failed to convert file URI: {file_uri} - {e}")
                    return match.group(0)

            return match.group(0)

        # Replace file:// URIs in src, href, and url() attributes
        patterns = [
            r'"(file://[^"]+)"',  # src="file://..." and href="file://..."
            r"'(file://[^']+)'",  # src='file://...' and href='file://...'
            r'url\((file://[^)]+)\)',  # url(file://...)
        ]

        for pattern in patterns:
            html_content = re.sub(pattern, replace_file_uri, html_content)

        return html_content

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

    def _generate_preview_html(self):
        """Generate HTML for preview using file paths instead of base64 embedding"""
        try:
            # Create temp file
            if not self.temp_html_path:
                temp_dir = Path(tempfile.gettempdir())
                self.temp_html_path = temp_dir / "sop_preview.html"

            # For Live Preview with FILE PATHS (no base64 embedding)
            html_content = self.app.html_generator.generate_html(
                self.app.active_modules,
                title="SOP Preview",
                embed_theme=False,  # Link to the original theme CSS file (faster)
                embed_media=False,  # Use file paths instead of base64 (FIXED!)
                embed_css_assets=False,  # Don't embed CSS assets like fonts (faster)
                output_dir=None  # Signals to html_generator it's a preview
            )

            # Add auto-refresh meta tag with longer interval since we're doing event-driven updates
            auto_refresh_html = html_content.replace(
                '<head>',
                '<head>\n    <meta http-equiv="refresh" content="4">'  # Increased from 2 to 5 seconds
            )

            # Write to temp file
            with open(self.temp_html_path, 'w', encoding='utf-8') as f:
                f.write(auto_refresh_html)

            print(f"Preview HTML updated at {time.strftime('%H:%M:%S')}")
            return True

        except Exception as e:
            print(f"Error generating preview HTML: {e}")
            return False

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

    def _perform_preview_update(self):
        """Perform the actual preview update (called by timer)"""
        try:
            with self.update_lock:
                self.pending_update_timer = None

            if self.auto_refresh_enabled and self._generate_preview_html():
                self.last_update_time = time.time()
                print("✅ Preview updated successfully")
            else:
                print("⚠️ Preview update skipped (disabled or failed)")

        except Exception as e:
            print(f"❌ Error updating preview: {e}")

    def force_preview_update(self):
        """Force an immediate preview update (bypass debouncing)"""
        if not self.auto_refresh_enabled:
            return

        # Cancel any pending updates
        with self.update_lock:
            if self.pending_update_timer:
                self.pending_update_timer.cancel()
                self.pending_update_timer = None

        # Perform immediate update
        self._perform_preview_update()

    def is_preview_active(self) -> bool:
        """Check if live preview is currently active"""
        return self.auto_refresh_enabled
