# gui/renderers/tab_widget_manager.py
"""
Tab Widget Manager

Handles the creation, management, and lifecycle of tab module widgets on the canvas.
This includes creating tab content areas, managing tab switching, handling tab-specific
drop zones, and coordinating tab-related UI interactions.
"""

import customtkinter as ctk
from typing import Dict, Optional, Tuple, TYPE_CHECKING
import tkinter as tk

if TYPE_CHECKING:
    from modules.base_module import Module
    from modules.complex_module import TabModule


class TabWidgetManager:
    """Manages the creation and lifecycle of tab module widgets and their content"""

    def __init__(self, app_instance, module_widget_manager, library_drag_drop_handler,
                 safe_widget_exists_func, safe_destroy_widget_func):
        """
        Initialize the tab widget manager

        Args:
            app_instance: Reference to the main application
            module_widget_manager: Reference to the module widget manager
            library_drag_drop_handler: Reference to library drag drop handler
            safe_widget_exists_func: Function to safely check widget existence
            safe_destroy_widget_func: Function to safely destroy widgets
        """
        self.app = app_instance
        self.module_widget_manager = module_widget_manager
        self.library_drag_drop_handler = library_drag_drop_handler
        self._safe_widget_exists = safe_widget_exists_func
        self._safe_destroy_widget = safe_destroy_widget_func

        # Tab widget tracking - tab_module_id -> {tab_name -> frame}
        self.tab_widgets: Dict[str, Dict[str, ctk.CTkFrame]] = {}

    def create_tab_content_areas(self, tab_module: 'TabModule', parent_frame: ctk.CTkFrame,
                                 with_nested: bool = False):
        """Create visual areas for tab content with proper module display"""
        # Create a frame for tab contents
        tab_container = ctk.CTkFrame(parent_frame, fg_color="gray20")
        tab_container.pack(fill="both", expand=True, padx=5, pady=(0, 5))

        # Store reference to the tab container for easy access
        tab_container._tab_module_id = tab_module.id

        # Initialize storage for this tab module
        if tab_module.id not in self.tab_widgets:
            self.tab_widgets[tab_module.id] = {}

        # Create tab selector frame
        tab_selector_frame = ctk.CTkFrame(tab_container, fg_color="gray25", height=35)
        tab_selector_frame.pack(fill="x", padx=2, pady=2)
        tab_selector_frame.pack_propagate(False)

        # Store reference for easy access
        tab_container._tab_selector_frame = tab_selector_frame

        # Create content area container (this will hold the switchable content)
        content_area = ctk.CTkFrame(tab_container, fg_color="gray18")
        content_area.pack(fill="both", expand=True, padx=2, pady=2)

        # Store reference for easy access
        tab_container._content_area = content_area

        # Create tab content frames for ALL tabs (but only show the active one)
        self._create_all_tab_content_frames(tab_module, content_area, with_nested)

        # Create/update tab buttons
        self._update_tab_buttons(tab_module, tab_selector_frame)

    def _update_tab_buttons(self, tab_module: 'TabModule', tab_selector_frame: ctk.CTkFrame):
        """Update tab buttons with current active state"""
        # Clear existing buttons
        for widget in tab_selector_frame.winfo_children():
            if self._safe_widget_exists(widget):
                self._safe_destroy_widget(widget)

        active_tab_index = tab_module.content_data.get('active_tab', 0)

        # Create tab buttons
        for i, tab_name in enumerate(tab_module.content_data['tabs']):
            is_active = (i == active_tab_index)

            tab_btn = ctk.CTkButton(
                tab_selector_frame,
                text=tab_name,
                width=100,
                height=25,
                fg_color="gray30" if is_active else "gray40",
                hover_color="gray35" if is_active else "gray45",
                command=lambda tn=tab_name, tm=tab_module: self._safe_on_tab_click(tm, tn)
            )
            tab_btn.pack(side="left", padx=2, pady=4)

        # Add "+" button to add new tab
        add_tab_btn = ctk.CTkButton(
            tab_selector_frame,
            text="+",
            width=30,
            height=25,
            fg_color="green",
            hover_color="darkgreen",
            command=lambda: self._safe_add_new_tab(tab_module)
        )
        add_tab_btn.pack(side="left", padx=2)

    def _create_all_tab_content_frames(self, tab_module: 'TabModule', content_area: ctk.CTkFrame,
                                       with_nested: bool = False):
        """Create content frames for all tabs in the module"""
        active_tab_index = tab_module.content_data.get('active_tab', 0)

        for i, tab_name in enumerate(tab_module.content_data['tabs']):
            # Create content frame for this tab
            tab_content_frame = ctk.CTkFrame(
                content_area,
                fg_color="gray15",
                border_width=1,
                border_color="gray20"
            )

            # Only pack the active tab initially
            if i == active_tab_index:
                tab_content_frame.pack(fill="both", expand=True, padx=5, pady=5)

            # Store the tab content frame
            tab_content_frame._tab_name = tab_name
            tab_content_frame._tab_module_id = tab_module.id

            # Enable drop zone for this tab (including library drops)
            self._enable_tab_drop_zone(tab_content_frame, tab_module, tab_name)

            # Header label for the tab content with better instructions
            module_count = len(tab_module.sub_modules.get(tab_name, []))
            if module_count > 0:
                header_text = f"'{tab_name}' tab ({module_count} modules)"
                subheader_text = "Drag modules here or click to add new ones"
            else:
                header_text = f"'{tab_name}' tab - Empty"
                subheader_text = "Drag modules from left panel or click to select this tab"

            header_label = ctk.CTkLabel(
                tab_content_frame,
                text=header_text,
                font=("Arial", 12, "bold"),
                text_color="white"
            )
            header_label.pack(pady=(10, 2))

            # Add instructional subheader
            subheader_label = ctk.CTkLabel(
                tab_content_frame,
                text=subheader_text,
                font=("Arial", 10),
                text_color="gray"
            )
            subheader_label.pack(pady=(0, 5))

            # Container for modules in this tab
            modules_container = ctk.CTkScrollableFrame(tab_content_frame, fg_color="gray15")
            modules_container.pack(fill="both", expand=True, padx=5, pady=5)

            # Store the modules container
            self.tab_widgets[tab_module.id][tab_name] = modules_container

            # If loading from file, add existing nested modules
            if with_nested and tab_name in tab_module.sub_modules:
                for nested_module in sorted(tab_module.sub_modules[tab_name], key=lambda m: m.position):
                    self.add_module_to_tab_widget(tab_module, tab_name, nested_module)

    def _enable_tab_drop_zone(self, content_frame: ctk.CTkFrame, tab_module: 'TabModule', tab_name: str):
        """Enable the content frame as a drop zone for modules (including library modules)"""

        def on_click(event):
            if self._safe_widget_exists(content_frame):
                # Set tab context when explicitly clicking in the tab content area
                self._set_tab_context(tab_module, tab_name)

                # Visual feedback that this tab is now the active add target
                self._highlight_active_add_target(content_frame)

        def on_enter(event):
            if self._safe_widget_exists(content_frame) and not self._is_dragging():
                # Enhanced feedback for library drags
                if self.app.main_window.is_dragging_from_library:
                    try:
                        content_frame.configure(border_width=3, border_color="lightgreen")
                    except tk.TclError:
                        pass
                else:
                    # Regular hover feedback
                    try:
                        content_frame.configure(border_width=2, border_color="lightblue")
                    except tk.TclError:
                        pass

        def on_leave(event):
            if self._safe_widget_exists(content_frame) and not self._is_dragging():
                # Remove hover feedback unless this is the active add target
                if (not hasattr(self.app, 'selected_tab_context') or
                        not self.app.selected_tab_context or
                        self.app.selected_tab_context != (tab_module, tab_name)):
                    try:
                        content_frame.configure(border_width=1, border_color="gray20")
                    except tk.TclError:
                        pass

        # Bind events for better UX
        content_frame.bind("<Button-1>", on_click)
        content_frame.bind("<Enter>", on_enter)
        content_frame.bind("<Leave>", on_leave)

        # Store drop zone info for drag detection (works for both existing module drags and library drags)
        content_frame._drop_zone_info = {
            'type': 'tab',
            'tab_module': tab_module,
            'tab_name': tab_name
        }

    def add_module_to_tab_widget(self, tab_module: 'TabModule', tab_name: str, module: 'Module'):
        """Add a module widget to a specific tab"""
        if tab_module.id not in self.tab_widgets:
            return

        # Get or create the container for this tab
        if tab_name not in self.tab_widgets[tab_module.id]:
            self.switch_active_tab(tab_module, tab_name)

        container = self.tab_widgets[tab_module.id].get(tab_name)
        if not container or not self._safe_widget_exists(container):
            print(f"Error: Container for tab '{tab_name}' not found after attempting to switch/create.")
            return

        # Create module frame using the widget manager
        module_frame = self.module_widget_manager.create_module_frame(
            module,
            is_top_level=False,
            parent_tab=(tab_module, tab_name),
            parent_widget=container
        )
        module_frame.pack(fill="x", padx=5, pady=5)

        # Store reference (with tab context in the key)
        widget_key = f"{tab_module.id}:{tab_name}:{module.id}"
        self.module_widget_manager.module_widgets[widget_key] = module_frame

        # Enable drag and drop for this module using the handler
        if hasattr(self.app, 'canvas_panel') and hasattr(self.app.canvas_panel, 'drag_drop_handler'):
            self.app.canvas_panel.drag_drop_handler.enable_drag_drop(
                module_frame, module, parent_tab=(tab_module, tab_name)
            )

    def remove_module_from_tab_widget(self, tab_module: 'TabModule', tab_name: str, module_id: str):
        """Remove a module widget from a tab"""
        widget_key = f"{tab_module.id}:{tab_name}:{module_id}"
        if widget_key in self.module_widget_manager.module_widgets:
            widget = self.module_widget_manager.module_widgets[widget_key]

            # Clear selection if this widget is currently selected
            if self.module_widget_manager.selected_widget == widget:
                self.module_widget_manager.selected_widget = None

            self._safe_destroy_widget(widget)
            del self.module_widget_manager.module_widgets[widget_key]

    def on_tab_click(self, tab_module: 'TabModule', tab_name: str):
        """Handle tab selection - for VIEWING only, not setting add context"""
        if tab_name not in tab_module.content_data['tabs']:
            return

        old_active_index = tab_module.content_data.get('active_tab', 0)
        new_active_index = tab_module.content_data['tabs'].index(tab_name)

        # Only switch if it's actually a different tab
        if old_active_index != new_active_index:
            # Update the active tab in the module
            tab_module.content_data['active_tab'] = new_active_index

            # Switch the visible content
            self._switch_tab_content(tab_module, tab_name)

            # Update button appearances
            self._update_tab_button_states(tab_module)

            # DON'T automatically set this as the add context
            # User needs to explicitly click in the tab content area for that

            self.app.set_modified(True)

    def _switch_tab_content(self, tab_module: 'TabModule', new_active_tab: str):
        """Switch visible tab content without destroying widgets"""
        tab_module_widget = self.module_widget_manager.module_widgets.get(tab_module.id)
        if not tab_module_widget or not self._safe_widget_exists(tab_module_widget):
            return

        # Find the content area
        content_area = self._find_content_area(tab_module_widget)
        if not content_area:
            return

        # Hide all tab content frames and show the active one
        for widget in content_area.winfo_children():
            if not self._safe_widget_exists(widget):
                continue

            if hasattr(widget, '_tab_name'):
                if widget._tab_name == new_active_tab:
                    widget.pack(fill="both", expand=True, padx=5, pady=5)
                    # Update the header text with current module count
                    self._update_tab_header(widget, tab_module, widget._tab_name)
                else:
                    widget.pack_forget()

    def refresh_tab_module(self, tab_module: 'TabModule'):
        """Refresh the entire tab module widget - simplified version"""
        # Store the current active tab
        current_active_tab = tab_module.content_data.get('active_tab', 0)

        # Clean up all references first
        self._cleanup_tab_widget_references(tab_module.id)

        # Remove and recreate the widget
        if tab_module.id in self.module_widget_manager.module_widgets:
            widget = self.module_widget_manager.module_widgets[tab_module.id]
            if self._safe_widget_exists(widget):
                self._safe_destroy_widget(widget)
            del self.module_widget_manager.module_widgets[tab_module.id]

        # Clean up tab widget references
        if tab_module.id in self.tab_widgets:
            del self.tab_widgets[tab_module.id]

        # Recreate with the preserved active tab
        try:
            # Delegate to canvas panel to add the widget with nested content
            if hasattr(self.app, 'canvas_panel'):
                self.app.canvas_panel.add_module_widget(tab_module, with_nested=True)

            # Ensure the correct tab is still active
            if current_active_tab < len(tab_module.content_data['tabs']):
                tab_module.content_data['active_tab'] = current_active_tab
                active_tab_name = tab_module.content_data['tabs'][current_active_tab]
                self._switch_tab_content(tab_module, active_tab_name)
                self._update_tab_button_states(tab_module)

        except Exception as e:
            print(f"Error refreshing tab module: {e}")

    def switch_active_tab(self, tab_module: 'TabModule', tab_name: str):
        """Switch the visible tab content with improved safety"""
        # Find the parent_frame of the tab_module
        if tab_module.id not in self.module_widget_manager.module_widgets:
            return

        tab_module_main_frame = self.module_widget_manager.module_widgets[tab_module.id]
        if not self._safe_widget_exists(tab_module_main_frame):
            return

        # Find tab_container within tab_module_main_frame
        tab_container = None
        try:
            for child in tab_module_main_frame.winfo_children():
                if isinstance(child, ctk.CTkFrame) and self._safe_widget_exists(child):
                    try:
                        if child.cget("fg_color") == "gray20":
                            tab_container = child
                            break
                    except tk.TclError:
                        continue
        except tk.TclError:
            return

        if not tab_container or not self._safe_widget_exists(tab_container):
            return

        # Clean up widget references before destroying widgets
        self._cleanup_tab_widget_references(tab_module.id)

        # Safely destroy existing content_frame
        widgets_to_destroy = []
        try:
            for widget in tab_container.winfo_children():
                if self._safe_widget_exists(widget):
                    try:
                        if widget.cget("fg_color") == "gray15":
                            widgets_to_destroy.append(widget)
                    except tk.TclError:
                        pass
        except tk.TclError:
            pass

        for widget in widgets_to_destroy:
            self._safe_destroy_widget(widget)

        # Recreate tab buttons and content
        self._recreate_tab_interface(tab_module, tab_container, tab_name)

    def _recreate_tab_interface(self, tab_module: 'TabModule', tab_container: ctk.CTkFrame, target_tab_name: str):
        """Recreate tab buttons and content for the specified target tab"""
        # Recreate tab buttons
        tab_selector_frame = None
        try:
            for child in tab_container.winfo_children():
                if isinstance(child, ctk.CTkFrame) and self._safe_widget_exists(child):
                    try:
                        if child.cget("fg_color") == "gray25":
                            tab_selector_frame = child
                            break
                    except tk.TclError:
                        continue
        except tk.TclError:
            pass

        if tab_selector_frame and self._safe_widget_exists(tab_selector_frame):
            # Clear existing buttons
            buttons_to_destroy = []
            try:
                for widget in tab_selector_frame.winfo_children():
                    if self._safe_widget_exists(widget):
                        buttons_to_destroy.append(widget)
            except tk.TclError:
                pass

            for widget in buttons_to_destroy:
                self._safe_destroy_widget(widget)

            # Create new buttons
            self._create_tab_buttons(tab_module, tab_selector_frame, target_tab_name)

        # Create new content frame for the selected tab
        self._create_new_tab_content_frame(tab_module, tab_container, target_tab_name)

    def _create_tab_buttons(self, tab_module: 'TabModule', tab_selector_frame: ctk.CTkFrame, active_tab_name: str):
        """Create tab buttons with the specified active tab"""
        try:
            for i, tn in enumerate(tab_module.content_data['tabs']):
                is_active = (tn == active_tab_name)
                tab_btn = ctk.CTkButton(
                    tab_selector_frame,
                    text=tn,
                    width=100,
                    height=25,
                    fg_color="gray30" if is_active else "gray40",
                    command=lambda t_name=tn, tm=tab_module: self._safe_on_tab_click(tm, t_name)
                )
                tab_btn.pack(side="left", padx=2, pady=4)

            add_tab_btn = ctk.CTkButton(
                tab_selector_frame,
                text="+",
                width=30,
                height=25,
                command=lambda tm=tab_module: self._safe_add_new_tab(tm)
            )
            add_tab_btn.pack(side="left", padx=2)
        except tk.TclError:
            pass

    def _create_new_tab_content_frame(self, tab_module: 'TabModule', tab_container: ctk.CTkFrame, tab_name: str):
        """Create new content frame for the selected tab"""
        if self._safe_widget_exists(tab_container):
            try:
                content_frame = ctk.CTkFrame(tab_container, fg_color="gray15")
                content_frame.pack(fill="both", expand=True, padx=5, pady=5)

                # Enable drop zone for this tab
                self._enable_tab_drop_zone(content_frame, tab_module, tab_name)

                # Header label for the tab content
                if tab_name in tab_module.sub_modules and tab_module.sub_modules[tab_name]:
                    header_text = f"'{tab_name}' tab content ({len(tab_module.sub_modules[tab_name])} modules)"
                else:
                    header_text = f"'{tab_name}' tab - Drop modules here or click to select"

                header_label = ctk.CTkLabel(
                    content_frame,
                    text=header_text,
                    font=("Arial", 12, "bold"),
                    text_color="gray"
                )
                header_label.pack(pady=(10, 5))

                # Container for modules in this tab
                modules_container = ctk.CTkScrollableFrame(content_frame, fg_color="gray15")
                modules_container.pack(fill="both", expand=True, padx=5, pady=5)

                # Store the new content frame
                self.tab_widgets[tab_module.id][tab_name] = modules_container

                # Re-add modules for this tab
                if tab_name in tab_module.sub_modules:
                    for nested_module in sorted(tab_module.sub_modules[tab_name], key=lambda m: m.position):
                        self.add_module_to_tab_widget(tab_module, tab_name, nested_module)

            except tk.TclError as e:
                print(f"Error creating tab content frame: {e}")

    def refresh_tab_content(self, tab_module: 'TabModule', tab_name: str):
        """Refresh the content of a specific tab"""
        if tab_module.id not in self.tab_widgets or tab_name not in self.tab_widgets[tab_module.id]:
            return

        container = self.tab_widgets[tab_module.id][tab_name]
        if not self._safe_widget_exists(container):
            return

        # Clean up widget references for this specific tab before destroying widgets
        keys_to_remove = []
        for widget_key in list(self.module_widget_manager.module_widgets.keys()):
            if widget_key.startswith(f"{tab_module.id}:{tab_name}:"):
                keys_to_remove.append(widget_key)

        for key in keys_to_remove:
            if key in self.module_widget_manager.module_widgets:
                widget = self.module_widget_manager.module_widgets[key]
                if self.module_widget_manager.selected_widget == widget:
                    self.module_widget_manager.selected_widget = None
                del self.module_widget_manager.module_widgets[key]

        # Clear existing widgets in the container
        widgets_to_destroy = []
        try:
            for widget in container.winfo_children():
                if self._safe_widget_exists(widget):
                    widgets_to_destroy.append(widget)
        except tk.TclError:
            pass

        for widget in widgets_to_destroy:
            self._safe_destroy_widget(widget)

        # Re-add modules in correct order
        if tab_name in tab_module.sub_modules:
            for module in sorted(tab_module.sub_modules.get(tab_name, []), key=lambda m: m.position):
                try:
                    self.add_module_to_tab_widget(tab_module, tab_name, module)
                except Exception as e:
                    print(f"Error adding module to tab widget: {e}")

    def clear_tab_widgets(self, tab_module_id: str):
        """Clear all tab widgets for a specific tab module"""
        if tab_module_id in self.tab_widgets:
            del self.tab_widgets[tab_module_id]

    def clear_all_tab_widgets(self):
        """Clear all tab widgets"""
        self.tab_widgets.clear()

    # Helper methods
    def _safe_on_tab_click(self, tab_module: 'TabModule', tab_name: str):
        """Safely handle tab selection with widget existence checks"""
        try:
            if not self._safe_widget_exists(self.module_widget_manager.module_widgets.get(tab_module.id)):
                return
            self.on_tab_click(tab_module, tab_name)
        except Exception as e:
            print(f"Error in tab click: {e}")

    def _safe_add_new_tab(self, tab_module: 'TabModule'):
        """Safely add new tab with widget existence checks"""
        try:
            if not self._safe_widget_exists(self.module_widget_manager.module_widgets.get(tab_module.id)):
                return
            self._add_new_tab(tab_module)
        except Exception as e:
            print(f"Error adding new tab: {e}")

    def _add_new_tab(self, tab_module: 'TabModule'):
        """Add a new tab to the TabModule"""
        dialog = ctk.CTkInputDialog(text="Enter tab name:", title="New Tab")
        tab_name = dialog.get_input()

        if tab_name and tab_name not in tab_module.content_data['tabs']:
            tab_module.add_tab(tab_name)
            self.refresh_tab_module(tab_module)
            self.app.set_modified(True)

    def _update_tab_button_states(self, tab_module: 'TabModule'):
        """Update the visual state of tab buttons"""
        tab_module_widget = self.module_widget_manager.module_widgets.get(tab_module.id)
        if not tab_module_widget or not self._safe_widget_exists(tab_module_widget):
            return

        # Find the tab selector frame
        tab_selector_frame = None
        try:
            for child in tab_module_widget.winfo_children():
                if (isinstance(child, ctk.CTkFrame) and
                        self._safe_widget_exists(child) and
                        hasattr(child, '_tab_selector_frame')):
                    tab_selector_frame = child._tab_selector_frame
                    break
        except tk.TclError:
            return

        if not tab_selector_frame:
            return

        # Update button colors
        active_tab_index = tab_module.content_data.get('active_tab', 0)
        button_index = 0

        try:
            for widget in tab_selector_frame.winfo_children():
                if (isinstance(widget, ctk.CTkButton) and
                        self._safe_widget_exists(widget) and
                        widget.cget("text") != "+"):  # Skip the add button

                    is_active = (button_index == active_tab_index)
                    try:
                        widget.configure(
                            fg_color="gray30" if is_active else "gray40",
                            hover_color="gray35" if is_active else "gray45"
                        )
                    except tk.TclError:
                        pass
                    button_index += 1
        except tk.TclError:
            pass

    def _update_tab_header(self, tab_content_frame, tab_module: 'TabModule', tab_name: str):
        """Update the header text for a tab"""
        module_count = len(tab_module.sub_modules.get(tab_name, []))
        if module_count > 0:
            header_text = f"'{tab_name}' tab ({module_count} modules)"
            subheader_text = "Drag modules here or click to add new ones"
        else:
            header_text = f"'{tab_name}' tab - Empty"
            subheader_text = "Drag modules from left panel or click to select this tab"

        # Find and update the header labels
        labels_updated = 0
        try:
            for widget in tab_content_frame.winfo_children():
                if (isinstance(widget, ctk.CTkLabel) and
                        self._safe_widget_exists(widget) and
                        "tab" in widget.cget("text")):

                    if labels_updated == 0:  # Main header
                        widget.configure(text=header_text)
                    elif labels_updated == 1:  # Subheader
                        widget.configure(text=subheader_text)
                        break
                    labels_updated += 1
        except tk.TclError:
            pass

    def _find_content_area(self, tab_module_widget):
        """Find the content area within a tab module widget"""
        try:
            for child in tab_module_widget.winfo_children():
                if (isinstance(child, ctk.CTkFrame) and
                        self._safe_widget_exists(child) and
                        hasattr(child, '_content_area')):
                    return child._content_area
        except tk.TclError:
            pass
        return None

    def _cleanup_tab_widget_references(self, tab_module_id: str):
        """Clean up widget references for a tab module before recreating them"""
        keys_to_remove = []
        for widget_key in list(self.module_widget_manager.module_widgets.keys()):
            if widget_key.startswith(f"{tab_module_id}:"):
                keys_to_remove.append(widget_key)

        for key in keys_to_remove:
            if key in self.module_widget_manager.module_widgets:
                widget = self.module_widget_manager.module_widgets[key]
                # Clear selection if this widget is currently selected
                if self.module_widget_manager.selected_widget == widget:
                    self.module_widget_manager.selected_widget = None
                del self.module_widget_manager.module_widgets[key]

    def _set_tab_context(self, tab_module: 'TabModule', tab_name: str):
        """Set the selected tab context for adding new modules with visual feedback"""
        if not self._is_dragging():  # Only set context if not dragging
            self.app.selected_tab_context = (tab_module, tab_name)
            self.app.select_tab(tab_module, tab_name)

            # Clear any previous add target highlights
            self._clear_add_target_highlights()

            # Show user feedback about where modules will be added
            self._show_add_target_feedback(tab_module, tab_name)

    def _highlight_active_add_target(self, content_frame):
        """Highlight the active add target with visual feedback"""
        try:
            content_frame.configure(border_width=3, border_color="green")
        except tk.TclError:
            pass

    def _clear_add_target_highlights(self):
        """Clear all add target highlights"""
        for tab_id, tab_containers in self.tab_widgets.items():
            for tab_name, container in tab_containers.items():
                if self._safe_widget_exists(container):
                    # Find the parent content frame
                    try:
                        parent = container.master
                        if self._safe_widget_exists(parent):
                            parent.configure(border_width=1, border_color="gray20")
                    except tk.TclError:
                        pass

    def _show_add_target_feedback(self, tab_module: 'TabModule', tab_name: str):
        """Show user feedback about where new modules will be added"""
        # Update the main window status
        if hasattr(self.app, 'main_window') and hasattr(self.app.main_window, 'set_status'):
            self.app.main_window.set_status(f"Adding to '{tab_name}' tab", "green")

    def _is_dragging(self) -> bool:
        """Check if currently dragging (delegates to drag drop handler)"""
        if hasattr(self.app, 'canvas_panel') and hasattr(self.app.canvas_panel, 'drag_drop_handler'):
            return self.app.canvas_panel.drag_drop_handler.is_dragging
        return False