# gui/canvas_panel.py - Enhanced with library drag and drop support
import customtkinter as ctk
from typing import Dict, Optional, Tuple, Any
from modules.base_module import Module
from modules.complex_module import TabModule
from gui.handlers.canvas_drag_drop_handler import CanvasDragDropHandler
from gui.handlers.library_drag_drop_handler import LibraryDragDropHandler
import tkinter as tk


class CanvasPanel:
    """Central panel for arranging modules with enhanced drag and drop support"""

    def __init__(self, parent, app_instance):
        self.parent = parent
        self.app = app_instance
        self.module_widgets: Dict[str, ctk.CTkFrame] = {}
        self.tab_widgets: Dict[str, Dict[str, ctk.CTkFrame]] = {}  # tab_module_id -> {tab_name -> frame}
        self.selected_widget: Optional[ctk.CTkFrame] = None
        self.preview_mode = False

        # Track widgets scheduled for destruction to prevent access
        self.widgets_being_destroyed = set()

        # Initialize drag and drop handlers
        self.drag_drop_handler = CanvasDragDropHandler(self, app_instance)
        self.library_drag_drop_handler = LibraryDragDropHandler(self, app_instance)

        self._setup_canvas()

    def _setup_canvas(self):
        """Initialize canvas layout with drop zone support"""
        # Create a frame to hold all module widgets
        self.modules_frame = ctk.CTkFrame(
            self.parent,
            fg_color=("gray92", "gray12")
        )
        self.modules_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Enable the canvas as a drop zone for library modules
        self.library_drag_drop_handler.setup_library_drop_zone()

    def handle_library_drop(self, drop_target, module_type: str) -> bool:
        """Handle dropping a module from the library"""
        return self.library_drag_drop_handler.handle_library_drop(drop_target, module_type)

    def _safe_widget_exists(self, widget):
        """Safely check if a widget exists and hasn't been destroyed"""
        if widget is None:
            return False
        if id(widget) in self.widgets_being_destroyed:
            return False
        try:
            return widget.winfo_exists()
        except tk.TclError:
            return False

    def _safe_destroy_widget(self, widget):
        """Safely destroy a widget with proper cleanup"""
        if not self._safe_widget_exists(widget):
            return

        try:
            # Mark widget as being destroyed
            self.widgets_being_destroyed.add(id(widget))

            # Clear any selection
            if self.selected_widget == widget:
                self.selected_widget = None

            # Clear library drop highlighting if this widget is highlighted
            if self.library_drop_highlight == widget:
                self.library_drop_highlight = None

            # Unbind all events recursively
            self._unbind_all_events(widget)

            # Destroy the widget
            widget.destroy()

        except tk.TclError:
            # Widget already destroyed
            pass
        finally:
            # Remove from tracking set
            if id(widget) in self.widgets_being_destroyed:
                self.widgets_being_destroyed.remove(id(widget))

    def _unbind_all_events(self, widget):
        """Recursively unbind all events from a widget and its children"""
        if not self._safe_widget_exists(widget):
            return

        try:
            # Unbind common events
            events_to_unbind = [
                '<Button-1>', '<B1-Motion>', '<ButtonRelease-1>',
                '<Enter>', '<Leave>', '<KeyRelease>', '<FocusIn>', '<FocusOut>',
                '<Motion>'  # Added Motion event
            ]

            for event in events_to_unbind:
                try:
                    widget.unbind(event)
                except:
                    pass

            # Recursively unbind for children
            for child in widget.winfo_children():
                self._unbind_all_events(child)

        except tk.TclError:
            # Widget no longer exists
            pass

    def add_module_widget(self, module: Module, with_nested: bool = False):
        """Add visual representation of module"""
        # Create main module frame
        module_frame = self._create_module_frame(module, is_top_level=True)
        module_frame.pack(fill="x", padx=5, pady=5)

        # Store reference
        self.module_widgets[module.id] = module_frame

        # If it's a TabModule, create tab content areas
        if isinstance(module, TabModule):
            self._create_tab_content_areas(module, module_frame, with_nested)

        # Make frame draggable using the drag drop handler
        self.drag_drop_handler.enable_drag_drop(module_frame, module)

    def _create_tab_content_areas(self, tab_module: TabModule, parent_frame: ctk.CTkFrame,
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

    def _update_tab_buttons(self, tab_module: TabModule, tab_selector_frame: ctk.CTkFrame):
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

    def _create_all_tab_content_frames(self, tab_module: TabModule, content_area: ctk.CTkFrame,
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

    def _safe_on_tab_click(self, tab_module: TabModule, tab_name: str):
        """Safely handle tab selection with widget existence checks"""
        try:
            if not self._safe_widget_exists(self.module_widgets.get(tab_module.id)):
                return
            self._on_tab_click(tab_module, tab_name)
        except Exception as e:
            print(f"Error in tab click: {e}")

    def _safe_add_new_tab(self, tab_module: TabModule):
        """Safely add new tab with widget existence checks"""
        try:
            if not self._safe_widget_exists(self.module_widgets.get(tab_module.id)):
                return
            self._add_new_tab(tab_module)
        except Exception as e:
            print(f"Error adding new tab: {e}")

    def _enable_tab_drop_zone(self, content_frame: ctk.CTkFrame, tab_module: TabModule, tab_name: str):
        """Enable the content frame as a drop zone for modules (including library modules)"""

        def on_click(event):
            if self._safe_widget_exists(content_frame):
                # Set tab context when explicitly clicking in the tab content area
                self._set_tab_context(tab_module, tab_name)

                # Visual feedback that this tab is now the active add target
                self._highlight_active_add_target(content_frame)

        def on_enter(event):
            if self._safe_widget_exists(content_frame) and not self.drag_drop_handler.is_dragging:
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
            if self._safe_widget_exists(content_frame) and not self.drag_drop_handler.is_dragging:
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

    def _set_tab_context(self, tab_module: TabModule, tab_name: str):
        """Set the selected tab context for adding new modules with visual feedback"""
        if not self.drag_drop_handler.is_dragging:  # Only set context if not dragging
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

    def add_module_to_tab_widget(self, tab_module: TabModule, tab_name: str, module: Module):
        """Add a module widget to a specific tab"""
        if tab_module.id not in self.tab_widgets:
            return

        # Get or create the container for this tab
        if tab_name not in self.tab_widgets[tab_module.id]:
            self._switch_active_tab(tab_module, tab_name)

        container = self.tab_widgets[tab_module.id].get(tab_name)
        if not container or not self._safe_widget_exists(container):
            print(f"Error: Container for tab '{tab_name}' not found after attempting to switch/create.")
            return

        # Create module frame
        module_frame = self._create_module_frame(module, is_top_level=False, parent_tab=(tab_module, tab_name))
        module_frame.pack(fill="x", padx=5, pady=5)

        # Store reference (with tab context in the key)
        widget_key = f"{tab_module.id}:{tab_name}:{module.id}"
        self.module_widgets[widget_key] = module_frame

        # Enable drag and drop for this module using the handler
        self.drag_drop_handler.enable_drag_drop(module_frame, module, parent_tab=(tab_module, tab_name))

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

    def _show_add_target_feedback(self, tab_module: TabModule, tab_name: str):
        """Show user feedback about where new modules will be added"""
        # Update the main window status
        if hasattr(self.app, 'main_window') and hasattr(self.app.main_window, 'set_status'):
            self.app.main_window.set_status(f"Adding to '{tab_name}' tab", "green")

    def _create_module_frame(self, module: Module, is_top_level: bool = True,
                             parent_tab: Optional[Tuple[TabModule, str]] = None) -> ctk.CTkFrame:
        """Create a frame for a module"""
        # Use different styling for nested modules
        frame_color = "gray15" if is_top_level else "gray18"
        border_color = "gray15" if is_top_level else "gray20"

        parent_widget = self.modules_frame
        if not is_top_level and parent_tab:
            tab_module_id, tab_name = parent_tab[0].id, parent_tab[1]
            if tab_module_id in self.tab_widgets and tab_name in self.tab_widgets[tab_module_id]:
                container = self.tab_widgets[tab_module_id][tab_name]
                if self._safe_widget_exists(container):
                    parent_widget = container
                else:
                    parent_widget = self.modules_frame
            else:
                parent_widget = self.modules_frame

        module_frame = ctk.CTkFrame(
            parent_widget,
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

        # Add clickable area for module selection (separate from drag)
        # When clicking a main canvas module, clear tab context
        def on_module_click(event):
            # Don't trigger selection if clicking on drag handle or control buttons
            if (hasattr(event.widget, '_drag_handle') or
                    isinstance(event.widget, ctk.CTkButton) or
                    event.widget == drag_handle):
                return

            if is_top_level:  # Only clear context when clicking main canvas modules
                self.clear_tab_context()
            self._safe_select_module_click(module, parent_tab)

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
                self.clear_tab_context()
            self._safe_select_module_click(module, parent_tab)

        # Bind click to multiple areas for better UX
        type_label.bind("<Button-1>", on_module_click)
        header_frame.bind("<Button-1>", on_header_click)

        # Also make indent label clickable for nested modules
        if not is_top_level:
            indent_label.bind("<Button-1>", on_module_click)

        # Control buttons
        controls_frame = ctk.CTkFrame(header_frame, fg_color="gray20")
        controls_frame.pack(side="right", padx=5)

        # Context-specific controls
        if not is_top_level and parent_tab:
            # For modules in tabs: add "move to main" button
            move_out_btn = ctk.CTkButton(
                controls_frame,
                text="↗",
                width=25,
                height=25,
                command=lambda m=module, pt0=parent_tab[0], pt1=parent_tab[1]: self._safe_move_module_from_tab(m, pt0,
                                                                                                               pt1)
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
        self._create_module_preview(preview_frame, module)

        return module_frame

    def _is_child_of(self, child_widget, parent_widget) -> bool:
        """Check if child_widget is a descendant of parent_widget"""
        if not self._safe_widget_exists(child_widget) or not self._safe_widget_exists(parent_widget):
            return False

        current = child_widget
        while current:
            if current == parent_widget:
                return True
            try:
                current = current.master
            except (tk.TclError, AttributeError):
                break
        return False

    def clear_tab_context(self):
        """Clear the tab context and reset to main canvas adding"""
        self.app.selected_tab_context = None
        self._clear_add_target_highlights()
        self.library_drag_drop_handler.clear_library_drop_highlight()

        # Update status
        if hasattr(self.app, 'main_window') and hasattr(self.app.main_window, 'set_status'):
            self.app.main_window.set_status("Drag modules from left panel to canvas", "blue")

    def _move_module_up(self, module: Module, parent_tab: Optional[Tuple[TabModule, str]] = None):
        """Move module up in its context (main canvas or within a tab)"""
        if parent_tab:
            # Module is in a tab - move within that tab
            tab_module, tab_name = parent_tab
            if tab_name in tab_module.sub_modules:
                modules = tab_module.sub_modules[tab_name]
                current_index = None
                for i, m in enumerate(modules):
                    if m.id == module.id:
                        current_index = i
                        break

                if current_index is not None and current_index > 0:
                    tab_module.reorder_module_in_tab(tab_name, module.id, current_index - 1)
                    self._refresh_tab_content(tab_module, tab_name)
                    self.app.set_modified(True)
        else:
            # Module is on main canvas
            self._move_module(module.id, -1)

    def _move_module_down(self, module: Module, parent_tab: Optional[Tuple[TabModule, str]] = None):
        """Move module down in its context (main canvas or within a tab)"""
        if parent_tab:
            # Module is in a tab - move within that tab
            tab_module, tab_name = parent_tab
            if tab_name in tab_module.sub_modules:
                modules = tab_module.sub_modules[tab_name]
                current_index = None
                for i, m in enumerate(modules):
                    if m.id == module.id:
                        current_index = i
                        break

                if current_index is not None and current_index < len(modules) - 1:
                    tab_module.reorder_module_in_tab(tab_name, module.id, current_index + 1)
                    self._refresh_tab_content(tab_module, tab_name)
                    self.app.set_modified(True)
        else:
            # Module is on main canvas
            self._move_module(module.id, 1)

    def _create_module_preview(self, parent: ctk.CTkFrame, module: Module):
        """Create preview of module content"""
        # Create a simplified preview based on module type
        preview_text = self._get_preview_text(module)

        preview_label = ctk.CTkLabel(
            parent,
            text=preview_text,
            font=("Arial", 11),
            justify="left",
            anchor="w",
            wraplength=400
        )
        preview_label.pack(fill="both", expand=True, padx=10, pady=10)

    def _on_tab_click(self, tab_module: TabModule, tab_name: str):
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

    def _switch_tab_content(self, tab_module: TabModule, new_active_tab: str):
        """Switch visible tab content without destroying widgets"""
        tab_module_widget = self.module_widgets.get(tab_module.id)
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

    def _update_tab_button_states(self, tab_module: TabModule):
        """Update the visual state of tab buttons"""
        tab_module_widget = self.module_widgets.get(tab_module.id)
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

    def _update_tab_header(self, tab_content_frame, tab_module: TabModule, tab_name: str):
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

    def _switch_active_tab(self, tab_module: TabModule, tab_name: str):
        """Switch the visible tab content with improved safety"""
        # Find the parent_frame of the tab_module
        if tab_module.id not in self.module_widgets:
            return

        tab_module_main_frame = self.module_widgets[tab_module.id]
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
            try:
                for i, tn in enumerate(tab_module.content_data['tabs']):
                    is_active = (tn == tab_name)
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

        # Create new content frame for the selected tab
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

    def _cleanup_tab_widget_references(self, tab_module_id: str):
        """Clean up widget references for a tab module before recreating them"""
        keys_to_remove = []
        for widget_key in list(self.module_widgets.keys()):  # Create a copy of keys
            if widget_key.startswith(f"{tab_module_id}:"):
                keys_to_remove.append(widget_key)

        for key in keys_to_remove:
            if key in self.module_widgets:
                widget = self.module_widgets[key]
                # Clear selection if this widget is currently selected
                if self.selected_widget == widget:
                    self.selected_widget = None
                del self.module_widgets[key]

    def _add_new_tab(self, tab_module: TabModule):
        """Add a new tab to the TabModule"""
        dialog = ctk.CTkInputDialog(text="Enter tab name:", title="New Tab")
        tab_name = dialog.get_input()

        if tab_name and tab_name not in tab_module.content_data['tabs']:
            tab_module.add_tab(tab_name)
            self._refresh_tab_module(tab_module)
            self.app.set_modified(True)

    def _refresh_tab_module(self, tab_module: TabModule):
        """Refresh the entire tab module widget - simplified version"""
        # Store the current active tab
        current_active_tab = tab_module.content_data.get('active_tab', 0)

        # Clean up all references first
        self._cleanup_tab_widget_references(tab_module.id)

        # Remove and recreate the widget
        if tab_module.id in self.module_widgets:
            widget = self.module_widgets[tab_module.id]
            if self._safe_widget_exists(widget):
                self._safe_destroy_widget(widget)
            del self.module_widgets[tab_module.id]

        # Clean up tab widget references
        if tab_module.id in self.tab_widgets:
            del self.tab_widgets[tab_module.id]

        # Recreate with the preserved active tab
        try:
            self.add_module_widget(tab_module, with_nested=True)

            # Ensure the correct tab is still active
            if current_active_tab < len(tab_module.content_data['tabs']):
                tab_module.content_data['active_tab'] = current_active_tab
                active_tab_name = tab_module.content_data['tabs'][current_active_tab]
                self._switch_tab_content(tab_module, active_tab_name)
                self._update_tab_button_states(tab_module)

        except Exception as e:
            print(f"Error refreshing tab module: {e}")

    def _refresh_tab_content(self, tab_module: TabModule, tab_name: str):
        """Refresh the content of a specific tab"""
        if tab_module.id not in self.tab_widgets or tab_name not in self.tab_widgets[tab_module.id]:
            return

        container = self.tab_widgets[tab_module.id][tab_name]
        if not self._safe_widget_exists(container):
            return

        # Clean up widget references for this specific tab before destroying widgets
        keys_to_remove = []
        for widget_key in list(self.module_widgets.keys()):
            if widget_key.startswith(f"{tab_module.id}:{tab_name}:"):
                keys_to_remove.append(widget_key)

        for key in keys_to_remove:
            if key in self.module_widgets:
                widget = self.module_widgets[key]
                if self.selected_widget == widget:
                    self.selected_widget = None
                del self.module_widgets[key]

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

    def remove_module_from_tab_widget(self, tab_module: TabModule, tab_name: str, module_id: str):
        """Remove a module widget from a tab"""
        widget_key = f"{tab_module.id}:{tab_name}:{module_id}"
        if widget_key in self.module_widgets:
            widget = self.module_widgets[widget_key]

            # Clear selection if this widget is currently selected
            if self.selected_widget == widget:
                self.selected_widget = None

            self._safe_destroy_widget(widget)
            del self.module_widgets[widget_key]

    def highlight_tab(self, tab_module: TabModule, tab_name: str):
        """Highlight a selected tab"""
        if tab_module.id in self.module_widgets:
            pass

    def _get_preview_text(self, module: Module) -> str:
        """Get preview text for module"""
        if module.module_type == 'header':
            return f"📄 {module.content_data.get('title', 'Header')}"
        elif module.module_type == 'text':
            content = module.content_data.get('content', '')[:100]
            return f"📝 {content}..." if len(content) >= 100 else f"📝 {content}"
        elif module.module_type == 'media':
            return f"🖼️ Media: {module.content_data.get('source', 'No source')}"
        elif module.module_type == 'step_card':
            return f"#{module.content_data.get('step_number', '1')} - {module.content_data.get('title', 'Step')}"
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

    def highlight_module(self, module: Module):
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

    def clear(self):
        """Clear all modules from canvas"""
        self.selected_widget = None

        # Notify drag drop handler to clean up
        self.drag_drop_handler.cleanup_on_canvas_clear()
        self.library_drag_drop_handler.cleanup_on_canvas_clear()

        # Destroy all widgets safely
        widgets_to_destroy = list(self.module_widgets.values())
        for widget in widgets_to_destroy:
            self._safe_destroy_widget(widget)

        # Clear all tracking dictionaries
        self.module_widgets.clear()
        self.tab_widgets.clear()
        self.widgets_being_destroyed.clear()

    def refresh_order(self):
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

    def update_module_preview(self, module: Module):
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
                                    grandchild.configure(text=self._get_preview_text(module))
                                except tk.TclError:
                                    pass
                                break
            except tk.TclError:
                pass

    def set_preview_mode(self, enabled: bool):
        """Toggle between edit and preview modes"""
        self.preview_mode = enabled

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
                    self.refresh_order()
            except tk.TclError:
                pass

    def _move_module(self, module_id: str, direction: int):
        """Move module up or down on main canvas"""
        module_index = None
        for i, module in enumerate(self.app.active_modules):
            if module.id == module_id:
                module_index = i
                break

        if module_index is not None:
            new_index = module_index + direction
            if 0 <= new_index < len(self.app.active_modules):
                self.app.reorder_modules(module_id, new_index)

    def _safe_select_module_click(self, module: Module, parent_tab: Optional[Tuple[TabModule, str]] = None):
        """Handle module selection clicks (separate from drag) with safety checks"""
        try:
            if not self.drag_drop_handler.is_dragging:
                self.app.select_module(module, parent_tab)
        except Exception as e:
            print(f"Error in module selection: {e}")

    def _safe_move_module_from_tab(self, module: Module, tab_module: TabModule, tab_name: str):
        """Safely move module from tab to main canvas"""
        try:
            self.app.move_module_from_tab(module, tab_module, tab_name)
        except Exception as e:
            print(f"Error moving module from tab: {e}")

    def _safe_move_module_up(self, module: Module, parent_tab: Optional[Tuple[TabModule, str]] = None):
        """Safely move module up"""
        try:
            self._move_module_up(module, parent_tab)
        except Exception as e:
            print(f"Error moving module up: {e}")

    def _safe_move_module_down(self, module: Module, parent_tab: Optional[Tuple[TabModule, str]] = None):
        """Safely move module down"""
        try:
            self._move_module_down(module, parent_tab)
        except Exception as e:
            print(f"Error moving module down: {e}")

    def _safe_remove_module(self, module_id: str):
        """Safely remove module"""
        try:
            self.app.remove_module(module_id)
        except Exception as e:
            print(f"Error removing module: {e}")
