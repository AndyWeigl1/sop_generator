# gui/properties_panel.py
import customtkinter as ctk
from typing import Dict, Optional, Any
from modules.base_module import Module
from tkinter import filedialog


class PropertiesPanel:
    """Panel for editing module properties"""

    def __init__(self, parent, app_instance):
        self.parent = parent
        self.app = app_instance
        self.current_module: Optional[Module] = None
        self.property_widgets: Dict[str, ctk.CTkBaseClass] = {}

        # Create a frame for the content
        self.content_frame = ctk.CTkFrame(parent, fg_color=("gray90", "gray15"))  # Changed from "transparent"
        self.content_frame.pack(fill="both", expand=True)

        # Show empty state initially
        self._show_empty_state()

    def _show_empty_state(self):
        """Show empty state when no module is selected"""
        self.clear()
        empty_label = ctk.CTkLabel(
            self.content_frame,
            text="Select a module to edit its properties",
            text_color="gray"
        )
        empty_label.pack(pady=50)

    def clear(self):
        """Clear all property widgets"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        self.property_widgets.clear()
        self.current_module = None

    def show_module_properties(self, module: Module):
        """Display properties for the selected module"""
        self.clear()
        self.current_module = module

        # Module name header
        header_frame = ctk.CTkFrame(self.content_frame, fg_color=("gray90", "gray15"))  # Changed from "transparent"
        header_frame.pack(fill="x", padx=10, pady=(10, 20))

        module_label = ctk.CTkLabel(
            header_frame,
            text=module.display_name,
            font=("Arial", 16, "bold")
        )
        module_label.pack(side="left")

        # Delete button
        delete_btn = ctk.CTkButton(
            header_frame,
            text="Delete",
            width=60,
            fg_color="darkred",
            hover_color="red",
            command=lambda: self._delete_module()
        )
        delete_btn.pack(side="right")

        # Create property fields
        fields = module.get_property_fields()
        for field_name, field_type in fields.items():
            self._create_property_field(field_name, field_type, module)

    def _create_property_field(self, field_name: str, field_type: str, module: Module):
        """Create a property field based on its type"""
        # Frame for the field
        field_frame = ctk.CTkFrame(self.content_frame, fg_color=("gray90", "gray15"))  # Changed from "transparent"
        field_frame.pack(fill="x", padx=10, pady=5)

        # Label
        label = ctk.CTkLabel(
            field_frame,
            text=field_name.replace('_', ' ').title() + ":",
            width=120,
            anchor="w"
        )
        label.pack(side="left", padx=(0, 10))

        # Get current value
        current_value = module.content_data.get(field_name, "")

        # Create appropriate widget based on field type
        if field_type == "text":
            widget = ctk.CTkEntry(field_frame, width=200)
            widget.insert(0, str(current_value))
            widget.bind("<KeyRelease>", lambda e: self._on_property_change(field_name, widget.get()))

        elif field_type == "textarea":
            widget = ctk.CTkTextbox(field_frame, height=80, width=200)
            widget.insert("1.0", str(current_value))
            widget.bind("<KeyRelease>", lambda e: self._on_property_change(field_name, widget.get("1.0", "end-1c")))

        elif field_type.startswith("dropdown:"):
            options = field_type.split(":")[1].split(",")
            widget = ctk.CTkComboBox(field_frame, values=options, width=200)
            widget.set(str(current_value) if current_value in options else options[0])
            widget.configure(command=lambda value: self._on_property_change(field_name, value))

        elif field_type == "checkbox":
            widget = ctk.CTkCheckBox(field_frame, text="", width=20)
            if current_value:
                widget.select()
            widget.configure(command=lambda: self._on_property_change(field_name, widget.get()))

        elif field_type == "file" or field_type == "file_or_url":
            # Frame for file input
            file_frame = ctk.CTkFrame(field_frame, fg_color=("gray90", "gray15"))  # Changed from "transparent"
            file_frame.pack(side="left", fill="x", expand=True)

            widget = ctk.CTkEntry(file_frame, width=150)
            widget.insert(0, str(current_value))
            widget.bind("<KeyRelease>", lambda e: self._on_property_change(field_name, widget.get()))
            widget.pack(side="left", padx=(0, 5))

            browse_btn = ctk.CTkButton(
                file_frame,
                text="Browse",
                width=50,
                command=lambda: self._browse_file(field_name, widget)
            )
            browse_btn.pack(side="left")

        elif field_type == "number":
            widget = ctk.CTkEntry(field_frame, width=200)
            widget.insert(0, str(current_value))
            widget.bind("<KeyRelease>", lambda e: self._on_property_change(field_name, widget.get()))

        elif field_type == "list_editor":
            # For simple lists, use a text widget with comma separation
            widget = ctk.CTkEntry(field_frame, width=200)
            if isinstance(current_value, list):
                widget.insert(0, ", ".join(str(v) for v in current_value))
            else:
                widget.insert(0, str(current_value))
            widget.bind("<KeyRelease>", lambda e: self._on_property_change(field_name, widget.get()))

        else:
            # Default to text entry
            widget = ctk.CTkEntry(field_frame, width=200)
            widget.insert(0, str(current_value))
            widget.bind("<KeyRelease>", lambda e: self._on_property_change(field_name, widget.get()))

        widget.pack(side="left", fill="x", expand=True)
        self.property_widgets[field_name] = widget

    def _on_property_change(self, field_name: str, value: Any):
        """Handle property value changes"""
        if self.current_module:
            self.app.update_module_property(self.current_module, field_name, value)

    def _browse_file(self, field_name: str, entry_widget: ctk.CTkEntry):
        """Open file browser and update the entry widget"""
        filename = filedialog.askopenfilename(
            title=f"Select {field_name.replace('_', ' ').title()}",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.gif *.bmp *.webp"),
                ("Video files", "*.mp4 *.avi *.mov *.wmv"),
                ("All files", "*.*")
            ]
        )
        if filename:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, filename)
            self._on_property_change(field_name, filename)

    def _delete_module(self):
        """Delete the current module"""
        if self.current_module:
            self.app.remove_module(self.current_module.id)
