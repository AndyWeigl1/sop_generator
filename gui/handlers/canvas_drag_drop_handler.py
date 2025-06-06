# gui/handlers/canvas_drag_drop_handler.py

import customtkinter as ctk
from typing import Optional, Dict, Any, Tuple, TYPE_CHECKING
import tkinter as tk
from gui.utils.widget_safety import safe_widget_exists, is_child_of

if TYPE_CHECKING:
    from gui.canvas_panel import CanvasPanel
    from modules.base_module import Module
    from modules.complex_module import TabModule


class CanvasDragDropHandler:

    def __init__(self, canvas_panel: 'CanvasPanel', app_instance):
        self.canvas_panel = canvas_panel
        self.app = app_instance

        # Drag and drop state
        self.drag_data: Optional[Dict[str, Any]] = None
        self.drop_zone_highlight: Optional[ctk.CTkFrame] = None
        self.drag_preview: Optional[ctk.CTkToplevel] = None
        self.is_dragging = False

    def enable_drag_drop(self, frame: ctk.CTkFrame, module: 'Module',
                         parent_tab: Optional[Tuple['TabModule', str]] = None):
        """Enable drag and drop functionality for a module frame with safety checks"""

        # Get the drag handle
        drag_handle = getattr(frame, '_drag_handle', None)
        if not drag_handle or not safe_widget_exists(drag_handle):
            print(f"Warning: No valid drag handle found for module {module.id}")
            return

        def start_drag(event):
            if (self.canvas_panel.preview_mode or
                    not safe_widget_exists(frame) or
                    not safe_widget_exists(drag_handle)):
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
            if safe_widget_exists(frame):
                try:
                    frame.configure(fg_color=("gray25", "gray25"))
                except tk.TclError:
                    pass

            # Change cursor
            if safe_widget_exists(drag_handle):
                try:
                    drag_handle.configure(cursor="hand2")
                except tk.TclError:
                    pass

        def on_drag_motion(event):
            if not self.drag_data or not self.is_dragging:
                return

            # Update drag preview position
            if self.drag_preview and safe_widget_exists(self.drag_preview):
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
        if safe_widget_exists(drag_handle):
            try:
                drag_handle.bind('<Button-1>', start_drag)
                drag_handle.configure(cursor="hand2")

                # Add hover effect to make it clear it's draggable
                def on_enter(event):
                    if not self.is_dragging and safe_widget_exists(drag_handle):
                        try:
                            drag_handle.configure(fg_color="gray40")
                        except tk.TclError:
                            pass

                def on_leave(event):
                    if not self.is_dragging and safe_widget_exists(drag_handle):
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
        if self.drop_zone_highlight and safe_widget_exists(self.drop_zone_highlight):
            try:
                self.drop_zone_highlight.configure(fg_color=self.drop_zone_highlight._original_color)
            except (tk.TclError, AttributeError):
                pass
            self.drop_zone_highlight = None

        # Find drop zone
        drop_zone = self._find_drop_zone(widget_under_cursor)

        if drop_zone and safe_widget_exists(drop_zone):
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
            if not safe_widget_exists(current):
                try:
                    current = current.master
                    continue
                except (tk.TclError, AttributeError):
                    break

            # Check if this widget has drop zone info
            if hasattr(current, '_drop_zone_info'):
                return current

            # Check if this is the main modules frame (for main canvas drops)
            if current == self.canvas_panel.modules_frame:
                return current

            # Check if this is a tab content frame
            if isinstance(current, (ctk.CTkFrame, ctk.CTkScrollableFrame)):
                for tab_id, tab_containers in self.canvas_panel.tab_widgets.items():
                    for tab_name, container in tab_containers.items():
                        if not safe_widget_exists(container):
                            continue
                        if current == container or is_child_of(current, container):
                            # Add drop zone info if not present
                            if not hasattr(current, '_drop_zone_info'):
                                # Find the tab module
                                for module in self.app.active_modules:
                                    if hasattr(module, 'id') and hasattr(module, 'sub_modules') and module.id == tab_id:
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
        elif drop_zone == self.canvas_panel.modules_frame:
            self._handle_drop_on_main_canvas(dragged_module)

    def _handle_drop_on_tab(self, module: 'Module', target_tab_module: 'TabModule', tab_name: str):
        """Handle dropping a module onto a tab"""
        source_parent_tab = self.drag_data.get('parent_tab')

        # Remove from source
        if source_parent_tab:
            # Moving from another tab
            source_tab_module, source_tab_name = source_parent_tab
            removed_module = source_tab_module.remove_module_from_tab(source_tab_name, module.id)
            if removed_module:
                self.canvas_panel.remove_module_from_tab_widget(source_tab_module, source_tab_name, module.id)
        else:
            # Moving from main canvas
            if module in self.app.active_modules:
                self.app.active_modules.remove(module)
                self.canvas_panel.remove_module_widget(module.id)

        # Add to target tab
        if target_tab_module.add_module_to_tab(tab_name, module):
            # Check if target tab is currently active
            current_active_tab_index = target_tab_module.content_data.get('active_tab', 0)
            current_active_tab = None
            if 0 <= current_active_tab_index < len(target_tab_module.content_data['tabs']):
                current_active_tab = target_tab_module.content_data['tabs'][current_active_tab_index]

            if current_active_tab == tab_name:
                # The target tab is already active, add the widget directly
                self.canvas_panel.add_module_to_tab_widget(target_tab_module, tab_name, module)
            else:
                # Switch to the target tab (this will recreate all widgets including the new one)
                target_tab_module.content_data['active_tab'] = target_tab_module.content_data['tabs'].index(tab_name)
                self.canvas_panel._switch_active_tab(target_tab_module, tab_name)

            self.app.set_modified(True)

    def _handle_drop_on_main_canvas(self, module: 'Module'):
        """Handle dropping a module onto the main canvas"""
        source_parent_tab = self.drag_data.get('parent_tab')

        if source_parent_tab:
            # Moving from a tab to main canvas
            source_tab_module, source_tab_name = source_parent_tab
            removed_module = source_tab_module.remove_module_from_tab(source_tab_name, module.id)
            if removed_module:
                self.canvas_panel.remove_module_from_tab_widget(source_tab_module, source_tab_name, module.id)

                # Add to main canvas
                removed_module.position = len(self.app.active_modules)
                self.app.active_modules.append(removed_module)
                self.canvas_panel.add_module_widget(removed_module)

                self.app._update_module_positions()
                self.app.set_modified(True)

    def _cleanup_drag(self):
        """Clean up drag and drop state with safety checks"""
        self.is_dragging = False

        if self.drag_preview:
            try:
                if safe_widget_exists(self.drag_preview):
                    self.drag_preview.destroy()
            except:
                pass
            self.drag_preview = None

        if self.drop_zone_highlight and safe_widget_exists(self.drop_zone_highlight):
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
            if safe_widget_exists(source_widget):
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

    def cleanup_on_canvas_clear(self):
        """Clean up drag state when canvas is cleared"""
        if self.is_dragging:
            self._cleanup_drag()
