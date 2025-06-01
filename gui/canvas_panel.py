# gui/canvas_panel.py
import customtkinter as ctk
from typing import Dict, Optional, Tuple, Any
from modules.base_module import Module
from modules.complex_module import TabModule
import tkinter as tk


class CanvasPanel:
    """Central panel for arranging modules with drag and drop support"""

    def __init__(self, parent, app_instance):
        self.parent = parent
        self.app = app_instance
        self.module_widgets: Dict[str, ctk.CTkFrame] = {}
        self.tab_widgets: Dict[str, Dict[str, ctk.CTkFrame]] = {}  # tab_module_id -> {tab_name -> frame}
        self.selected_widget: Optional[ctk.CTkFrame] = None
        self.preview_mode = False

        # Drag and drop state
        self.drag_data = None
        self.drop_zone_highlight = None
        self.drag_preview = None
        self.is_dragging = False

        # Track widgets scheduled for destruction to prevent access
        self.widgets_being_destroyed = set()

        self._setup_canvas()

    def _setup_canvas(self):
        """Initialize canvas layout"""
        # Create a frame to hold all module widgets
        self.modules_frame = ctk.CTkFrame(
            self.parent,
            fg_color=("gray92", "gray12")
        )
        self.modules_frame.pack(fill="both", expand=True, padx=10, pady=10)

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

            # Clear drag state if this widget is involved
            if self.drag_data and self.drag_data.get('source_widget') == widget:
                self._cleanup_drag()

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
                '<Enter>', '<Leave>', '<KeyRelease>', '<FocusIn>', '<FocusOut>'
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

        # Make frame draggable
        self._enable_drag_drop(module_frame, module)

    def _create_tab_content_areas(self, tab_module: TabModule, parent_frame: ctk.CTkFrame,
                                  with_nested: bool = False):
        """Create visual areas for tab content with proper module display"""
        # Create a frame for tab contents
        tab_container = ctk.CTkFrame(parent_frame, fg_color="gray20")
        tab_container.pack(fill="both", expand=True, padx=5, pady=(0, 5))

        # Initialize storage for this tab module
        if tab_module.id not in self.tab_widgets:
            self.tab_widgets[tab_module.id] = {}

        # Create tab selector
        tab_selector_frame = ctk.CTkFrame(tab_container, fg_color="gray25", height=35)
        tab_selector_frame.pack(fill="x", padx=2, pady=2)
        tab_selector_frame.pack_propagate(False)

        # Tab buttons
        for i, tab_name in enumerate(tab_module.content_data['tabs']):
            tab_btn = ctk.CTkButton(
                tab_selector_frame,
                text=tab_name,
                width=100,
                height=25,
                fg_color="gray30" if i == tab_module.content_data['active_tab'] else "gray40",
                command=lambda tn=tab_name, tm=tab_module: self._safe_on_tab_click(tm, tn)
            )
            tab_btn.pack(side="left", padx=2, pady=4)

        # Add "+" button to add new tab
        add_tab_btn = ctk.CTkButton(
            tab_selector_frame,
            text="+",
            width=30,
            height=25,
            command=lambda: self._safe_add_new_tab(tab_module)
        )
        add_tab_btn.pack(side="left", padx=2)

        # Create content frame for active tab
        active_tab_index = tab_module.content_data['active_tab']
        if 0 <= active_tab_index < len(tab_module.content_data['tabs']):
            active_tab = tab_module.content_data['tabs'][active_tab_index]
        else:
            if tab_module.content_data['tabs']:
                active_tab = tab_module.content_data['tabs'][0]
                tab_module.content_data['active_tab'] = 0
            else:
                return

        content_frame = ctk.CTkFrame(tab_container, fg_color="gray15")
        content_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Enable drop zone for this tab
        self._enable_tab_drop_zone(content_frame, tab_module, active_tab)

        # Header label for the tab content
        if active_tab in tab_module.sub_modules and tab_module.sub_modules[active_tab]:
            header_text = f"'{active_tab}' tab content ({len(tab_module.sub_modules[active_tab])} modules)"
        else:
            header_text = f"'{active_tab}' tab - Drop modules here or click to select"

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

        # Store the content frame
        self.tab_widgets[tab_module.id][active_tab] = modules_container

        # If loading from file, add existing nested modules
        if with_nested and active_tab in tab_module.sub_modules:
            for nested_module in sorted(tab_module.sub_modules[active_tab], key=lambda m: m.position):
                self.add_module_to_tab_widget(tab_module, active_tab, nested_module)

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
        """Enable the content frame as a drop zone for modules"""

        def on_click(event):
            if self._safe_widget_exists(content_frame):
                self._set_tab_context(tab_module, tab_name)

        # Bind click events
        content_frame.bind("<Button-1>", on_click)

        # Store drop zone info for drag detection
        content_frame._drop_zone_info = {
            'type': 'tab',
            'tab_module': tab_module,
            'tab_name': tab_name
        }

    def _set_tab_context(self, tab_module: TabModule, tab_name: str):
        """Set the selected tab context for adding new modules"""
        if not self.is_dragging:  # Only set context if not dragging
            self.app.selected_tab_context = (tab_module, tab_name)
            self.app.select_tab(tab_module, tab_name)

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

        # Enable drag and drop for this module
        self._enable_drag_drop(module_frame, module, parent_tab=(tab_module, tab_name))

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
        type_label.bind("<Button-1>", lambda e: self._safe_select_module_click(module, parent_tab))

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

    def _safe_select_module_click(self, module: Module, parent_tab: Optional[Tuple[TabModule, str]] = None):
        """Handle module selection clicks (separate from drag) with safety checks"""
        try:
            if not self.is_dragging:
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

    def _enable_drag_drop(self, frame: ctk.CTkFrame, module: Module,
                          parent_tab: Optional[Tuple[TabModule, str]] = None):
        """Enable drag and drop functionality for a module frame with safety checks"""

        # Get the drag handle
        drag_handle = getattr(frame, '_drag_handle', None)
        if not drag_handle or not self._safe_widget_exists(drag_handle):
            print(f"Warning: No valid drag handle found for module {module.id}")
            return

        def start_drag(event):
            if self.preview_mode or not self._safe_widget_exists(frame) or not self._safe_widget_exists(drag_handle):
                return

            self.is_dragging = True
            self.drag_data = {
                'module': module,
                'parent_tab': parent_tab,
                'start_x': event.x_root,
                'start_y': event.y_root,
                'source_widget': frame
            }

            # Create drag preview
            self._create_drag_preview(event.x_root, event.y_root, module.display_name)

            # Bind drag motion to the root window to track mouse movement
            try:
                self.app.root.bind('<B1-Motion>', on_drag_motion)
                self.app.root.bind('<ButtonRelease-1>', end_drag)
            except tk.TclError:
                self._cleanup_drag()
                return

            # Make frame semi-transparent during drag
            if self._safe_widget_exists(frame):
                try:
                    frame.configure(fg_color=("gray25", "gray25"))
                except tk.TclError:
                    pass

            # Change cursor
            if self._safe_widget_exists(drag_handle):
                try:
                    drag_handle.configure(cursor="hand2")
                except tk.TclError:
                    pass

        def on_drag_motion(event):
            if not self.drag_data or not self.is_dragging:
                return

            # Update drag preview position
            if self.drag_preview and self._safe_widget_exists(self.drag_preview):
                try:
                    self.drag_preview.geometry(f"200x40+{event.x_root + 10}+{event.y_root + 10}")
                except Exception:
                    pass

            # Check for drop zones
            try:
                widget_under_cursor = self.app.root.winfo_containing(event.x_root, event.y_root)
                self._update_drop_zone_highlight(widget_under_cursor)
            except tk.TclError:
                pass

        def end_drag(event):
            if not self.drag_data:
                return

            # Find drop target
            try:
                drop_target = self.app.root.winfo_containing(event.x_root, event.y_root)
                self._handle_drop(drop_target, event.x_root, event.y_root)
            except tk.TclError:
                pass

            # Cleanup
            self._cleanup_drag()

        # Bind specifically to the drag handle only with safety checks
        if self._safe_widget_exists(drag_handle):
            try:
                drag_handle.bind('<Button-1>', start_drag)
                drag_handle.configure(cursor="hand2")

                # Add hover effect to make it clear it's draggable
                def on_enter(event):
                    if not self.is_dragging and self._safe_widget_exists(drag_handle):
                        try:
                            drag_handle.configure(fg_color="gray40")
                        except tk.TclError:
                            pass

                def on_leave(event):
                    if not self.is_dragging and self._safe_widget_exists(drag_handle):
                        try:
                            drag_handle.configure(fg_color="gray30")
                        except tk.TclError:
                            pass

                drag_handle.bind('<Enter>', on_enter)
                drag_handle.bind('<Leave>', on_leave)
            except tk.TclError:
                pass

    def _create_drag_preview(self, x: int, y: int, module_name: str):
        """Create a visual preview of the dragged module"""
        try:
            self.drag_preview = ctk.CTkToplevel(self.app.root)
            self.drag_preview.overrideredirect(True)
            self.drag_preview.attributes('-alpha', 0.8)
            self.drag_preview.geometry(f"200x40+{x + 10}+{y + 10}")

            preview_label = ctk.CTkLabel(
                self.drag_preview,
                text=f"📦 {module_name}",
                fg_color="blue",
                corner_radius=5,
                font=("Arial", 10, "bold")
            )
            preview_label.pack(fill="both", expand=True, padx=2, pady=2)
        except Exception as e:
            print(f"Error creating drag preview: {e}")
            self.drag_preview = None

    def _update_drop_zone_highlight(self, widget_under_cursor):
        """Update visual feedback for drop zones"""
        # Clear previous highlight
        if self.drop_zone_highlight and self._safe_widget_exists(self.drop_zone_highlight):
            try:
                self.drop_zone_highlight.configure(fg_color=self.drop_zone_highlight._original_color)
            except (tk.TclError, AttributeError):
                pass
            self.drop_zone_highlight = None

        # Find drop zone
        drop_zone = self._find_drop_zone(widget_under_cursor)

        if drop_zone and self._safe_widget_exists(drop_zone):
            # Store original color and highlight
            if not hasattr(drop_zone, '_original_color'):
                try:
                    drop_zone._original_color = drop_zone.cget('fg_color')
                except tk.TclError:
                    drop_zone._original_color = "gray15"

            try:
                drop_zone.configure(fg_color="lightblue")
                self.drop_zone_highlight = drop_zone
            except tk.TclError:
                pass

    def _find_drop_zone(self, widget) -> Optional[ctk.CTkFrame]:
        """Find the nearest valid drop zone widget"""
        current = widget

        while current:
            # Check if widget still exists
            if not self._safe_widget_exists(current):
                try:
                    current = current.master
                    continue
                except (tk.TclError, AttributeError):
                    break

            # Check if this widget has drop zone info
            if hasattr(current, '_drop_zone_info'):
                return current

            # Check if this is the main modules frame (for main canvas drops)
            if current == self.modules_frame:
                return current

            # Check if this is a tab content frame
            if isinstance(current, (ctk.CTkFrame, ctk.CTkScrollableFrame)):
                for tab_id, tab_containers in self.tab_widgets.items():
                    for tab_name, container in tab_containers.items():
                        if not self._safe_widget_exists(container):
                            continue
                        if current == container or self._is_child_of(current, container):
                            # Add drop zone info if not present
                            if not hasattr(current, '_drop_zone_info'):
                                # Find the tab module
                                for module in self.app.active_modules:
                                    if isinstance(module, TabModule) and module.id == tab_id:
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

    def _handle_drop(self, drop_target, x: int, y: int):
        """Handle the drop operation"""
        if not self.drag_data:
            return

        dragged_module = self.drag_data['module']
        source_parent_tab = self.drag_data.get('parent_tab')

        drop_zone = self._find_drop_zone(drop_target)

        if not drop_zone:
            return  # Invalid drop

        # Determine drop action
        if hasattr(drop_zone, '_drop_zone_info'):
            drop_info = drop_zone._drop_zone_info
            if drop_info['type'] == 'tab':
                self._handle_drop_on_tab(dragged_module, drop_info['tab_module'], drop_info['tab_name'])
        elif drop_zone == self.modules_frame:
            self._handle_drop_on_main_canvas(dragged_module)

    def _handle_drop_on_tab(self, module: Module, target_tab_module: TabModule, tab_name: str):
        """Handle dropping a module onto a tab"""
        source_parent_tab = self.drag_data.get('parent_tab')

        # Remove from source
        if source_parent_tab:
            # Moving from another tab
            source_tab_module, source_tab_name = source_parent_tab
            removed_module = source_tab_module.remove_module_from_tab(source_tab_name, module.id)
            if removed_module:
                self.remove_module_from_tab_widget(source_tab_module, source_tab_name, module.id)
        else:
            # Moving from main canvas
            if module in self.app.active_modules:
                self.app.active_modules.remove(module)
                self.remove_module_widget(module.id)

        # Add to target tab
        if target_tab_module.add_module_to_tab(tab_name, module):
            # Check if target tab is currently active
            current_active_tab_index = target_tab_module.content_data.get('active_tab', 0)
            current_active_tab = None
            if 0 <= current_active_tab_index < len(target_tab_module.content_data['tabs']):
                current_active_tab = target_tab_module.content_data['tabs'][current_active_tab_index]

            if current_active_tab == tab_name:
                # The target tab is already active, add the widget directly
                self.add_module_to_tab_widget(target_tab_module, tab_name, module)
            else:
                # Switch to the target tab (this will recreate all widgets including the new one)
                target_tab_module.content_data['active_tab'] = target_tab_module.content_data['tabs'].index(tab_name)
                self._switch_active_tab(target_tab_module, tab_name)

            self.app.set_modified(True)

    def _handle_drop_on_main_canvas(self, module: Module):
        """Handle dropping a module onto the main canvas"""
        source_parent_tab = self.drag_data.get('parent_tab')

        if source_parent_tab:
            # Moving from a tab to main canvas
            source_tab_module, source_tab_name = source_parent_tab
            removed_module = source_tab_module.remove_module_from_tab(source_tab_name, module.id)
            if removed_module:
                self.remove_module_from_tab_widget(source_tab_module, source_tab_name, module.id)

                # Add to main canvas
                removed_module.position = len(self.app.active_modules)
                self.app.active_modules.append(removed_module)
                self.add_module_widget(removed_module)

                self.app._update_module_positions()
                self.app.set_modified(True)

    def _cleanup_drag(self):
        """Clean up drag and drop state with safety checks"""
        self.is_dragging = False

        if self.drag_preview:
            try:
                if self._safe_widget_exists(self.drag_preview):
                    self.drag_preview.destroy()
            except:
                pass
            self.drag_preview = None

        if self.drop_zone_highlight and self._safe_widget_exists(self.drop_zone_highlight):
            try:
                if hasattr(self.drop_zone_highlight, '_original_color'):
                    self.drop_zone_highlight.configure(fg_color=self.drop_zone_highlight._original_color)
                else:
                    self.drop_zone_highlight.configure(fg_color="gray15")
            except tk.TclError:
                pass
            self.drop_zone_highlight = None

        if self.drag_data and self.drag_data.get('source_widget'):
            # Restore original appearance
            source_widget = self.drag_data['source_widget']
            if self._safe_widget_exists(source_widget):
                try:
                    # Determine if it's a top-level or nested module
                    if hasattr(source_widget, '_parent_tab') and source_widget._parent_tab:
                        source_widget.configure(fg_color="gray18")  # nested module color
                    else:
                        source_widget.configure(fg_color="gray15")  # top-level module color
                except tk.TclError:
                    pass

        # Unbind root window events
        try:
            self.app.root.unbind('<B1-Motion>')
            self.app.root.unbind('<ButtonRelease-1>')
        except tk.TclError:
            pass

        self.drag_data = None

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
        """Handle tab selection"""
        # Update the active tab in the module
        if tab_name in tab_module.content_data['tabs']:
            tab_module.content_data['active_tab'] = tab_module.content_data['tabs'].index(tab_name)
            self._switch_active_tab(tab_module, tab_name)
            self.app.set_modified(True)

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
        """Refresh the entire tab module widget"""
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

        # Recreate
        try:
            self.add_module_widget(tab_module, with_nested=True)
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
