# gui/canvas_panel.py
import customtkinter as ctk
from typing import Dict, Optional
from modules.base_module import Module


class CanvasPanel:
    """Central panel for arranging modules"""

    def __init__(self, parent, app_instance):
        self.parent = parent
        self.app = app_instance
        self.module_widgets: Dict[str, ctk.CTkFrame] = {}
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

    def add_module_widget(self, module: Module):
        """Add visual representation of module"""
        # Create a frame for the module
        module_frame = ctk.CTkFrame(
            self.modules_frame,
            fg_color="gray15",
            border_width=2,
            border_color=("gray15", "gray15")  # Changed from "transparent"
        )
        module_frame.pack(fill="x", padx=5, pady=5)

        # Create header with module type and controls
        header_frame = ctk.CTkFrame(module_frame, fg_color="gray20", height=30)
        header_frame.pack(fill="x", padx=2, pady=2)
        header_frame.pack_propagate(False)

        # Module type label
        type_label = ctk.CTkLabel(
            header_frame,
            text=module.display_name,
            font=("Arial", 12, "bold")
        )
        type_label.pack(side="left", padx=10)

        # Control buttons
        controls_frame = ctk.CTkFrame(header_frame, fg_color="gray20")  # Changed from "transparent"
        controls_frame.pack(side="right", padx=5)

        # Move up button
        up_btn = ctk.CTkButton(
            controls_frame,
            text="↑",
            width=25,
            height=25,
            command=lambda: self._move_module(module.id, -1)
        )
        up_btn.pack(side="left", padx=2)

        # Move down button
        down_btn = ctk.CTkButton(
            controls_frame,
            text="↓",
            width=25,
            height=25,
            command=lambda: self._move_module(module.id, 1)
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
            command=lambda: self.app.remove_module(module.id)
        )
        delete_btn.pack(side="left", padx=2)

        # Content preview
        preview_frame = ctk.CTkFrame(module_frame, fg_color="gray10")
        preview_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Add module preview content
        self._create_module_preview(preview_frame, module)

        # Store reference
        self.module_widgets[module.id] = module_frame

        # Make frame clickable
        module_frame.bind("<Button-1>", lambda e: self.app.select_module(module))
        preview_frame.bind("<Button-1>", lambda e: self.app.select_module(module))

        # Enable drag functionality
        self._enable_drag(module_frame, module)

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
        # Remove previous highlight
        if self.selected_widget:
            self.selected_widget.configure(border_color=("gray15", "gray15"))  # Changed from "transparent"

        # Add highlight to selected module
        if module.id in self.module_widgets:
            widget = self.module_widgets[module.id]
            widget.configure(border_color="blue")
            self.selected_widget = widget

    def remove_module_widget(self, module_id: str):
        """Remove module widget from canvas"""
        if module_id in self.module_widgets:
            widget = self.module_widgets[module_id]
            widget.destroy()
            del self.module_widgets[module_id]

    def clear(self):
        """Clear all modules from canvas"""
        for widget in self.module_widgets.values():
            widget.destroy()
        self.module_widgets.clear()
        self.selected_widget = None

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
        """Move module up or down"""
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