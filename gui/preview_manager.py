# gui/preview_manager.py
"""
Document Preview Manager

Handles live preview functionality for the SOP Builder.
Supports both full document preview and module-level preview.
"""

import customtkinter as ctk
import webbrowser
import tempfile
import threading
from pathlib import Path
from typing import Optional, List
import time
import tkinter as tk


class DocumentPreviewManager:
    """Manages document preview functionality"""

    def __init__(self, app_instance):
        self.app = app_instance
        self.preview_window: Optional[ctk.CTkToplevel] = None
        self.temp_html_path: Optional[Path] = None
        self.auto_refresh_enabled = False
        self.last_update_time = 0
        self.update_debounce_delay = 1.5  # seconds
        self.refresh_thread: Optional[threading.Thread] = None

    def toggle_live_preview(self):
        """Toggle the live preview window"""
        if self.preview_window and self.preview_window.winfo_exists():
            self.close_preview()
        else:
            self.open_preview()

    def open_preview(self):
        """Open live preview in external browser"""
        try:
            # Generate initial HTML
            self._generate_preview_html()

            # Open in browser
            if self.temp_html_path and self.temp_html_path.exists():
                webbrowser.open(f"file://{self.temp_html_path.absolute()}")

                # Enable auto-refresh
                self.auto_refresh_enabled = True
                self.app.main_window.set_status("Live preview opened - auto-refresh enabled", "green")

                # Start monitoring for changes
                self._start_change_monitoring()
            else:
                self.app.main_window.set_status("Failed to generate preview", "red")

        except Exception as e:
            print(f"Error opening preview: {e}")
            self.app.main_window.set_status("Error opening preview", "red")

    def close_preview(self):
        """Close live preview and cleanup"""
        self.auto_refresh_enabled = False

        # Clean up temp file
        if self.temp_html_path and self.temp_html_path.exists():
            try:
                self.temp_html_path.unlink()
            except:
                pass

        self.app.main_window.set_status("Live preview closed", "gray")

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
                embed_theme=False,     # Link to the original theme CSS file (faster)
                embed_media=False,     # Use file paths instead of base64 (FIXED!)
                embed_css_assets=False, # Don't embed CSS assets like fonts (faster)
                output_dir=None        # Signals to html_generator it's a preview
            )

            # Add auto-refresh meta tag
            auto_refresh_html = html_content.replace(
                '<head>',
                '<head>\n    <meta http-equiv="refresh" content="2">'
            )

            # Write to temp file
            with open(self.temp_html_path, 'w', encoding='utf-8') as f:
                f.write(auto_refresh_html)

            return True

        except Exception as e:
            print(f"Error generating preview HTML: {e}")
            return False

    def _start_change_monitoring(self):
        """Start monitoring for document changes"""

        def monitor_changes():
            while self.auto_refresh_enabled:
                try:
                    current_time = time.time()

                    # Check if document was modified recently
                    if (self.app.is_modified and
                            current_time - self.last_update_time > self.update_debounce_delay):

                        # Regenerate HTML
                        if self._generate_preview_html():
                            self.last_update_time = current_time
                            print("Preview updated")

                    time.sleep(0.5)  # Check every 500ms

                except Exception as e:
                    print(f"Error in change monitoring: {e}")
                    break

        # Start monitoring thread
        self.refresh_thread = threading.Thread(target=monitor_changes, daemon=True)
        self.refresh_thread.start()

    def request_preview_update(self):
        """Request a preview update (called when document changes)"""
        if self.auto_refresh_enabled:
            self.last_update_time = time.time()
