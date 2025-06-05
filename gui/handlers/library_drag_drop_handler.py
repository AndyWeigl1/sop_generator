# gui/handlers/library_drag_drop_handler.py

import customtkinter as ctk
from typing import Optional, TYPE_CHECKING
import tkinter as tk
from gui.utils.widget_safety import safe_widget_exists, is_child_of

if TYPE_CHECKING:
    from gui.canvas_panel import CanvasPanel
    from modules.complex_module import TabModule


class LibraryDragDropHandler:
    """Handles drag and drop operations for modules from the library"""

    def __init__(self, canvas_panel: 'CanvasPanel', app_instance):
        self.canvas_panel = canvas_panel
        self.app = app_instance

        # Library drag drop state
        self.library_drop_highlight: Optional[ctk.CTkFrame] = None

    def setup_library_drop_zone(self):
        """Set up the canvas as a drop zone for library modules"""

        def on_canvas_enter(event):
            """Handle mouse entering canvas during library drag"""
            if self.app.main_window.is_dragging_from_library:
                self.highlight_canvas_as_drop_zone(True)

        def on_canvas_leave(event):
            """Handle mouse leaving canvas during library drag"""
            if self.app.main_window.is_dragging_from_library:
                self.highlight_canvas_as_drop_zone(False)

        def on_canvas_motion(event):
            """Handle mouse motion over canvas during library drag"""
            if self.app.main_window.is_dragging_from_library:
                # Provide more specific drop zone feedback
                self.update_library_drop_target(event.x_root, event.y_root)

        # Bind events to modules frame and parent
        self.canvas_panel.modules_frame.bind("<Enter>", on_canvas_enter)
        self.canvas_panel.modules_frame.bind("<Leave>", on_canvas_leave)
        self.canvas_panel.modules_frame.bind("<Motion>", on_canvas_motion)
        self.canvas_panel.parent.bind("<Enter>", on_canvas_enter)
        self.canvas_panel.parent.bind("<Leave>", on_canvas_leave)
        self.canvas_panel.parent.bind("<Motion>", on_canvas_motion)

        # Mark the canvas areas as drop zones for library detection
        self.canvas_panel.modules_frame._is_canvas_drop_zone = True
        self.canvas_panel.parent._is_canvas_drop_zone = True

    def highlight_canvas_as_drop_zone(self, highlight: bool):
        """Highlight the entire canvas as a drop zone"""
        if highlight:
            try:
                # Store original border settings if not already stored
                if not hasattr(self.canvas_panel.modules_frame, '_original_border_width'):
                    try:
                        self.canvas_panel.modules_frame._original_border_width = self.canvas_panel.modules_frame.cget('border_width')
                    except tk.TclError:
                        self.canvas_panel.modules_frame._original_border_width = 0

                if not hasattr(self.canvas_panel.modules_frame, '_original_border_color'):
                    try:
                        original_color = self.canvas_panel.modules_frame.cget('border_color')
                        self.canvas_panel.modules_frame._original_border_color = original_color if original_color else "gray"
                    except tk.TclError:
                        self.canvas_panel.modules_frame._original_border_color = "gray"

                if not hasattr(self.canvas_panel.parent, '_original_border_width'):
                    try:
                        self.canvas_panel.parent._original_border_width = self.canvas_panel.parent.cget('border_width')
                    except tk.TclError:
                        self.canvas_panel.parent._original_border_width = 0

                if not hasattr(self.canvas_panel.parent, '_original_border_color'):
                    try:
                        original_color = self.canvas_panel.parent.cget('border_color')
                        self.canvas_panel.parent._original_border_color = original_color if original_color else "gray"
                    except tk.TclError:
                        self.canvas_panel.parent._original_border_color = "gray"

                self.canvas_panel.modules_frame.configure(border_width=3, border_color="lightblue")
                self.canvas_panel.parent.configure(border_width=2, border_color="lightblue")
            except tk.TclError:
                pass
        else:
            try:
                # Restore original border settings
                original_width = getattr(self.canvas_panel.modules_frame, '_original_border_width', 0)
                original_color = getattr(self.canvas_panel.modules_frame, '_original_border_color', "gray")
                # Ensure we have valid values
                if original_color == '' or original_color is None:
                    original_color = "gray"
                self.canvas_panel.modules_frame.configure(border_width=original_width, border_color=original_color)

                original_width_parent = getattr(self.canvas_panel.parent, '_original_border_width', 0)
                original_color_parent = getattr(self.canvas_panel.parent, '_original_border_color', "gray")
                # Ensure we have valid values
                if original_color_parent == '' or original_color_parent is None:
                    original_color_parent = "gray"
                self.canvas_panel.parent.configure(border_width=original_width_parent, border_color=original_color_parent)
            except tk.TclError:
                pass

    def update_library_drop_target(self, x: int, y: int):
        """Update drop target highlighting during library drag"""
        try:
            widget_under_cursor = self.app.root.winfo_containing(x, y)

            # Clear previous library drop highlight
            if self.library_drop_highlight and safe_widget_exists(self.library_drop_highlight):
                try:
                    if hasattr(self.library_drop_highlight, '_original_library_color'):
                        self.library_drop_highlight.configure(
                            fg_color=self.library_drop_highlight._original_library_color)
                    else:
                        self.library_drop_highlight.configure(fg_color="gray15")
                    # Clear the stored original color
                    if hasattr(self.library_drop_highlight, '_original_library_color'):
                        delattr(self.library_drop_highlight, '_original_library_color')
                except tk.TclError:
                    pass
                self.library_drop_highlight = None

            # Find the appropriate drop zone
            drop_zone = self.find_library_drop_zone(widget_under_cursor)

            if drop_zone and safe_widget_exists(drop_zone):
                # Store original color and highlight
                if not hasattr(drop_zone, '_original_library_color'):
                    try:
                        original_color = drop_zone.cget('fg_color')
                        # Make sure we have a valid color (not None or empty)
                        if original_color and original_color != '':
                            drop_zone._original_library_color = original_color
                        else:
                            drop_zone._original_library_color = "gray15"
                    except tk.TclError:
                        drop_zone._original_library_color = "gray15"

                try:
                    drop_zone.configure(fg_color="lightgreen")
                    self.library_drop_highlight = drop_zone
                except tk.TclError:
                    pass

        except tk.TclError:
            pass

    def find_library_drop_zone(self, widget) -> Optional[ctk.CTkFrame]:
        """Find the appropriate drop zone for library modules"""
        current = widget

        while current:
            if not safe_widget_exists(current):
                try:
                    current = current.master
                    continue
                except (tk.TclError, AttributeError):
                    break

            # Check if this is the main modules frame (for main canvas drops)
            if current == self.canvas_panel.modules_frame:
                return current

            # Check if this is a tab content frame
            if hasattr(current, '_drop_zone_info'):
                return current

            # Check if this is a tab content container
            for tab_id, tab_containers in self.canvas_panel.tab_widgets.items():
                for tab_name, container in tab_containers.items():
                    if not safe_widget_exists(container):
                        continue
                    if current == container or is_child_of(current, container):
                        # Add drop zone info if not present
                        if not hasattr(current, '_drop_zone_info'):
                            # Find the tab module
                            for module in self.app.active_modules:
                                if hasattr(module, 'sub_modules') and module.id == tab_id:
                                    current._drop_zone_info = {
                                        'type': 'tab',
                                        'tab_module': module,
                                        'tab_name': tab_name
                                    }
                                    break
                        return current

            try:
                current = current.master
            except (tk.TclError, AttributeError):
                break

        return None

    def handle_library_drop(self, drop_target, module_type: str) -> bool:
        """Handle dropping a module from the library"""
        drop_zone = self.find_library_drop_zone(drop_target)

        # Clear any library drop highlighting first
        self.clear_library_drop_highlight()

        if not drop_zone:
            # If no specific drop zone found, check if we're generally over the canvas
            if (drop_target == self.canvas_panel.modules_frame or
                    drop_target == self.canvas_panel.parent or
                    is_child_of(drop_target, self.canvas_panel.modules_frame) or
                    is_child_of(drop_target, self.canvas_panel.parent)):
                # We're over the canvas area, so add to main canvas
                self.app.selected_tab_context = None  # Clear tab context
                self.app.add_module_to_canvas(module_type)
                return True
            return False

        # Determine where to add the module
        if hasattr(drop_zone, '_drop_zone_info'):
            # Dropping on a tab
            drop_info = drop_zone._drop_zone_info
            if drop_info['type'] == 'tab':
                # Set the tab context and add the module
                self.app.selected_tab_context = (drop_info['tab_module'], drop_info['tab_name'])
                self.app.add_module_to_canvas(module_type)
                return True
        elif (drop_zone == self.canvas_panel.modules_frame or
              hasattr(drop_zone, '_is_canvas_drop_zone')):
            # Dropping on main canvas
            self.app.selected_tab_context = None  # Clear tab context
            self.app.add_module_to_canvas(module_type)
            return True

        return False

    def clear_library_drop_highlight(self):
        """Clear library drop highlighting"""
        if self.library_drop_highlight and safe_widget_exists(self.library_drop_highlight):
            try:
                if hasattr(self.library_drop_highlight, '_original_library_color'):
                    original_color = self.library_drop_highlight._original_library_color
                    # Make sure we have a valid color
                    if original_color and original_color != '':
                        self.library_drop_highlight.configure(fg_color=original_color)
                    else:
                        self.library_drop_highlight.configure(fg_color="gray15")
                    # Clean up the stored color
                    delattr(self.library_drop_highlight, '_original_library_color')
                else:
                    self.library_drop_highlight.configure(fg_color="gray15")
            except (tk.TclError, AttributeError):
                pass
            self.library_drop_highlight = None

        # Also clear canvas highlighting
        self.highlight_canvas_as_drop_zone(False)

    def cleanup_on_canvas_clear(self):
        """Clean up library drag state when canvas is cleared"""
        self.clear_library_drop_highlight()
