# gui/preview_manager.py
"""
Document Preview Manager

Handles live preview functionality for the SOP Builder.
Supports both full document preview and module-level preview.
Now uses event-driven updates instead of continuous polling.
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
    """Manages document preview functionality with event-driven updates"""

    def __init__(self, app_instance):
        self.app = app_instance
        self.preview_window: Optional[ctk.CTkToplevel] = None
        self.temp_html_path: Optional[Path] = None
        self.auto_refresh_enabled = False
        self.last_update_time = 0
        self.update_debounce_delay = 1.0  # seconds (reduced from 1.5)
        self.pending_update_timer: Optional[threading.Timer] = None
        self.update_lock = threading.Lock()

    def toggle_live_preview(self):
        """Toggle the live preview window on/off"""
        if self.auto_refresh_enabled:
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
                self.app.main_window.set_status("Live preview opened - event-driven updates enabled", "green")

                # Update the button text to show it can be toggled off
                if hasattr(self.app.main_window, 'menu_frame'):
                    for widget in self.app.main_window.menu_frame.winfo_children():
                        if (isinstance(widget, ctk.CTkButton) and
                            widget.cget("text") == "👁️ Live Preview"):
                            widget.configure(text="👁️ Close Preview", fg_color="red", hover_color="darkred")
                            break

            else:
                self.app.main_window.set_status("Failed to generate preview", "red")

        except Exception as e:
            print(f"Error opening preview: {e}")
            self.app.main_window.set_status("Error opening preview", "red")

    def close_preview(self):
        """Close live preview and cleanup"""
        self.auto_refresh_enabled = False

        # Cancel any pending updates
        with self.update_lock:
            if self.pending_update_timer:
                self.pending_update_timer.cancel()
                self.pending_update_timer = None

        # Clean up temp file
        if self.temp_html_path and self.temp_html_path.exists():
            try:
                self.temp_html_path.unlink()
            except:
                pass

        # Update button text back to original
        if hasattr(self.app.main_window, 'menu_frame'):
            for widget in self.app.main_window.menu_frame.winfo_children():
                if (isinstance(widget, ctk.CTkButton) and
                    widget.cget("text") == "👁️ Close Preview"):
                    widget.configure(text="👁️ Live Preview", fg_color="purple", hover_color="darkmagenta")
                    break

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

            # Add auto-refresh meta tag with longer interval since we're doing event-driven updates
            auto_refresh_html = html_content.replace(
                '<head>',
                '<head>\n    <meta http-equiv="refresh" content="5">'  # Increased from 2 to 5 seconds
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
        """
        Request a preview update (called when document changes)
        Now uses debounced event-driven updates instead of polling
        """
        if not self.auto_refresh_enabled:
            return

        with self.update_lock:
            # Cancel any existing pending update
            if self.pending_update_timer:
                self.pending_update_timer.cancel()

            # Schedule a new update after the debounce delay
            self.pending_update_timer = threading.Timer(
                self.update_debounce_delay,
                self._perform_preview_update
            )
            self.pending_update_timer.daemon = True
            self.pending_update_timer.start()

            print(f"Preview update scheduled (debounce: {self.update_debounce_delay}s)")

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
