# utils/preview_server.py
import asyncio
import json
import threading
import time
from pathlib import Path
from typing import Set, Optional
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
import websockets
import socket
import logging

# Suppress websockets logging to reduce noise
logging.getLogger('websockets').setLevel(logging.WARNING)


class LivePreviewServer:
    """WebSocket-based live preview server for SOP Builder"""

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

        # Stop HTTP server
        if self.http_server:
            try:
                self.http_server.shutdown()
                self.http_server = None
                print("   ✅ HTTP server stopped")
            except Exception as e:
                print(f"   ⚠️ Error stopping HTTP server: {e}")

        # Stop WebSocket server and close connections
        if self.ws_loop and self.websocket_clients:
            try:
                # Schedule cleanup in the WebSocket event loop
                future = asyncio.run_coroutine_threadsafe(
                    self._cleanup_websockets(),
                    self.ws_loop
                )
                future.result(timeout=2.0)  # Wait up to 2 seconds
                print("   ✅ WebSocket connections closed")
            except Exception as e:
                print(f"   ⚠️ Error closing WebSocket connections: {e}")

        self.websocket_clients.clear()

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

                elif self.path.startswith('/Assets/') or self.path.startswith('/assets/'):
                    # Serve asset files
                    self._serve_asset_file()
                else:
                    self.send_error(404, "File not found")

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

        async def handle_client(websocket, path=None):  # ← Make path optional
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

    async def _cleanup_websockets(self):
        """Async method to properly close all WebSocket connections"""
        if not self.websocket_clients:
            return

        # Send goodbye message and close all connections
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
