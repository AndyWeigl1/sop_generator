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
        """Generate HTML for preview"""
        try:
            # Create temp file
            if not self.temp_html_path:
                temp_dir = Path(tempfile.gettempdir())
                self.temp_html_path = temp_dir / "sop_preview.html"

            # Generate HTML with embedded CSS and auto-refresh
            html_content = self.app.html_generator.generate_html(
                self.app.active_modules,
                title="SOP Preview",
                embed_theme=True,  # Embed CSS for standalone preview
                embed_media=False  # Don't embed media for faster preview
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


class ModulePreviewPanel:
    """Panel showing live preview of selected module"""

    def __init__(self, parent_frame, app_instance):
        self.parent = parent_frame
        self.app = app_instance
        self.current_module = None

        # Create preview section
        self.preview_frame = ctk.CTkFrame(parent_frame, fg_color=("gray85", "gray25"))
        self.preview_content = None

        self._setup_preview_panel()

    def _setup_preview_panel(self):
        """Set up the module preview panel"""
        # Header
        header = ctk.CTkLabel(
            self.preview_frame,
            text="👁️ Module Preview",
            font=("Arial", 14, "bold")
        )
        header.pack(pady=(15, 10))

        # Preview content area
        self.preview_content = ctk.CTkScrollableFrame(
            self.preview_frame,
            height=200,
            fg_color=("gray90", "gray20")
        )
        self.preview_content.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # Initially hidden
        self.preview_frame.pack_forget()

    def show_module_preview(self, module):
        """Show preview for the given module"""
        self.current_module = module

        # Clear existing preview
        for widget in self.preview_content.winfo_children():
            widget.destroy()

        # Generate preview
        try:
            preview_widgets = self._convert_module_to_widgets(module)
            if preview_widgets:
                self.preview_frame.pack(fill="x", pady=(20, 0))
            else:
                self.preview_frame.pack_forget()

        except Exception as e:
            print(f"Error generating module preview: {e}")
            self.preview_frame.pack_forget()

    def hide_preview(self):
        """Hide the preview panel"""
        self.preview_frame.pack_forget()
        self.current_module = None

    def _convert_module_to_widgets(self, module) -> bool:
        """Convert module to tkinter widgets for preview"""
        try:
            # Get module HTML
            html_content = module.render_to_html()

            # Simple HTML to widgets conversion
            if module.module_type == 'text':
                return self._create_text_preview(module)
            elif module.module_type == 'media':
                return self._create_media_preview(module)
            elif module.module_type == 'table':
                return self._create_table_preview(module)
            elif module.module_type == 'disclaimer':
                return self._create_disclaimer_preview(module)
            elif module.module_type == 'section_title':
                return self._create_section_title_preview(module)
            else:
                # Generic preview
                return self._create_generic_preview(module)

        except Exception as e:
            print(f"Error creating widget preview: {e}")
            return False

    def _create_text_preview(self, module):
        """Create preview for text module"""
        content = module.content_data.get('content', '')
        header = module.content_data.get('header', '')

        if header:
            header_label = ctk.CTkLabel(
                self.preview_content,
                text=header,
                font=("Arial", 16, "bold"),
                anchor="w"
            )
            header_label.pack(fill="x", pady=(5, 10))

        # Simple text preview (could be enhanced to handle formatting)
        text_label = ctk.CTkLabel(
            self.preview_content,
            text=content[:300] + ("..." if len(content) > 300 else ""),
            font=("Arial", 12),
            anchor="nw",
            justify="left",
            wraplength=400
        )
        text_label.pack(fill="x", pady=5)

        return True

    def _create_media_preview(self, module):
        """Create preview for media module"""
        source = module.content_data.get('source', '')
        caption = module.content_data.get('caption', '')
        header = module.content_data.get('header', '')

        if header:
            header_label = ctk.CTkLabel(
                self.preview_content,
                text=f"🖼️ {header}",
                font=("Arial", 14, "bold"),
                anchor="w"
            )
            header_label.pack(fill="x", pady=(5, 5))

        # Media placeholder
        media_frame = ctk.CTkFrame(self.preview_content, height=100, fg_color="gray30")
        media_frame.pack(fill="x", pady=5)
        media_frame.pack_propagate(False)

        if source:
            source_label = ctk.CTkLabel(
                media_frame,
                text=f"📁 {Path(source).name}",
                font=("Arial", 11)
            )
            source_label.pack(expand=True)
        else:
            placeholder_label = ctk.CTkLabel(
                media_frame,
                text="No media source",
                font=("Arial", 11),
                text_color="gray"
            )
            placeholder_label.pack(expand=True)

        if caption:
            caption_label = ctk.CTkLabel(
                self.preview_content,
                text=caption,
                font=("Arial", 10),
                text_color="gray",
                wraplength=400
            )
            caption_label.pack(fill="x", pady=2)

        return True

    def _create_disclaimer_preview(self, module):
        """Create preview for disclaimer module"""
        title = module.content_data.get('title', '')
        content = module.content_data.get('content', '')
        disclaimer_type = module.content_data.get('type', 'warning')

        # Color mapping
        colors = {
            'warning': ('orange', 'darkorange'),
            'info': ('lightblue', 'blue'),
            'danger': ('red', 'darkred'),
            'success': ('lightgreen', 'green')
        }

        bg_color, border_color = colors.get(disclaimer_type, colors['warning'])

        disclaimer_frame = ctk.CTkFrame(
            self.preview_content,
            fg_color=bg_color,
            border_width=2,
            border_color=border_color
        )
        disclaimer_frame.pack(fill="x", pady=5)

        if title:
            title_label = ctk.CTkLabel(
                disclaimer_frame,
                text=f"⚠️ {title}",
                font=("Arial", 13, "bold"),
                text_color="black"
            )
            title_label.pack(pady=(10, 5), padx=10)

        content_label = ctk.CTkLabel(
            disclaimer_frame,
            text=content,
            font=("Arial", 11),
            text_color="black",
            wraplength=400,
            justify="left"
        )
        content_label.pack(pady=(0, 10), padx=10)

        return True

    def _create_section_title_preview(self, module):
        """Create preview for section title module"""
        title = module.content_data.get('title', '')
        subtitle = module.content_data.get('subtitle', '')
        size = module.content_data.get('size', 'large')

        # Font size mapping
        font_sizes = {'small': 14, 'medium': 16, 'large': 18}
        font_size = font_sizes.get(size, 16)

        title_label = ctk.CTkLabel(
            self.preview_content,
            text=f"🎯 {title}",
            font=("Arial", font_size, "bold"),
            anchor="w",
            text_color="blue"
        )
        title_label.pack(fill="x", pady=(10, 5))

        if subtitle:
            subtitle_label = ctk.CTkLabel(
                self.preview_content,
                text=subtitle,
                font=("Arial", 12),
                anchor="w",
                text_color="gray"
            )
            subtitle_label.pack(fill="x", pady=(0, 10))

        return True

    def _create_generic_preview(self, module):
        """Create generic preview for unsupported modules"""
        preview_label = ctk.CTkLabel(
            self.preview_content,
            text=f"Preview for {module.display_name}\n(Preview not yet implemented for this module type)",
            font=("Arial", 12),
            text_color="gray",
            justify="center"
        )
        preview_label.pack(expand=True, pady=20)

        return True

    def update_preview(self):
        """Update the current preview"""
        if self.current_module:
            self.show_module_preview(self.current_module)