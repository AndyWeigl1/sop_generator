# gui/canvas_panel.py
import customtkinter as ctk
from typing import Dict, Optional, Tuple
from modules.base_module import Module
from modules.complex_module import TabModule

class CanvasPanel:
    """Central panel for arranging modules"""

    def __init__(self, parent, app_instance):
        self.parent = parent
        self.app = app_instance
        self.module_widgets: Dict[str, ctk.CTkFrame] = {}
        self.tab_widgets: Dict[str, Dict[str, ctk.CTkFrame]] = {} # tab_module_id -> {tab_name -> frame}
        self.selected_widget: Optional[ctk.CTkFrame] = None
        self.preview_mode = False

        self._setup_canvas()

    def _setup_canvas(self):
        """Initialize canvas layout"""
        # Create a frame to hold all module widgets
        self.modules_frame = ctk.CTkFrame(
            self.parent,
            fg_color=("gray92", "gray12")  # Changed from "transparent"
        )
        self.modules_frame.pack(fill="both", expand=True, padx=10, pady=10)

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

        # Make frame clickable
        self._bind_module_events(module_frame, module)


    def _create_tab_content_areas(self, tab_module: TabModule, parent_frame: ctk.CTkFrame,
                                with_nested: bool = False):
        """Create visual areas for tab content"""
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
                command=lambda tn=tab_name, tm=tab_module: self._on_tab_click(tm, tn)
            )
            tab_btn.pack(side="left", padx=2, pady=4)

        # Add "+" button to add new tab
        add_tab_btn = ctk.CTkButton(
            tab_selector_frame,
            text="+",
            width=30,
            height=25,
            command=lambda: self._add_new_tab(tab_module)
        )
        add_tab_btn.pack(side="left", padx=2)


        # Create content frame for active tab
        active_tab_index = tab_module.content_data['active_tab']
        if 0 <= active_tab_index < len(tab_module.content_data['tabs']):
            active_tab = tab_module.content_data['tabs'][active_tab_index]
        else:
            # Handle cases where active_tab_index might be out of bounds
            # or if tabs list is empty. Default to first tab or handle error.
            if tab_module.content_data['tabs']:
                active_tab = tab_module.content_data['tabs'][0]
                tab_module.content_data['active_tab'] = 0
            else:
                # No tabs exist, cannot create content frame for active tab yet
                return


        content_frame = ctk.CTkFrame(tab_container, fg_color="gray15")
        content_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Create drop zone for adding modules to this tab
        drop_zone = ctk.CTkFrame(content_frame, fg_color="gray18", height=40)
        drop_zone.pack(fill="x", padx=5, pady=5)

        drop_label = ctk.CTkLabel(
            drop_zone,
            text=f"+ Add modules to '{active_tab}' tab",
            text_color="gray",
            cursor="hand2"
        )
        drop_label.pack(pady=10)

        # Make drop zone clickable
        drop_zone.bind("<Button-1>", lambda e, tm=tab_module, at=active_tab: self._on_tab_dropzone_click(tm, at))
        drop_label.bind("<Button-1>", lambda e, tm=tab_module, at=active_tab: self._on_tab_dropzone_click(tm, at))


        # Container for modules in this tab
        modules_container = ctk.CTkFrame(content_frame, fg_color="gray15")
        modules_container.pack(fill="both", expand=True, padx=5)

        # Store the content frame
        self.tab_widgets[tab_module.id][active_tab] = modules_container

        # If loading from file, add existing nested modules
        if with_nested and active_tab in tab_module.sub_modules:
            for nested_module in sorted(tab_module.sub_modules[active_tab], key=lambda m: m.position):
                self.add_module_to_tab_widget(tab_module, active_tab, nested_module)

    def add_module_to_tab_widget(self, tab_module: TabModule, tab_name: str, module: Module):
        """Add a module widget to a specific tab"""
        if tab_module.id not in self.tab_widgets:
            return

        # Get or create the container for this tab
        if tab_name not in self.tab_widgets[tab_module.id]:
            # Tab doesn't have a visual container yet, create it
            self._switch_active_tab(tab_module, tab_name)  # This needs to ensure the container is made

        container = self.tab_widgets[tab_module.id].get(tab_name)
        if not container:
            # If _switch_active_tab doesn't create it or it's still missing
            print(f"Error: Container for tab '{tab_name}' not found after attempting to switch/create.")
            return

        # Create module frame
        module_frame = self._create_module_frame(module, is_top_level=False, parent_tab=(tab_module, tab_name))
        module_frame.pack(fill="x", padx=5, pady=5)

        # Store reference (with tab context in the key)
        widget_key = f"{tab_module.id}:{tab_name}:{module.id}"
        self.module_widgets[widget_key] = module_frame

        # Bind events
        self._bind_module_events(module_frame, module, parent_tab=(tab_module, tab_name))

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
                parent_widget = self.tab_widgets[tab_module_id][tab_name]
            else:
                print(f"Error: Parent container for tab {tab_name} of module {tab_module_id} not found.")
                parent_widget = self.modules_frame

        module_frame = ctk.CTkFrame(
            parent_widget,
            fg_color=frame_color,
            border_width=2,
            border_color=border_color
        )

        # Create header with module type and controls
        header_frame = ctk.CTkFrame(module_frame, fg_color="gray20", height=30)
        header_frame.pack(fill="x", padx=2, pady=2)
        header_frame.pack_propagate(False)

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
                command=lambda m=module, pt0=parent_tab[0], pt1=parent_tab[1]: self.app.move_module_from_tab(m, pt0,
                                                                                                             pt1)
            )
            move_out_btn.pack(side="left", padx=2)

        # Standard controls
        # Move up button - FIXED: pass module.id and handle parent_tab context properly
        up_btn = ctk.CTkButton(
            controls_frame,
            text="↑",
            width=25,
            height=25,
            command=lambda: self._move_module_up(module, parent_tab)
        )
        up_btn.pack(side="left", padx=2)

        # Move down button - FIXED: pass module.id and handle parent_tab context properly
        down_btn = ctk.CTkButton(
            controls_frame,
            text="↓",
            width=25,
            height=25,
            command=lambda: self._move_module_down(module, parent_tab)
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
            command=lambda mid=module.id: self.app.remove_module(mid)
        )
        delete_btn.pack(side="left", padx=2)

        # Content preview
        preview_frame = ctk.CTkFrame(module_frame, fg_color="gray10")
        preview_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Add module preview content
        self._create_module_preview(preview_frame, module)

        return module_frame

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
            # self.app.select_tab(tab_module, tab_name) # Assuming app has such a method
            self._switch_active_tab(tab_module, tab_name)
            self.app.set_modified(True)  # Assuming app has such a method

    def _switch_active_tab(self, tab_module: TabModule, tab_name: str):
        """Switch the visible tab content"""
        # This would update the visual display to show the selected tab's content
        # For simplicity, we'll just update the drop zone label
        # In a full implementation, you'd hide/show different content containers

        # Find the parent_frame of the tab_module (its main widget)
        if tab_module.id not in self.module_widgets:
            return
        tab_module_main_frame = self.module_widgets[tab_module.id]

        # Find tab_container within tab_module_main_frame
        # This assumes a certain structure created in _create_tab_content_areas
        tab_container = None
        for child in tab_module_main_frame.winfo_children():
            if isinstance(child, ctk.CTkFrame) and child.cget("fg_color") == "gray20":  # Heuristic
                tab_container = child
                break
        if not tab_container: return

        # Destroy existing content_frame (the one with fg_color="gray15")
        for widget in tab_container.winfo_children():
            # Avoid destroying the tab_selector_frame
            if widget.cget("fg_color") == "gray15":  # Heuristic for content_frame
                widget.destroy()

        # Recreate tab buttons to update their colors
        tab_selector_frame = None
        for child in tab_container.winfo_children():
            if isinstance(child, ctk.CTkFrame) and child.cget("fg_color") == "gray25":
                tab_selector_frame = child
                break

        if tab_selector_frame:
            for widget in tab_selector_frame.winfo_children():
                widget.destroy()  # Clear old buttons

            for i, tn in enumerate(tab_module.content_data['tabs']):
                is_active = (tn == tab_name)
                tab_btn = ctk.CTkButton(
                    tab_selector_frame,
                    text=tn,
                    width=100,
                    height=25,
                    fg_color="gray30" if is_active else "gray40",
                    command=lambda t_name=tn, tm=tab_module: self._on_tab_click(tm, t_name)
                )
                tab_btn.pack(side="left", padx=2, pady=4)

            add_tab_btn = ctk.CTkButton(
                tab_selector_frame,
                text="+",
                width=30,
                height=25,
                command=lambda tm=tab_module: self._add_new_tab(tm)
            )
            add_tab_btn.pack(side="left", padx=2)

        # Create new content frame for the selected tab
        content_frame = ctk.CTkFrame(tab_container, fg_color="gray15")
        content_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Create drop zone
        drop_zone = ctk.CTkFrame(content_frame, fg_color="gray18", height=40)
        drop_zone.pack(fill="x", padx=5, pady=5)
        drop_label = ctk.CTkLabel(
            drop_zone,
            text=f"+ Add modules to '{tab_name}' tab",
            text_color="gray",
            cursor="hand2"
        )
        drop_label.pack(pady=10)
        drop_zone.bind("<Button-1>", lambda e, tm=tab_module, tn=tab_name: self._on_tab_dropzone_click(tm, tn))
        drop_label.bind("<Button-1>", lambda e, tm=tab_module, tn=tab_name: self._on_tab_dropzone_click(tm, tn))

        # Container for modules in this tab
        modules_container = ctk.CTkFrame(content_frame, fg_color="gray15")
        modules_container.pack(fill="both", expand=True, padx=5)

        # Store the new content frame
        self.tab_widgets[tab_module.id][tab_name] = modules_container

        # Re-add modules for this tab
        if tab_name in tab_module.sub_modules:
            for nested_module in sorted(tab_module.sub_modules[tab_name], key=lambda m: m.position):
                self.add_module_to_tab_widget(tab_module, tab_name, nested_module)

    def _add_new_tab(self, tab_module: TabModule):
        """Add a new tab to the TabModule"""
        # Simple dialog to get tab name
        dialog = ctk.CTkInputDialog(text="Enter tab name:", title="New Tab")
        tab_name = dialog.get_input()

        if tab_name and tab_name not in tab_module.content_data['tabs']:
            tab_module.add_tab(tab_name) # Assuming TabModule has this method
            # Refresh the tab module widget
            self._refresh_tab_module(tab_module)
            self.app.set_modified(True) # Assuming app has such a method

    def _bind_module_events(self, frame: ctk.CTkFrame, module: Module,
                            parent_tab: Optional[Tuple[TabModule, str]] = None):
        """Bind click events to module frame"""
        # Capture current values for lambda
        current_module = module
        current_parent_tab = parent_tab

        frame.bind("<Button-1>", lambda e: self.app.select_module(current_module, current_parent_tab))
        for child in frame.winfo_children():
            # Only bind to direct children that are frames, avoid binding to all sub-widgets like buttons
            if isinstance(child, ctk.CTkFrame):
                child.bind("<Button-1>", lambda e: self.app.select_module(current_module, current_parent_tab))
            # Deeper binding might be needed if clicks on labels etc. should also select
            # but be careful not to override other specific bindings (like on buttons)

    def _refresh_tab_module(self, tab_module: TabModule):
        """Refresh the entire tab module widget"""
        # Remove and recreate the widget
        if tab_module.id in self.module_widgets:
            self.module_widgets[tab_module.id].destroy()
            del self.module_widgets[tab_module.id]

        # Clean up tab widget references (the actual widgets are already destroyed)
        if tab_module.id in self.tab_widgets:
            del self.tab_widgets[tab_module.id]

        # Recreate
        self.add_module_widget(tab_module, with_nested=True)

    def _refresh_tab_content(self, tab_module: TabModule, tab_name: str):
        """Refresh the content of a specific tab"""
        if tab_module.id in self.tab_widgets and tab_name in self.tab_widgets[tab_module.id]:
            container = self.tab_widgets[tab_module.id][tab_name]

            # Clear existing widgets in the container
            for widget in container.winfo_children():
                widget.destroy()

            # Re-add modules in correct order
            if tab_name in tab_module.sub_modules:
                for module in sorted(tab_module.sub_modules.get(tab_name, []), key=lambda m: m.position):
                    self.add_module_to_tab_widget(tab_module, tab_name, module)

    def remove_module_from_tab_widget(self, tab_module: TabModule, tab_name: str, module_id: str):
        """Remove a module widget from a tab"""
        widget_key = f"{tab_module.id}:{tab_name}:{module_id}"
        if widget_key in self.module_widgets:
            widget = self.module_widgets[widget_key]

            # Clear selection if this widget is currently selected
            if self.selected_widget == widget:
                self.selected_widget = None

            widget.destroy()
            del self.module_widgets[widget_key]

    def highlight_tab(self, tab_module: TabModule, tab_name: str):
        """Highlight a selected tab"""
        # Update visual indication of selected tab
        if tab_module.id in self.module_widgets:
            # self.highlight_module(tab_module) # Assuming this method exists and highlights the main module frame
            pass # Main module frame highlighting might be handled by select_module
        # Additional tab-specific highlighting could be added here
        # e.g., changing the style of the tab button itself via _switch_active_tab or similar logic

    def _on_tab_dropzone_click(self, tab_module: TabModule, tab_name: str):
        """Handle click on tab drop zone to add modules"""
        # self.app.select_tab(tab_module, tab_name) # Assuming app has such a method
        print(f"Dropzone clicked for tab: {tab_name} in module: {tab_module.id}")
        # Here you would typically open a dialog or module selection menu
        # and then call self.app.add_module_to_tab(tab_module, tab_name, selected_new_module)

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
        else:
            return f"{module.display_name}"

    def highlight_module(self, module: Module):
        """Highlight the selected module"""
        # Remove previous highlight (with error handling for destroyed widgets)
        if self.selected_widget:
            try:
                self.selected_widget.configure(border_color=("gray15", "gray15"))
            except Exception:
                # Widget was destroyed, clear the reference
                self.selected_widget = None

        # Add highlight to selected module
        if module.id in self.module_widgets:
            widget = self.module_widgets[module.id]
            try:
                widget.configure(border_color="blue")
                self.selected_widget = widget
            except Exception:
                # Widget is invalid, remove from tracking
                del self.module_widgets[module.id]
                self.selected_widget = None

    def remove_module_widget(self, module_id: str):
        """Remove module widget from canvas"""
        if module_id in self.module_widgets:
            widget = self.module_widgets[module_id]

            # Clear selection if this widget is currently selected
            if self.selected_widget == widget:
                self.selected_widget = None

            widget.destroy()
            del self.module_widgets[module_id]

            # Also clean up any tab-related widgets for this module
            keys_to_remove = [key for key in self.module_widgets.keys() if key.startswith(f"{module_id}:")]
            for key in keys_to_remove:
                if self.module_widgets[key] == self.selected_widget:
                    self.selected_widget = None
                self.module_widgets[key].destroy()
                del self.module_widgets[key]

    def clear(self):
        """Clear all modules from canvas"""
        # Clear selection first
        self.selected_widget = None

        # Destroy all widgets
        for widget in self.module_widgets.values():
            try:
                widget.destroy()
            except Exception:
                # Widget already destroyed, ignore
                pass

        # Clear all tracking dictionaries
        self.module_widgets.clear()
        self.tab_widgets.clear()

    def refresh_order(self):
        """Refresh the visual order of modules"""
        # Get all modules from app sorted by position
        modules = sorted(self.app.active_modules, key=lambda m: m.position)

        # Repack all widgets in correct order
        for module in modules:
            if module.id in self.module_widgets:
                self.module_widgets[module.id].pack_forget()
                self.module_widgets[module.id].pack(fill="x", padx=5, pady=5)

    def update_module_preview(self, module: Module):
        """Update the preview for a specific module"""
        if module.id in self.module_widgets:
            widget = self.module_widgets[module.id]

            # Find and update the preview label
            for child in widget.winfo_children():
                if isinstance(child, ctk.CTkFrame):
                    for grandchild in child.winfo_children():
                        if isinstance(grandchild, ctk.CTkLabel) and grandchild.cget("font") == ("Arial", 11):
                            grandchild.configure(text=self._get_preview_text(module))
                            break

    def set_preview_mode(self, enabled: bool):
        """Toggle between edit and preview modes"""
        self.preview_mode = enabled

        # Update visual state of all widgets
        for widget in self.module_widgets.values():
            if enabled:
                # Hide controls in preview mode
                for child in widget.winfo_children():
                    if isinstance(child, ctk.CTkFrame):
                        # Find header frame with controls
                        for grandchild in child.winfo_children():
                            if isinstance(grandchild, ctk.CTkFrame):
                                grandchild.pack_forget()
            else:
                # Show controls in edit mode
                self.refresh_order()

    def _move_module(self, module_id: str, direction: int):
        """Move module up or down on main canvas"""
        # Find module position
        module_index = None
        for i, module in enumerate(self.app.active_modules):
            if module.id == module_id:
                module_index = i
                break

        if module_index is not None:
            new_index = module_index + direction
            if 0 <= new_index < len(self.app.active_modules):
                self.app.reorder_modules(module_id, new_index)

    def _enable_drag(self, widget: ctk.CTkFrame, module: Module):
        """Enable drag functionality for module widget"""
        widget.bind("<Button-1>", lambda e: self._start_drag(e, module))
        widget.bind("<B1-Motion>", self._on_drag)
        widget.bind("<ButtonRelease-1>", self._stop_drag)

    def _start_drag(self, event, module: Module):
        """Start dragging a module"""
        self.drag_data = {
            "module": module,
            "start_y": event.y_root,
            "widget": event.widget
        }

    def _on_drag(self, event):
        """Handle drag motion"""
        # Visual feedback during drag could be added here
        pass

    def _stop_drag(self, event):
        """Stop dragging and reorder if needed"""
        if hasattr(self, 'drag_data'):
            # Calculate new position based on mouse position
            # This is a simplified version - you can enhance it
            del self.drag_data


