# gui/components/text_formatting_toolbar.py
"""
Text Formatting Toolbar Component

A reusable toolbar that provides formatting options for text fields.
Includes buttons for bullets, numbering, and bold text with helpful tooltips.
"""

import customtkinter as ctk
from typing import Callable, Optional, Dict, Any
import tkinter as tk


class TextFormattingToolbar:
    """A toolbar component that provides text formatting options"""

    def __init__(self, parent: ctk.CTkFrame, text_widget: ctk.CTkTextbox,
                 field_name: str, on_change_callback: Callable[[str, str], None]):
        """
        Initialize the formatting toolbar

        Args:
            parent: Parent frame to attach the toolbar to
            text_widget: The text widget this toolbar will control
            field_name: Name of the field (for callbacks)
            on_change_callback: Callback when text changes
        """
        self.parent = parent
        self.text_widget = text_widget
        self.field_name = field_name
        self.on_change_callback = on_change_callback

        # Create the toolbar
        self._create_toolbar()

    def _create_toolbar(self):
        """Create the toolbar with formatting buttons"""
        # Toolbar frame
        self.toolbar_frame = ctk.CTkFrame(
            self.parent,
            fg_color="transparent",
            height=30
        )
        self.toolbar_frame.pack(fill="x", pady=(0, 5))

        # Left side - formatting buttons
        buttons_frame = ctk.CTkFrame(self.toolbar_frame, fg_color="transparent")
        buttons_frame.pack(side="left", fill="x", expand=True)

        # Bullet button
        self.bullet_btn = self._create_format_button(
            buttons_frame,
            "• ",
            "Bullets",
            "Insert bullet point (•)\n\nExample:\n• First item\n• Second item\n• Third item"
        )

        # Number button
        self.number_btn = self._create_format_button(
            buttons_frame,
            "1.",
            "Numbers",
            "Insert numbered list\n\nExample:\n1. First step\n2. Second step\n3. Third step"
        )

        # Bold button
        self.bold_btn = self._create_format_button(
            buttons_frame,
            "B",
            "Bold",
            "Make text bold\n\nUsage: **text**\n\nExample:\nThis is **bold** text",
            font_style="bold"
        )

        # Separator
        separator = ctk.CTkLabel(
            buttons_frame,
            text="|",
            text_color="gray",
            width=20
        )
        separator.pack(side="left", padx=5)

        # Help icon with comprehensive tooltip
        help_label = ctk.CTkLabel(
            buttons_frame,
            text="ℹ️",
            font=("Arial", 14),
            cursor="question_arrow"
        )
        help_label.pack(side="left", padx=5)

        # Create comprehensive help tooltip
        self._create_help_tooltip(help_label)

    def _create_format_button(self, parent: ctk.CTkFrame, text: str,
                              tooltip_title: str, tooltip_text: str,
                              font_style: str = "normal") -> ctk.CTkButton:
        """Create a formatting button with tooltip"""
        # Determine font based on style
        if font_style == "bold":
            font = ("Arial", 11, "bold")
        else:
            font = ("Arial", 11)

        button = ctk.CTkButton(
            parent,
            text=text,
            width=35,
            height=25,
            font=font,
            fg_color="gray30",
            hover_color="gray40",
            command=lambda: self._insert_format(text)
        )
        button.pack(side="left", padx=2)

        # Create tooltip
        self._create_tooltip(button, tooltip_title, tooltip_text)

        return button

    def _insert_format(self, format_text: str):
        """Insert formatting at cursor position"""
        try:
            # Get current cursor position
            cursor_pos = self.text_widget.index("insert")

            if format_text == "B":  # Bold
                # Get selected text if any
                try:
                    sel_start = self.text_widget.index("sel.first")
                    sel_end = self.text_widget.index("sel.last")
                    selected_text = self.text_widget.get(sel_start, sel_end)

                    # Replace selection with bold formatted text
                    self.text_widget.delete(sel_start, sel_end)
                    self.text_widget.insert(sel_start, f"**{selected_text}**")
                except tk.TclError:
                    # No selection, just insert bold markers
                    self.text_widget.insert(cursor_pos, "**text**")
                    # Position cursor between the markers
                    new_pos = self.text_widget.index(f"{cursor_pos} + 2 chars")
                    self.text_widget.mark_set("insert", new_pos)
                    # Select "text" for easy replacement
                    self.text_widget.tag_add("sel", new_pos, f"{new_pos} + 4 chars")

            elif format_text == "• ":  # Bullet
                # Insert at beginning of current line
                line_start = cursor_pos.split('.')[0] + '.0'
                self.text_widget.insert(line_start, format_text)

            elif format_text == "1.":  # Number
                # Check if we're continuing a numbered list
                current_line = int(cursor_pos.split('.')[0])
                if current_line > 1:
                    # Check previous line for a number
                    prev_line_start = f"{current_line - 1}.0"
                    prev_line_end = f"{current_line - 1}.end"
                    prev_line_text = self.text_widget.get(prev_line_start, prev_line_end).strip()

                    # Extract number if present
                    if prev_line_text and prev_line_text[0].isdigit():
                        # Find the number
                        num_end = 0
                        for i, char in enumerate(prev_line_text):
                            if not char.isdigit():
                                num_end = i
                                break
                        if num_end > 0:
                            try:
                                prev_num = int(prev_line_text[:num_end])
                                format_text = f"{prev_num + 1}. "
                            except ValueError:
                                pass

                # Insert at beginning of current line
                line_start = cursor_pos.split('.')[0] + '.0'
                self.text_widget.insert(line_start, format_text)

            # Trigger the change callback
            new_content = self.text_widget.get("1.0", "end-1c")
            self.on_change_callback(self.field_name, new_content)

            # Focus back on text widget
            self.text_widget.focus_set()

        except Exception as e:
            print(f"Error inserting format: {e}")

    def _create_tooltip(self, widget: ctk.CTkBaseClass, title: str, text: str):
        """Create a tooltip for a widget"""
        tooltip = ToolTip(widget, title, text)

    def _create_help_tooltip(self, widget: ctk.CTkLabel):
        """Create comprehensive help tooltip"""
        help_text = """Formatting Guide

BULLETS:
• Use the bullet button or type "• " 
• Each line starting with "• " becomes a bullet point

NUMBERED LISTS:
1. Use the number button or type "1. ", "2. ", etc.
2. The number button auto-increments when continuing a list
3. Each numbered line becomes a list item

BOLD TEXT:
**text** becomes bold in the final output
Use the B button to wrap selected text or insert markers

TIPS:
- Click buttons to insert formatting at cursor position
- Select text first, then click B to make it bold
- Formatting is applied when HTML is generated"""

        tooltip = ToolTip(widget, "Text Formatting Help", help_text, width=350)


class ToolTip:
    """Custom tooltip implementation for CustomTkinter widgets"""

    def __init__(self, widget: ctk.CTkBaseClass, title: str, text: str, width: int = 250):
        self.widget = widget
        self.title = title
        self.text = text
        self.width = width
        self.tooltip_window = None
        self.show_delay = 500  # milliseconds
        self.hide_delay = 300  # milliseconds
        self.after_id = None
        self.hide_after_id = None

        # Bind events
        widget.bind("<Enter>", self._on_enter)
        widget.bind("<Leave>", self._on_leave)
        widget.bind("<Button-1>", self._on_click)

    def _on_enter(self, event):
        """Handle mouse entering widget"""
        # Cancel any pending hide
        if self.hide_after_id:
            self.widget.after_cancel(self.hide_after_id)
            self.hide_after_id = None

        # Schedule showing tooltip
        if not self.tooltip_window:
            self.after_id = self.widget.after(self.show_delay, self._show_tooltip)

    def _on_leave(self, event):
        """Handle mouse leaving widget"""
        # Cancel any pending show
        if self.after_id:
            self.widget.after_cancel(self.after_id)
            self.after_id = None

        # Schedule hiding tooltip
        if self.tooltip_window:
            self.hide_after_id = self.widget.after(self.hide_delay, self._hide_tooltip)

    def _on_click(self, event):
        """Hide tooltip on click"""
        self._hide_tooltip()

    def _show_tooltip(self):
        """Display the tooltip"""
        if self.tooltip_window or not self.widget.winfo_exists():
            return

        # Create tooltip window
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)

        # Configure appearance based on theme
        if ctk.get_appearance_mode() == "Dark":
            bg_color = "#2b2b2b"
            fg_color = "#ffffff"
            border_color = "#555555"
        else:
            bg_color = "#ffffe0"
            fg_color = "#000000"
            border_color = "#000000"

        self.tooltip_window.configure(bg=border_color)

        # Main frame with border effect
        main_frame = tk.Frame(
            self.tooltip_window,
            bg=bg_color,
            highlightthickness=0
        )
        main_frame.pack(padx=1, pady=1)

        # Title label
        if self.title:
            title_label = tk.Label(
                main_frame,
                text=self.title,
                font=("Arial", 11, "bold"),
                bg=bg_color,
                fg=fg_color,
                justify="left",
                wraplength=self.width
            )
            title_label.pack(anchor="w", padx=8, pady=(6, 2))

        # Content label
        content_label = tk.Label(
            main_frame,
            text=self.text,
            font=("Arial", 10),
            bg=bg_color,
            fg=fg_color,
            justify="left",
            wraplength=self.width
        )
        content_label.pack(anchor="w", padx=8, pady=(2, 6))

        # Position tooltip
        self._position_tooltip()

    def _position_tooltip(self):
        """Position tooltip near the widget"""
        if not self.tooltip_window:
            return

        # Update to get final size
        self.tooltip_window.update_idletasks()

        # Get widget position
        widget_x = self.widget.winfo_rootx()
        widget_y = self.widget.winfo_rooty()
        widget_height = self.widget.winfo_height()

        # Get tooltip size
        tooltip_width = self.tooltip_window.winfo_width()
        tooltip_height = self.tooltip_window.winfo_height()

        # Get screen size
        screen_width = self.widget.winfo_screenwidth()
        screen_height = self.widget.winfo_screenheight()

        # Calculate position (prefer below widget)
        x = widget_x
        y = widget_y + widget_height + 5

        # Adjust if tooltip would go off screen
        if x + tooltip_width > screen_width:
            x = screen_width - tooltip_width - 5

        if y + tooltip_height > screen_height:
            # Show above widget instead
            y = widget_y - tooltip_height - 5

        self.tooltip_window.geometry(f"+{x}+{y}")

    def _hide_tooltip(self):
        """Hide the tooltip"""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None