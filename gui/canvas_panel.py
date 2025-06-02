# gui/canvas_panel.py - Streamlined with tab widget management extracted
import customtkinter as ctk
from typing import Dict, Optional, Tuple, Any
from modules.base_module import Module
from modules.complex_module import TabModule
from gui.handlers.canvas_drag_drop_handler import CanvasDragDropHandler
from gui.handlers.library_drag_drop_handler import LibraryDragDropHandler
from gui.renderers.module_widget_manager import ModuleWidgetManager
from gui.renderers.tab_widget_manager import TabWidgetManager
import tkinter as tk


class CanvasPanel:
    """Central panel for arranging modules with enhanced drag and drop support"""

    def __init__(self, parent, app_instance):
        self.parent = parent
        self.app = app_instance
        self.preview_mode = False

        # Track widgets scheduled for destruction to prevent access
        self.widgets_being_destroyed = set()

        # Initialize drag and drop handlers
        self.drag_drop_handler = CanvasDragDropHandler(self, app_instance)
        self.library_drag_drop_handler = LibraryDragDropHandler(self, app_instance)

        self._setup_canvas()

        # Initialize module widget manager after canvas setup
        self.module_widget_manager = ModuleWidgetManager(
            modules_frame=self.modules_frame,
            app_instance=app_instance,
            drag_drop_handler=self.drag_drop_handler,
            safe_widget_exists_func=self._safe_widget_exists,
            safe_destroy_widget_func=self._safe_destroy_widget
        )

        # Initialize tab widget manager
        self.tab_widget_manager = TabWidgetManager(
            app_instance=app_instance,
            module_widget_manager=self.module_widget_manager,
            library_drag_drop_handler=self.library_drag_drop_handler,
            safe_widget_exists_func=self._safe_widget_exists,
            safe_destroy_widget_func=self._safe_destroy_widget
        )

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
            if hasattr(self.module_widget_manager, 'selected_widget') and self.module_widget_manager.selected_widget == widget:
                self.module_widget_manager.selected_widget = None

            # Clear library drop highlighting if this widget is highlighted
            if hasattr(self.library_drag_drop_handler, 'library_drop_highlight') and self.library_drag_drop_handler.library_drop_highlight == widget:
                self.library_drag_drop_handler.library_drop_highlight = None

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
        # Delegate to module widget manager
        self.module_widget_manager.add_module_widget(module, with_nested)

        # If it's a TabModule, create tab content areas using tab widget manager
        if isinstance(module, TabModule):
            # Get the main module frame that was just created
            module_frame = self.module_widget_manager.module_widgets.get(module.id)
            if module_frame:
                self.tab_widget_manager.create_tab_content_areas(module, module_frame, with_nested)

    def add_module_to_tab_widget(self, tab_module: TabModule, tab_name: str, module: Module):
        """Add a module widget to a specific tab - delegate to tab widget manager"""
        self.tab_widget_manager.add_module_to_tab_widget(tab_module, tab_name, module)

    def remove_module_from_tab_widget(self, tab_module: TabModule, tab_name: str, module_id: str):
        """Remove a module widget from a tab - delegate to tab widget manager"""
        self.tab_widget_manager.remove_module_from_tab_widget(tab_module, tab_name, module_id)

    def highlight_tab(self, tab_module: TabModule, tab_name: str):
        """Highlight a selected tab"""
        if tab_module.id in self.module_widget_manager.module_widgets:
            pass

    def highlight_module(self, module: Module):
        """Highlight the selected module - delegate to module widget manager"""
        self.module_widget_manager.highlight_module(module)

    def remove_module_widget(self, module_id: str):
        """Remove module widget from canvas - delegate to module widget manager"""
        self.module_widget_manager.remove_module_widget(module_id)

    def clear(self):
        """Clear all modules from canvas"""
        # Notify drag drop handler to clean up
        self.drag_drop_handler.cleanup_on_canvas_clear()
        self.library_drag_drop_handler.cleanup_on_canvas_clear()

        # Clear all module widgets via the manager
        self.module_widget_manager.clear_all_widgets()

        # Clear tab tracking dictionaries via tab widget manager
        self.tab_widget_manager.clear_all_tab_widgets()
        self.widgets_being_destroyed.clear()

    def refresh_order(self):
        """Refresh the visual order of modules - delegate to module widget manager"""
        self.module_widget_manager.refresh_widget_order()

    def update_module_preview(self, module: Module):
        """Update the preview for a specific module - delegate to module widget manager"""
        self.module_widget_manager.update_module_preview(module)

    def set_preview_mode(self, enabled: bool):
        """Toggle between edit and preview modes (FIXED VERSION)"""
        self.preview_mode = enabled

        if enabled:
            # Preview mode - hide editing controls but keep content visible
            self._hide_editing_controls()
        else:
            # Edit mode - show editing controls
            self._show_editing_controls()

    def _hide_editing_controls(self):
        """Hide editing controls for preview mode"""
        for widget_id, widget in self.module_widget_manager.module_widgets.items():
            if not self._safe_widget_exists(widget):
                continue

            try:
                # Find and hide control buttons in header
                for child in widget.winfo_children():
                    if isinstance(child, ctk.CTkFrame):  # Header frame
                        for grandchild in child.winfo_children():
                            if isinstance(grandchild, ctk.CTkFrame):  # Controls frame
                                grandchild.pack_forget()
                            elif hasattr(grandchild, 'text') and grandchild.cget('text') == '⋮⋮':
                                grandchild.pack_forget()  # Hide drag handle
            except tk.TclError:
                pass

        # Hide controls in tab modules too
        for tab_id, tab_containers in self.tab_widget_manager.tab_widgets.items():
            for tab_name, container in tab_containers.items():
                if self._safe_widget_exists(container):
                    # Hide tab controls
                    parent = container.master
                    while parent:
                        if hasattr(parent, '_tab_selector_frame'):
                            try:
                                parent._tab_selector_frame.pack_forget()
                                break
                            except:
                                pass
                        parent = getattr(parent, 'master', None)

    def _show_editing_controls(self):
        """Show editing controls for edit mode"""
        # Refresh the entire canvas to restore controls
        self.module_widget_manager.refresh_widget_order()

        # Restore tab controls
        for module in self.app.active_modules:
            if isinstance(module, TabModule):
                self.tab_widget_manager.refresh_tab_module(module)

    def clear_tab_context(self):
        """Clear the tab context and reset to main canvas adding"""
        self.app.selected_tab_context = None
        self.tab_widget_manager._clear_add_target_highlights()
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
                    self.tab_widget_manager.refresh_tab_content(tab_module, tab_name)
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
                    self.tab_widget_manager.refresh_tab_content(tab_module, tab_name)
                    self.app.set_modified(True)
        else:
            # Module is on main canvas
            self._move_module(module.id, 1)

    def _refresh_tab_module(self, tab_module: TabModule):
        """Refresh the entire tab module widget - delegate to tab widget manager"""
        self.tab_widget_manager.refresh_tab_module(tab_module)

    def _switch_active_tab(self, tab_module: TabModule, tab_name: str):
        """Switch the visible tab content - delegate to tab widget manager"""
        self.tab_widget_manager.switch_active_tab(tab_module, tab_name)

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

    # Provide property access to tab_widgets for backward compatibility
    @property
    def tab_widgets(self):
        """Access to tab widgets for backward compatibility"""
        return self.tab_widget_manager.tab_widgets

    # Delegated methods for library drag drop handler access
    def _find_library_drop_zone(self, widget):
        """Find library drop zone - delegate to library drag drop handler"""
        return self.library_drag_drop_handler.find_library_drop_zone(widget)

    def _clear_library_drop_highlight(self):
        """Clear library drop highlight - delegate to library drag drop handler"""
        self.library_drag_drop_handler.clear_library_drop_highlight()
