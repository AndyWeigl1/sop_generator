# gui/properties_panel.py
import customtkinter as ctk
from typing import Dict, Optional, Any, Tuple
from modules.base_module import Module
from modules.complex_module import TabModule
from tkinter import filedialog


class PropertiesPanel:
    """Panel for editing module properties"""

    def __init__(self, parent, app_instance):
        self.parent = parent
        self.app = app_instance
        self.current_module: Optional[Module] = None
        self.current_parent_tab: Optional[Tuple['TabModule', str]] = None
        self.property_widgets: Dict[str, ctk.CTkBaseClass] = {}

        # Create a frame for the content
        self.content_frame = ctk.CTkFrame(parent, fg_color=("gray90", "gray15"))
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
        self.current_parent_tab = None

    def show_module_properties(self, module: Module, parent_tab: Optional[Tuple['TabModule', str]] = None):
        """Display properties for the selected module"""
        self.clear()
        self.current_module = module
        self.current_parent_tab = parent_tab

        # Module name header
        header_frame = ctk.CTkFrame(self.content_frame, fg_color=("gray90", "gray15"))
        header_frame.pack(fill="x", padx=10, pady=(10, 20))

        # Show context if module is in a tab
        if parent_tab:
            tab_module, tab_name = parent_tab
            context_label = ctk.CTkLabel(
                header_frame,
                text=f"Tab: {tab_name}",
                font=("Arial", 11),
                text_color="gray"
            )
            context_label.pack(side="top", anchor="w")

        module_label = ctk.CTkLabel(
            header_frame,
            text=module.display_name,
            font=("Arial", 16, "bold")
        )
        module_label.pack(side="left")

        # Control buttons frame
        controls_frame = ctk.CTkFrame(header_frame, fg_color=("gray90", "gray15"))
        controls_frame.pack(side="right")

        # Move to main canvas button (if module is in a tab)
        if parent_tab:
            move_out_btn = ctk.CTkButton(
                controls_frame,
                text="Move to Main",
                width=80,
                fg_color="blue",
                hover_color="darkblue",
                command=lambda: self._move_module_from_tab()
            )
            move_out_btn.pack(side="left", padx=(0, 5))

        # Delete button
        delete_btn = ctk.CTkButton(
            controls_frame,
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

    def show_tab_properties(self, tab_module: 'TabModule', tab_name: str):
        """Display properties for a selected tab within a TabModule"""
        self.clear()
        self.current_module = None
        self.current_parent_tab = (tab_module, tab_name)

        # Tab header
        header_frame = ctk.CTkFrame(self.content_frame, fg_color=("gray90", "gray15"))
        header_frame.pack(fill="x", padx=10, pady=(10, 20))

        tab_label = ctk.CTkLabel(
            header_frame,
            text=f"Tab: {tab_name}",
            font=("Arial", 16, "bold")
        )
        tab_label.pack(side="left")

        # Tab controls
        controls_frame = ctk.CTkFrame(header_frame, fg_color=("gray90", "gray15"))
        controls_frame.pack(side="right")

        # Add module to tab button
        add_module_btn = ctk.CTkButton(
            controls_frame,
            text="Add Module",
            width=80,
            fg_color="green",
            hover_color="darkgreen",
            command=lambda: self._show_add_module_dialog(tab_module, tab_name)
        )
        add_module_btn.pack(side="left", padx=(0, 5))

        # Rename tab button
        rename_btn = ctk.CTkButton(
            controls_frame,
            text="Rename",
            width=60,
            command=lambda: self._rename_tab(tab_module, tab_name)
        )
        rename_btn.pack(side="left", padx=(0, 5))

        # Delete tab button (only if more than one tab)
        if len(tab_module.content_data['tabs']) > 1:
            delete_tab_btn = ctk.CTkButton(
                controls_frame,
                text="Delete Tab",
                width=70,
                fg_color="darkred",
                hover_color="red",
                command=lambda: self._delete_tab(tab_module, tab_name)
            )
            delete_tab_btn.pack(side="right")

        # Show modules in this tab
        self._show_tab_modules(tab_module, tab_name)

    def _show_tab_modules(self, tab_module: 'TabModule', tab_name: str):
        """Show list of modules in the selected tab"""
        modules_frame = ctk.CTkFrame(self.content_frame, fg_color=("gray90", "gray15"))
        modules_frame.pack(fill="x", padx=10, pady=(10, 0))

        modules_label = ctk.CTkLabel(
            modules_frame,
            text=f"Modules in '{tab_name}':",
            font=("Arial", 14, "bold")
        )
        modules_label.pack(pady=(10, 5))

        # List modules in this tab
        if tab_name in tab_module.sub_modules:
            modules = sorted(tab_module.sub_modules[tab_name], key=lambda m: m.position)
            if modules:
                for module in modules:
                    module_frame = ctk.CTkFrame(modules_frame, fg_color="gray20")
                    module_frame.pack(fill="x", padx=5, pady=2)

                    module_label = ctk.CTkLabel(
                        module_frame,
                        text=f"{module.position + 1}. {module.display_name}",
                        anchor="w"
                    )
                    module_label.pack(side="left", padx=10, pady=5)

                    select_btn = ctk.CTkButton(
                        module_frame,
                        text="Select",
                        width=60,
                        command=lambda m=module: self.app.select_module(m, (tab_module, tab_name))
                    )
                    select_btn.pack(side="right", padx=5, pady=2)
            else:
                empty_label = ctk.CTkLabel(
                    modules_frame,
                    text="No modules in this tab",
                    text_color="gray"
                )
                empty_label.pack(pady=10)

    def _show_add_module_dialog(self, tab_module: 'TabModule', tab_name: str):
        """Show dialog to add a module to the selected tab"""
        # This would open a dialog to select module type
        # For now, we'll just trigger the app's context setting
        self.app.selected_tab_context = (tab_module, tab_name)
        # You could implement a proper dialog here

    def _rename_tab(self, tab_module: 'TabModule', tab_name: str):
        """Rename the selected tab"""
        dialog = ctk.CTkInputDialog(text=f"Rename tab '{tab_name}':", title="Rename Tab")
        new_name = dialog.get_input()

        if new_name and new_name != tab_name and new_name not in tab_module.content_data['tabs']:
            tab_module.rename_tab(tab_name, new_name)
            self.app.canvas_panel._refresh_tab_module(tab_module)
            self.app.set_modified(True)
            # Refresh the properties panel with the new tab name
            self.show_tab_properties(tab_module, new_name)

    def _delete_tab(self, tab_module: 'TabModule', tab_name: str):
        """Delete the selected tab"""
        if len(tab_module.content_data['tabs']) > 1:
            result = ctk.CTkInputDialog(
                text=f"Type 'DELETE' to confirm deletion of tab '{tab_name}':",
                title="Confirm Tab Deletion"
            ).get_input()

            if result == "DELETE":
                tab_module.remove_tab(tab_name)
                self.app.canvas_panel._refresh_tab_module(tab_module)
                self.app.set_modified(True)
                # Clear properties panel
                self.clear()

    def _move_module_from_tab(self):
        """Move current module from tab to main canvas"""
        if self.current_module and self.current_parent_tab:
            tab_module, tab_name = self.current_parent_tab
            if self.app.move_module_from_tab(self.current_module, tab_module, tab_name):
                # Module moved successfully, clear properties
                self.clear()

    def _create_property_field(self, field_name: str, field_type: str, module: Module):
        """Create a property field based on its type"""
        # Frame for the field
        field_frame = ctk.CTkFrame(self.content_frame, fg_color=("gray90", "gray15"))
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
            file_frame = ctk.CTkFrame(field_frame, fg_color=("gray90", "gray15"))
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

        elif field_type == "tab_list_editor":
            # Special editor for tab management
            self._create_tab_list_editor(field_frame, field_name, module)
            return  # Don't pack the widget since we created custom UI

        else:
            # Default to text entry
            widget = ctk.CTkEntry(field_frame, width=200)
            widget.insert(0, str(current_value))
            widget.bind("<KeyRelease>", lambda e: self._on_property_change(field_name, widget.get()))

        widget.pack(side="left", fill="x", expand=True)
        self.property_widgets[field_name] = widget

    def _create_tab_list_editor(self, parent_frame: ctk.CTkFrame, field_name: str, module: Module):
        """Create special editor for managing tabs in TabModule"""
        if not isinstance(module, TabModule):
            return

        # Container for tab management
        tab_editor_frame = ctk.CTkFrame(parent_frame, fg_color="gray20")
        tab_editor_frame.pack(side="left", fill="x", expand=True)

        # Current tabs list
        for i, tab_name in enumerate(module.content_data['tabs']):
            tab_row = ctk.CTkFrame(tab_editor_frame, fg_color="gray25")
            tab_row.pack(fill="x", padx=2, pady=1)

            tab_label = ctk.CTkLabel(tab_row, text=f"{i + 1}. {tab_name}", anchor="w")
            tab_label.pack(side="left", padx=5)

            # Select tab button
            select_btn = ctk.CTkButton(
                tab_row,
                text="Select",
                width=50,
                command=lambda tn=tab_name: self.app.select_tab(module, tn)
            )
            select_btn.pack(side="right", padx=2)

        # Add new tab button
        add_tab_btn = ctk.CTkButton(
            tab_editor_frame,
            text="+ Add Tab",
            width=80,
            command=lambda: self._add_new_tab(module)
        )
        add_tab_btn.pack(pady=5)

    def _add_new_tab(self, tab_module: 'TabModule'):
        """Add a new tab to the TabModule"""
        dialog = ctk.CTkInputDialog(text="Enter new tab name:", title="Add Tab")
        tab_name = dialog.get_input()

        if tab_name and tab_name not in tab_module.content_data['tabs']:
            tab_module.add_tab(tab_name)
            self.app.canvas_panel._refresh_tab_module(tab_module)
            self.app.set_modified(True)
            # Refresh properties to show the new tab
            self.show_module_properties(tab_module)

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
