# utils/preview_server.py - ENHANCED to serve user-selected files
import asyncio
import json
import threading
import time
from pathlib import Path
from typing import Set, Optional, Dict
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
import websockets
import socket
import logging
import urllib.parse
import mimetypes

# Suppress websockets logging to reduce noise
logging.getLogger('websockets').setLevel(logging.WARNING)


class LivePreviewServer:
    """WebSocket-based live preview server for SOP Builder with user file support"""

    def __init__(self, http_port: int = 8080, ws_port: int = 8765):
        self.http_port = http_port
        self.ws_port = ws_port
        self.current_html = ""
        self.websocket_clients: Set = set()
        self.http_server = None
        self.ws_server = None
        self.server_thread = None
        self.ws_thread = None
        self.ws_loop = None
        self.is_running = False

        # NEW: Track user-selected files and their original paths
        self.user_file_mappings: Dict[str, str] = {}  # filename -> original_path

    def register_user_file(self, original_path: str) -> str:
        """
        Register a user-selected file and return the HTTP URL to access it

        Args:
            original_path: The original file path selected by the user

        Returns:
            HTTP URL that can be used to access the file through the preview server
        """
        if not original_path or not Path(original_path).exists():
            return original_path  # Return as-is if invalid

        # Get the filename
        filename = Path(original_path).name

        # Store the mapping
        self.user_file_mappings[filename] = original_path

        # Return the HTTP URL
        http_url = f"http://localhost:{self.http_port}/user-files/{filename}"
        print(f"📎 Registered user file: {filename} -> {http_url}")
        return http_url

    def start_server(self) -> bool:
        """Start both HTTP and WebSocket servers"""
        try:
            # Find available ports
            self.http_port = self._find_free_port(self.http_port)
            self.ws_port = self._find_free_port(self.ws_port)

            print(f"🚀 Starting preview server on ports HTTP:{self.http_port}, WS:{self.ws_port}")

            # Start HTTP server in separate thread
            self.server_thread = threading.Thread(
                target=self._start_http_server,
                daemon=True
            )
            self.server_thread.start()

            # Start WebSocket server in separate thread
            self.ws_thread = threading.Thread(
                target=self._start_websocket_server,
                daemon=True
            )
            self.ws_thread.start()

            # Wait a moment for servers to start
            time.sleep(1.0)
            self.is_running = True
            print(f"✅ Preview server started at http://localhost:{self.http_port}")
            return True

        except Exception as e:
            print(f"❌ Failed to start preview server: {e}")
            return False

    def stop_server(self):
        """Stop both servers"""
        print("🛑 Stopping preview server...")
        self.is_running = False

        # Clear user file mappings
        self.user_file_mappings.clear()

        # Stop HTTP server
        if self.http_server:
            try:
                self.http_server.shutdown()
                self.http_server = None
                print("   ✅ HTTP server stopped")
            except Exception as e:
                print(f"   ⚠️ Error stopping HTTP server: {e}")

        # Stop WebSocket server and close connections
        if self.ws_loop:
            try:
                # Schedule cleanup and server shutdown in the WebSocket event loop
                future = asyncio.run_coroutine_threadsafe(
                    self._cleanup_and_shutdown_websockets(),
                    self.ws_loop
                )
                future.result(timeout=3.0)  # Wait up to 3 seconds
                print("   ✅ WebSocket server stopped")
            except Exception as e:
                print(f"   ⚠️ Error stopping WebSocket server: {e}")

        self.websocket_clients.clear()

    async def _cleanup_and_shutdown_websockets(self):
        """Async method to properly close all WebSocket connections and stop the server"""
        # First, close all existing connections
        if self.websocket_clients:
            tasks = []
            for client in self.websocket_clients.copy():
                try:
                    # Send goodbye message
                    await client.send(json.dumps({
                        'type': 'server_shutdown',
                        'timestamp': time.time()
                    }))
                    # Close the connection
                    tasks.append(client.close())
                except Exception:
                    pass  # Client might already be disconnected

            # Wait for all connections to close
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

        self.websocket_clients.clear()

        # Now stop the WebSocket server itself
        if self.ws_server:
            try:
                self.ws_server.close()
                await self.ws_server.wait_closed()
                self.ws_server = None
            except Exception as e:
                print(f"   ⚠️ Error closing WebSocket server: {e}")

    def update_content(self, html_content: str):
        """Update cached content and broadcast to clients"""
        self.current_html = html_content
        if self.websocket_clients and self.ws_loop:
            try:
                # Schedule the broadcast in the WebSocket event loop
                asyncio.run_coroutine_threadsafe(
                    self._async_broadcast_update("content_update"),
                    self.ws_loop
                )
                print(f"📡 Broadcasted update to {len(self.websocket_clients)} clients")
            except Exception as e:
                print(f"❌ Error broadcasting update: {e}")

    def get_server_url(self) -> str:
        """Get the HTTP server URL"""
        return f"http://localhost:{self.http_port}"

    def _find_free_port(self, start_port: int) -> int:
        """Find an available port starting from start_port"""
        for port in range(start_port, start_port + 100):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('localhost', port))
                    return port
            except OSError:
                continue
        raise RuntimeError("No free ports available")

    def _start_http_server(self):
        """Start the HTTP server"""
        import mimetypes
        import urllib.parse
        import os

        class PreviewHandler(SimpleHTTPRequestHandler):
            def __init__(self, server_instance, *args, **kwargs):
                self.server_instance = server_instance
                super().__init__(*args, **kwargs)

            def do_GET(self):
                if self.path == '/' or self.path == '/index.html':
                    # Serve the main HTML content
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                    self.send_header('Pragma', 'no-cache')
                    self.send_header('Expires', '0')
                    self.end_headers()

                    html_content = self.server_instance.current_html or "<html><body><h1>Preview Loading...</h1></body></html>"
                    self.wfile.write(html_content.encode('utf-8'))

                elif self.path.startswith('/user-files/'):
                    # NEW: Serve user-selected files
                    self._serve_user_file()

                elif self.path.startswith('/Assets/') or self.path.startswith('/assets/'):
                    # Serve asset files
                    self._serve_asset_file()
                else:
                    self.send_error(404, "File not found")

            def _serve_user_file(self):
                """Serve user-selected files from their original locations"""
                try:
                    # Extract filename from path like /user-files/image.jpg
                    filename = self.path.split('/user-files/')[-1]
                    filename = urllib.parse.unquote(filename)

                    # Look up the original path
                    original_path = self.server_instance.user_file_mappings.get(filename)

                    if not original_path:
                        print(f"❌ User file not found in mappings: {filename}")
                        self.send_error(404, f"User file not found: {filename}")
                        return

                    file_path = Path(original_path)

                    if not file_path.exists():
                        print(f"❌ User file no longer exists: {original_path}")
                        self.send_error(404, f"User file no longer exists: {filename}")
                        return

                    # Determine content type
                    content_type, _ = mimetypes.guess_type(str(file_path))
                    if not content_type:
                        content_type = 'application/octet-stream'

                    # Send file
                    self.send_response(200)
                    self.send_header('Content-type', content_type)
                    self.send_header('Content-Length', str(file_path.stat().st_size))
                    self.send_header('Cache-Control', 'public, max-age=3600')  # Cache for 1 hour
                    self.end_headers()

                    with open(file_path, 'rb') as f:
                        self.wfile.write(f.read())

                    print(f"📎 Served user file: {filename} from {original_path}")

                except Exception as e:
                    print(f"❌ Error serving user file {self.path}: {e}")
                    self.send_error(500, f"Error serving user file: {str(e)}")

            def _serve_asset_file(self):
                """Serve asset files from the assets directory"""
                try:
                    # Clean the path and remove leading slash
                    clean_path = urllib.parse.unquote(self.path.lstrip('/'))

                    # Try multiple possible asset locations
                    possible_paths = [
                        Path.cwd() / clean_path,  # ./assets/file.ext
                        Path.cwd() / clean_path.lower(),  # ./assets/file.ext (lowercase)
                        Path.cwd() / "assets" / Path(clean_path).name,  # ./assets/filename only
                        Path.cwd() / "assets" / Path(clean_path).name.lower(),  # ./assets/filename (lowercase)
                    ]

                    asset_path = None
                    for possible_path in possible_paths:
                        if possible_path.exists() and possible_path.is_file():
                            asset_path = possible_path
                            break

                    if not asset_path:
                        # Try case-insensitive search in assets folder
                        assets_folder = Path.cwd() / "assets"
                        if assets_folder.exists():
                            target_name = Path(clean_path).name.lower()
                            for asset_file in assets_folder.iterdir():
                                if asset_file.is_file() and asset_file.name.lower() == target_name:
                                    asset_path = asset_file
                                    break

                    if asset_path and asset_path.exists():
                        # Determine content type
                        content_type, _ = mimetypes.guess_type(str(asset_path))
                        if not content_type:
                            content_type = 'application/octet-stream'

                        # Send file
                        self.send_response(200)
                        self.send_header('Content-type', content_type)
                        self.send_header('Content-Length', str(asset_path.stat().st_size))
                        self.send_header('Cache-Control', 'public, max-age=3600')  # Cache for 1 hour
                        self.end_headers()

                        with open(asset_path, 'rb') as f:
                            self.wfile.write(f.read())

                        print(f"📁 Served asset: {clean_path} -> {asset_path.name}")
                    else:
                        print(f"❌ Asset not found: {clean_path}")
                        self.send_error(404, f"Asset not found: {clean_path}")

                except Exception as e:
                    print(f"❌ Error serving asset {self.path}: {e}")
                    self.send_error(500, f"Error serving asset: {str(e)}")

            def log_message(self, format, *args):
                # Suppress HTTP server logs to reduce noise, except for errors
                if "Error" in format or "404" in format:
                    print(f"🌐 HTTP: {format % args}")

        # Create handler with server instance reference
        def handler_factory(*args, **kwargs):
            return PreviewHandler(self, *args, **kwargs)

        try:
            self.http_server = HTTPServer(('localhost', self.http_port), handler_factory)
            print(f"   🌐 HTTP server listening on port {self.http_port}")
            self.http_server.serve_forever()
        except Exception as e:
            print(f"❌ HTTP Server error: {e}")

    def _start_websocket_server(self):
        """Start the WebSocket server"""

        async def handle_client(websocket, path=None):
            """Handle WebSocket client connections with proper shutdown checking"""
            # Check if server is still running before accepting connection
            if not self.is_running:
                try:
                    await websocket.close()
                except:
                    pass
                return

            print(f"🔌 WebSocket client connected from {websocket.remote_address}")
            self.websocket_clients.add(websocket)
            try:
                # Send initial connection confirmation
                await websocket.send(json.dumps({
                    'type': 'connection_confirmed',
                    'timestamp': time.time(),
                    'path': path or getattr(websocket, 'path', '/')
                }))

                # Wait for the connection to close
                await websocket.wait_closed()
            except websockets.exceptions.ConnectionClosed:
                pass
            except Exception as e:
                print(f"⚠️ WebSocket client error: {e}")
            finally:
                self.websocket_clients.discard(websocket)
                print(f"🔌 WebSocket client disconnected")

        async def run_server():
            try:
                print(f"   🔌 WebSocket server starting on port {self.ws_port}")
                self.ws_server = await websockets.serve(
                    handle_client,
                    'localhost',
                    self.ws_port,
                    ping_interval=20,  # Send ping every 20 seconds
                    ping_timeout=10  # Wait 10 seconds for pong
                )
                print(f"   🔌 WebSocket server listening on port {self.ws_port}")
                await self.ws_server.wait_closed()
            except Exception as e:
                print(f"❌ WebSocket Server error: {e}")

        # Create new event loop for this thread
        try:
            self.ws_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.ws_loop)
            self.ws_loop.run_until_complete(run_server())
        except Exception as e:
            print(f"❌ Failed to start WebSocket server: {e}")
        finally:
            if self.ws_loop:
                self.ws_loop.close()

    async def _async_broadcast_update(self, update_type: str):
        """Async method to broadcast updates to all connected clients"""
        if not self.websocket_clients:
            return

        message = json.dumps({
            'type': update_type,
            'timestamp': time.time()
        })

        # Send to all clients and remove disconnected ones
        disconnected_clients = set()
        for client in self.websocket_clients.copy():
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(client)
            except Exception as e:
                print(f"⚠️ Error sending to client: {e}")
                disconnected_clients.add(client)

        # Remove disconnected clients
        self.websocket_clients -= disconnected_clients

        if disconnected_clients:
            print(f"🔌 Removed {len(disconnected_clients)} disconnected clients")
