# gui/renderers/module_widget_manager.py
"""
Module Widget Manager

Handles the creation, management, and lifecycle of individual module widgets on the canvas.
This includes creating visual representations, managing widget state, and handling module-specific
UI interactions like selection and previews.
"""

import customtkinter as ctk
from typing import Dict, Optional, Tuple, TYPE_CHECKING
import tkinter as tk
import os

if TYPE_CHECKING:
    from modules.base_module import Module
    from modules.complex_module import TabModule


class ModuleWidgetManager:
    """Manages the creation and lifecycle of individual module widgets"""

    def __init__(self, modules_frame: ctk.CTkFrame, app_instance, drag_drop_handler,
                 safe_widget_exists_func, safe_destroy_widget_func):
        """
        Initialize the module widget manager

        Args:
            modules_frame: The main container frame for modules
            app_instance: Reference to the main application
            drag_drop_handler: Handler for drag and drop operations
            safe_widget_exists_func: Function to safely check widget existence
            safe_destroy_widget_func: Function to safely destroy widgets
        """
        self.modules_frame = modules_frame
        self.app = app_instance
        self.drag_drop_handler = drag_drop_handler
        self._safe_widget_exists = safe_widget_exists_func
        self._safe_destroy_widget = safe_destroy_widget_func

        # Widget tracking
        self.module_widgets: Dict[str, ctk.CTkFrame] = {}
        self.selected_widget: Optional[ctk.CTkFrame] = None

    def add_module_widget(self, module: 'Module', with_nested: bool = False):
        """Add visual representation of module"""
        # Create main module frame
        module_frame = self.create_module_frame(module, is_top_level=True)
        module_frame.pack(fill="x", padx=5, pady=5)

        # Store reference
        self.module_widgets[module.id] = module_frame

        # If it's a TabModule, let the canvas panel handle tab content creation
        if hasattr(module, 'sub_modules'):  # Check if it's a TabModule
            # This will be handled by the tab widget manager in the future
            # For now, we'll let the canvas panel handle this
            pass

        # Make frame draggable using the drag drop handler
        self.drag_drop_handler.enable_drag_drop(module_frame, module)

    def create_module_frame(self, module: 'Module', is_top_level: bool = True,
                            parent_tab: Optional[Tuple['TabModule', str]] = None,
                            parent_widget: Optional[ctk.CTkFrame] = None) -> ctk.CTkFrame:
        """Create a frame for a module"""
        # Use different styling for nested modules
        frame_color = "gray15" if is_top_level else "gray18"
        border_color = "gray15" if is_top_level else "gray20"

        # Determine parent widget
        if parent_widget is not None:
            target_parent = parent_widget
        else:
            target_parent = self.modules_frame

        module_frame = ctk.CTkFrame(
            target_parent,
            fg_color=frame_color,
            border_width=2,
            border_color=border_color
        )

        # Store module reference in the frame
        module_frame._module = module
        module_frame._parent_tab = parent_tab

        # Create header with module type and controls
        header_frame = ctk.CTkFrame(module_frame, fg_color="gray20", height=30)
        header_frame.pack(fill="x", padx=2, pady=2)
        header_frame.pack_propagate(False)

        # Add drag handle with safer event binding
        drag_handle = ctk.CTkLabel(
            header_frame,
            text="⋮⋮",
            font=("Arial", 16, "bold"),
            text_color="white",
            width=30,
            height=25,
            fg_color="gray30",
            corner_radius=3
        )
        drag_handle.pack(side="left", padx=(5, 5), pady=2)

        # Store reference to drag handle for easy access
        module_frame._drag_handle = drag_handle

        # Add indentation for nested modules
        if not is_top_level:
            indent_label = ctk.CTkLabel(header_frame, text=" →", text_color="gray")
            indent_label.pack(side="left", padx=(5, 0))

        # Module type label
        type_label = ctk.CTkLabel(
            header_frame,
            text=module.display_name,
            font=("Arial", 12, "bold")
        )
        type_label.pack(side="left", padx=10)

        # Control buttons frame (created before event binding)
        controls_frame = ctk.CTkFrame(header_frame, fg_color="gray20")
        controls_frame.pack(side="right", padx=5)

        # Enhanced click handling - make entire header clickable
        def on_header_click(event):
            # Don't trigger selection if clicking on drag handle or buttons
            clicked_widget = event.widget

            # Check if we clicked on the drag handle
            if clicked_widget == drag_handle:
                return

            # Check if we clicked on a button (control buttons)
            if isinstance(clicked_widget, ctk.CTkButton):
                return

            # Check if the clicked widget is inside the controls frame
            current = clicked_widget
            while current and current != header_frame:
                if current == controls_frame:
                    return  # Don't select if clicking in controls area
                try:
                    current = current.master
                except:
                    break

            # Safe to trigger selection
            if is_top_level:  # Only clear context when clicking main canvas modules
                self._clear_tab_context()
            self._safe_select_module_click(module, parent_tab)

        # Bind click to multiple areas for better UX
        type_label.bind("<Button-1>", on_header_click)
        header_frame.bind("<Button-1>", on_header_click)

        # Also make indent label clickable for nested modules
        if not is_top_level:
            indent_label.bind("<Button-1>", on_header_click)

        # Context-specific controls
        if not is_top_level and parent_tab:
            # For modules in tabs: add "move to main" button
            move_out_btn = ctk.CTkButton(
                controls_frame,
                text="↗",
                width=25,
                height=25,
                command=lambda m=module, pt0=parent_tab[0], pt1=parent_tab[1]:
                self._safe_move_module_from_tab(m, pt0, pt1)
            )
            move_out_btn.pack(side="left", padx=2)

        # Standard controls
        up_btn = ctk.CTkButton(
            controls_frame,
            text="↑",
            width=25,
            height=25,
            command=lambda: self._safe_move_module_up(module, parent_tab)
        )
        up_btn.pack(side="left", padx=2)

        down_btn = ctk.CTkButton(
            controls_frame,
            text="↓",
            width=25,
            height=25,
            command=lambda: self._safe_move_module_down(module, parent_tab)
        )
        down_btn.pack(side="left", padx=2)

        # Delete button
        delete_btn = ctk.CTkButton(
            controls_frame,
            text="✕",
            width=25,
            height=25,
            fg_color="darkred",
            hover_color="red",
            command=lambda mid=module.id: self._safe_remove_module(mid)
        )
        delete_btn.pack(side="left", padx=2)

        # Content preview
        preview_frame = ctk.CTkFrame(module_frame, fg_color="gray10")
        preview_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Add module preview content
        self.create_module_preview(preview_frame, module)

        return module_frame

    def create_module_preview(self, parent: ctk.CTkFrame, module: 'Module'):
        """Create preview of module content"""
        # Create a simplified preview based on module type
        preview_text = self.get_preview_text(module)

        preview_label = ctk.CTkLabel(
            parent,
            text=preview_text,
            font=("Arial", 11),
            justify="left",
            anchor="w",
            wraplength=400
        )
        preview_label.pack(fill="both", expand=True, padx=10, pady=10)

    def get_preview_text(self, module: 'Module') -> str:
        """Get preview text for module"""
        if module.module_type == 'header':
            return f"📄 {module.content_data.get('title', 'Header')}"
        elif module.module_type == 'text':
            content = module.content_data.get('content', '')[:100]
            return f"📝 {content}..." if len(content) >= 100 else f"📝 {content}"
        elif module.module_type == 'media':
            return f"🖼️ Media: {module.content_data.get('source', 'No source')}"
        elif module.module_type == 'table':
            return f"📊 Table: {module.content_data.get('title', 'Untitled')}"
        elif module.module_type == 'disclaimer':
            return f"⚠️ {module.content_data.get('label', 'Disclaimer')}"
        elif module.module_type == 'section_title':
            return f"📌 {module.content_data.get('title', 'Section')}"
        elif module.module_type == 'issue_card':
            return f"❗ {module.content_data.get('issue_title', 'Issue')}"
        elif module.module_type == 'footer':
            return f"📍 Footer - {module.content_data.get('organization', 'Organization')}"
        elif module.module_type == 'tabs':
            tab_count = len(module.content_data.get('tabs', []))
            return f"📑 Tab Section ({tab_count} tabs)"
        else:
            return f"{module.display_name}"

    def update_module_preview(self, module: 'Module'):
        """Update the preview for a specific module"""
        if module.id in self.module_widgets:
            widget = self.module_widgets[module.id]
            if not self._safe_widget_exists(widget):
                return

            # Find and update the preview label
            try:
                for child in widget.winfo_children():
                    if isinstance(child, ctk.CTkFrame) and self._safe_widget_exists(child):
                        for grandchild in child.winfo_children():
                            if (isinstance(grandchild, ctk.CTkLabel) and
                                    self._safe_widget_exists(grandchild) and
                                    grandchild.cget("font") == ("Arial", 11)):
                                try:
                                    grandchild.configure(text=self.get_preview_text(module))
                                except tk.TclError:
                                    pass
                                break
            except tk.TclError:
                pass

    def highlight_module(self, module: 'Module'):
        """Highlight the selected module"""
        # Remove previous highlight
        if self.selected_widget and self._safe_widget_exists(self.selected_widget):
            try:
                self.selected_widget.configure(border_color=("gray15", "gray15"))
            except tk.TclError:
                pass
            finally:
                self.selected_widget = None

        # Add highlight to selected module
        if module.id in self.module_widgets:
            widget = self.module_widgets[module.id]
            if self._safe_widget_exists(widget):
                try:
                    widget.configure(border_color="blue")
                    self.selected_widget = widget
                except tk.TclError:
                    if module.id in self.module_widgets:
                        del self.module_widgets[module.id]

    def remove_module_widget(self, module_id: str):
        """Remove module widget from canvas"""
        if module_id in self.module_widgets:
            widget = self.module_widgets[module_id]

            # Clear selection if this widget is currently selected
            if self.selected_widget == widget:
                self.selected_widget = None

            self._safe_destroy_widget(widget)
            del self.module_widgets[module_id]

            # Also clean up any tab-related widgets for this module
            keys_to_remove = [key for key in self.module_widgets.keys() if key.startswith(f"{module_id}:")]
            for key in keys_to_remove:
                widget = self.module_widgets[key]
                if self.selected_widget == widget:
                    self.selected_widget = None
                self._safe_destroy_widget(widget)
                del self.module_widgets[key]

    def clear_all_widgets(self):
        """Clear all module widgets"""
        self.selected_widget = None

        # Destroy all widgets safely
        widgets_to_destroy = list(self.module_widgets.values())
        for widget in widgets_to_destroy:
            self._safe_destroy_widget(widget)

        # Clear tracking dictionary
        self.module_widgets.clear()

    def refresh_widget_order(self):
        """Refresh the visual order of modules"""
        modules = sorted(self.app.active_modules, key=lambda m: m.position)

        for module in modules:
            if module.id in self.module_widgets:
                widget = self.module_widgets[module.id]
                if self._safe_widget_exists(widget):
                    try:
                        widget.pack_forget()
                        widget.pack(fill="x", padx=5, pady=5)
                    except tk.TclError:
                        pass

    def set_preview_mode(self, enabled: bool):
        """Toggle between edit and preview modes"""
        for widget in self.module_widgets.values():
            if not self._safe_widget_exists(widget):
                continue

            try:
                if enabled:
                    for child in widget.winfo_children():
                        if isinstance(child, ctk.CTkFrame) and self._safe_widget_exists(child):
                            for grandchild in child.winfo_children():
                                if isinstance(grandchild, ctk.CTkFrame) and self._safe_widget_exists(grandchild):
                                    grandchild.pack_forget()
                else:
                    self.refresh_widget_order()
            except tk.TclError:
                pass

    # Delegate methods - these call back to the main canvas panel or app
    def _clear_tab_context(self):
        """Clear tab context - delegate to canvas panel"""
        if hasattr(self.app, 'canvas_panel') and hasattr(self.app.canvas_panel, 'clear_tab_context'):
            self.app.canvas_panel.clear_tab_context()

    def _safe_select_module_click(self, module: 'Module', parent_tab: Optional[Tuple['TabModule', str]] = None):
        """Handle module selection clicks - delegate to app"""
        try:
            if not self.drag_drop_handler.is_dragging:
                self.app.select_module(module, parent_tab)
        except Exception as e:
            print(f"Error in module selection: {e}")

    def _safe_move_module_from_tab(self, module: 'Module', tab_module: 'TabModule', tab_name: str):
        """Safely move module from tab to main canvas - delegate to app"""
        try:
            self.app.move_module_from_tab(module, tab_module, tab_name)
        except Exception as e:
            print(f"Error moving module from tab: {e}")

    def _safe_move_module_up(self, module: 'Module', parent_tab: Optional[Tuple['TabModule', str]] = None):
        """Safely move module up - delegate to canvas panel"""
        try:
            if hasattr(self.app, 'canvas_panel'):
                self.app.canvas_panel._move_module_up(module, parent_tab)
        except Exception as e:
            print(f"Error moving module up: {e}")

    def _safe_move_module_down(self, module: 'Module', parent_tab: Optional[Tuple['TabModule', str]] = None):
        """Safely move module down - delegate to canvas panel"""
        try:
            if hasattr(self.app, 'canvas_panel'):
                self.app.canvas_panel._move_module_down(module, parent_tab)
        except Exception as e:
            print(f"Error moving module down: {e}")

    def _safe_remove_module(self, module_id: str):
        """Safely remove module - delegate to app"""
        try:
            self.app.remove_module(module_id)
        except Exception as e:
            print(f"Error removing module: {e}")
