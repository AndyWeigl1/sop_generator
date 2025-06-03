# gui/properties_panel.py - Updated with preview updates for tab operations
import customtkinter as ctk
from typing import Dict, Optional, Any, Tuple, List
from modules.base_module import Module
from modules.complex_module import TabModule
from tkinter import filedialog, messagebox
from gui.components.text_formatting_toolbar import TextFormattingToolbar
import os
import json


class PropertiesPanel:
    """Redesigned panel for editing module properties with better usability and event-driven preview updates"""

    def __init__(self, parent, app_instance):
        self.parent = parent
        self.app = app_instance
        self.current_module: Optional[Module] = None
        self.current_parent_tab: Optional[Tuple['TabModule', str]] = None
        self.property_widgets: Dict[str, ctk.CTkBaseClass] = {}

        # Create main container that will hold both scroll frame and preview
        self.main_container = ctk.CTkFrame(parent, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True)

        # Create main scrollable frame for properties
        self.scroll_frame = ctk.CTkScrollableFrame(
            self.main_container,
            fg_color=("gray95", "gray10"),
            corner_radius=0
        )
        self.scroll_frame.pack(fill="both", expand=True)

        # Show empty state initially
        self._show_empty_state()

    def _show_empty_state(self):
        """Show empty state when no module is selected"""
        self.clear()

        # Create centered content
        empty_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        empty_frame.pack(expand=True, fill="both", pady=50)

        icon_label = ctk.CTkLabel(
            empty_frame,
            text="⚙️",
            font=("Arial", 48),
            text_color="gray"
        )
        icon_label.pack(pady=(20, 10))

        empty_label = ctk.CTkLabel(
            empty_frame,
            text="Select a module to edit\nits properties",
            font=("Arial", 14),
            text_color="gray",
            justify="center"
        )
        empty_label.pack()

    def clear(self):
        """Clear all property widgets"""
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.property_widgets.clear()
        self.current_module = None
        self.current_parent_tab = None
        # Hide module preview

    def show_module_properties(self, module: Module, parent_tab: Optional[Tuple['TabModule', str]] = None):
        """Display properties for the selected module with improved layout"""
        self.clear()
        self.current_module = module
        self.current_parent_tab = parent_tab

        # Main container
        main_container = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=15, pady=15)

        # Header Section
        self._create_header_section(main_container, module, parent_tab)

        # Properties Section
        self._create_properties_section(main_container, module)

    def _create_header_section(self, parent, module: Module, parent_tab: Optional[Tuple['TabModule', str]] = None):
        """Create the header section with module info and controls"""
        header_frame = ctk.CTkFrame(parent, fg_color=("gray90", "gray20"), corner_radius=8)
        header_frame.pack(fill="x", pady=(0, 20))

        # Header content
        header_content = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_content.pack(fill="x", padx=20, pady=15)

        # Module icon and name
        title_frame = ctk.CTkFrame(header_content, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, 10))

        # Module type icon
        icon_map = {
            'header': '📄', 'text': '📝', 'media': '🖼️', 'step_card': '📋',
            'table': '📊', 'disclaimer': '⚠️', 'section_title': '🎯',
            'issue_card': '🔧', 'footer': '📍', 'tabs': '📑', 'media_grid': '🎬'
        }
        icon = icon_map.get(module.module_type, '📦')

        icon_label = ctk.CTkLabel(
            title_frame,
            text=icon,
            font=("Arial", 24)
        )
        icon_label.pack(side="left", padx=(0, 15))

        # Module info
        info_frame = ctk.CTkFrame(title_frame, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True)

        name_label = ctk.CTkLabel(
            info_frame,
            text=module.display_name,
            font=("Arial", 18, "bold"),
            anchor="w"
        )
        name_label.pack(anchor="w")

        # Context info
        if parent_tab:
            tab_module, tab_name = parent_tab
            context_label = ctk.CTkLabel(
                info_frame,
                text=f"📑 In tab: {tab_name}",
                font=("Arial", 12),
                text_color="gray",
                anchor="w"
            )
            context_label.pack(anchor="w", pady=(2, 0))

        # Action buttons
        self._create_action_buttons(header_content, module, parent_tab)

    def _create_action_buttons(self, parent, module: Module, parent_tab: Optional[Tuple['TabModule', str]] = None):
        """Create action buttons for the module"""
        buttons_frame = ctk.CTkFrame(parent, fg_color="transparent")
        buttons_frame.pack(fill="x")

        # Move to main canvas button (if module is in a tab)
        if parent_tab:
            move_btn = ctk.CTkButton(
                buttons_frame,
                text="📤 Move to Main",
                width=120,
                height=32,
                font=("Arial", 12),
                fg_color=("blue", "blue"),
                hover_color=("darkblue", "darkblue"),
                command=self._move_module_from_tab
            )
            move_btn.pack(side="left", padx=(0, 10))

        # Duplicate button
        duplicate_btn = ctk.CTkButton(
            buttons_frame,
            text="📋 Duplicate",
            width=100,
            height=32,
            font=("Arial", 12),
            fg_color=("green", "green"),
            hover_color=("darkgreen", "darkgreen"),
            command=self._duplicate_module
        )
        duplicate_btn.pack(side="left", padx=(0, 10))

        # Delete button
        delete_btn = ctk.CTkButton(
            buttons_frame,
            text="🗑️ Delete",
            width=90,
            height=32,
            font=("Arial", 12),
            fg_color=("red", "red"),
            hover_color=("darkred", "darkred"),
            command=self._delete_module
        )
        delete_btn.pack(side="right")

    def _create_properties_section(self, parent, module: Module):
        """Create the properties editing section"""
        # Properties header
        props_header = ctk.CTkLabel(
            parent,
            text="Properties",
            font=("Arial", 16, "bold"),
            anchor="w"
        )
        props_header.pack(fill="x", pady=(0, 15))

        # Properties container
        props_container = ctk.CTkFrame(parent, fg_color=("gray90", "gray20"), corner_radius=8)
        props_container.pack(fill="both", expand=True)

        # Properties content
        props_content = ctk.CTkFrame(props_container, fg_color="transparent")
        props_content.pack(fill="both", expand=True, padx=20, pady=20)

        # Create property fields
        fields = module.get_property_fields()
        if not fields:
            no_props_label = ctk.CTkLabel(
                props_content,
                text="This module has no editable properties.",
                font=("Arial", 12),
                text_color="gray"
            )
            no_props_label.pack(pady=20)
            return

        for field_name, field_type in fields.items():
            self._create_property_field(props_content, field_name, field_type, module)

    def _create_property_field(self, parent, field_name: str, field_type: str, module: Module):
        """Create a property field with improved layout and sizing"""
        # Main field container
        field_container = ctk.CTkFrame(parent, fg_color="transparent")
        field_container.pack(fill="x", pady=(0, 15))

        # Field label
        label_text = field_name.replace('_', ' ').title()
        if field_name in ['source', 'logo_path', 'background_image', 'media_source']:
            label_text += " 📁"

        field_label = ctk.CTkLabel(
            field_container,
            text=label_text,
            font=("Arial", 13, "bold"),
            anchor="w"
        )
        field_label.pack(fill="x", pady=(0, 8))

        # Get current value
        current_value = module.content_data.get(field_name, "")

        # Create input container
        input_container = ctk.CTkFrame(field_container, fg_color="transparent")
        input_container.pack(fill="x")

        # Create appropriate widget based on field type
        widget = self._create_input_widget(input_container, field_name, field_type, current_value, module)

        # Store widget reference
        if widget:
            self.property_widgets[field_name] = widget

    def _create_input_widget(self, parent, field_name: str, field_type: str, current_value: Any, module: Module):
        """Create the appropriate input widget for the field type"""

        if field_type == "text":
            widget = ctk.CTkEntry(
                parent,
                height=36,
                font=("Arial", 12),
                placeholder_text=f"Enter {field_name.replace('_', ' ')}"
            )
            widget.pack(fill="x")
            if current_value:
                widget.insert(0, str(current_value))
            widget.bind("<KeyRelease>", lambda e: self._on_property_change(field_name, widget.get()))
            return widget

        elif field_type == "textarea" or field_type.startswith("textarea:"):
            # Check if it's a formatted textarea
            is_formatted = field_type.startswith("textarea:") and ":formatted" in field_type

            if is_formatted:
                # Create container for toolbar and textarea
                textarea_container = ctk.CTkFrame(parent, fg_color="transparent")
                textarea_container.pack(fill="x")

                widget = ctk.CTkTextbox(
                textarea_container,
                height=100,
                font=("Arial", 12),
                wrap="word"
                )
                # Create the toolbar (it will pack itself above the textbox)
                toolbar = TextFormattingToolbar(
                    textarea_container,
                    widget,
                    field_name,
                    self._on_property_change
                )
                # Pack the textbox below the toolbar
                widget.pack(fill="x")
            else:
                # Regular textarea without formatting
                widget = ctk.CTkTextbox(
                    parent,
                    height=100,
                    font=("Arial", 12),
                    wrap="word"
                )
                widget.pack(fill="x")

            if current_value:
                widget.insert("1.0", str(current_value))
            widget.bind("<KeyRelease>", lambda e: self._on_property_change(field_name, widget.get("1.0", "end-1c")))
            return widget

        elif field_type.startswith("dropdown:"):
            options = field_type.split(":")[1].split(",")
            widget = ctk.CTkComboBox(
                parent,
                values=options,
                height=36,
                font=("Arial", 12),
                dropdown_font=("Arial", 11),
                command=lambda value: self._on_property_change(field_name, value)
            )
            widget.pack(fill="x")
            if str(current_value) in options:
                widget.set(str(current_value))
            elif options:
                widget.set(options[0])
            return widget

        elif field_type == "checkbox":
            widget = ctk.CTkCheckBox(
                parent,
                text="",
                font=("Arial", 12),
                command=lambda: self._on_property_change(field_name, widget.get())
            )
            widget.pack(anchor="w")
            if current_value:
                widget.select()
            return widget

        elif field_type in ["file", "file_or_url"]:
            return self._create_file_input(parent, field_name, current_value)

        elif field_type == "number":
            widget = ctk.CTkEntry(
                parent,
                height=36,
                font=("Arial", 12),
                placeholder_text="Enter number"
            )
            widget.pack(fill="x")
            if current_value:
                widget.insert(0, str(current_value))
            widget.bind("<KeyRelease>", lambda e: self._on_property_change(field_name, widget.get()))
            return widget

        elif field_type == "list_editor":
            return self._create_list_editor(parent, field_name, current_value)

        elif field_type == "media_list_editor":
            return self._create_media_list_editor(parent, field_name, current_value, module)

        elif field_type == "tab_list_editor":
            return self._create_tab_list_editor(parent, field_name, module)

        elif field_type == "table_editor":
            return self._create_table_editor(parent, field_name, current_value)

        else:
            # Default to text entry
            widget = ctk.CTkEntry(parent, height=36, font=("Arial", 12))
            widget.pack(fill="x")
            if current_value:
                widget.insert(0, str(current_value))
            widget.bind("<KeyRelease>", lambda e: self._on_property_change(field_name, widget.get()))
            return widget

    def _create_file_input(self, parent, field_name: str, current_value: Any):
        """Create file input with browse button"""
        file_frame = ctk.CTkFrame(parent, fg_color="transparent")
        file_frame.pack(fill="x")

        # Entry widget
        entry = ctk.CTkEntry(
            file_frame,
            height=36,
            font=("Arial", 12),
            placeholder_text="Select file or enter URL"
        )
        entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        if current_value:
            entry.insert(0, str(current_value))

        entry.bind("<KeyRelease>", lambda e: self._on_property_change(field_name, entry.get()))

        # Browse button
        browse_btn = ctk.CTkButton(
            file_frame,
            text="📁 Browse",
            width=100,
            height=36,
            font=("Arial", 12),
            command=lambda: self._browse_file(field_name, entry)
        )
        browse_btn.pack(side="right")

        return entry

    def _create_list_editor(self, parent, field_name: str, current_value: Any):
        """Create editor for simple lists"""
        if isinstance(current_value, list):
            value_str = ", ".join(str(v) for v in current_value)
        else:
            value_str = str(current_value) if current_value else ""

        widget = ctk.CTkEntry(
            parent,
            height=36,
            font=("Arial", 12),
            placeholder_text="Enter items separated by commas"
        )
        widget.pack(fill="x")

        if value_str:
            widget.insert(0, value_str)

        widget.bind("<KeyRelease>", lambda e: self._on_property_change(field_name, widget.get()))
        return widget

    def _create_media_list_editor(self, parent, field_name: str, current_value: Any, module: Module):
        """Create advanced editor for media grid items"""
        editor_frame = ctk.CTkFrame(parent, fg_color=("gray85", "gray25"))
        editor_frame.pack(fill="x")

        # Header
        header_label = ctk.CTkLabel(
            editor_frame,
            text="Media Items",
            font=("Arial", 13, "bold")
        )
        header_label.pack(pady=(15, 10))

        # Items container
        items_container = ctk.CTkScrollableFrame(editor_frame, height=200)
        items_container.pack(fill="x", padx=15, pady=(0, 15))

        # Store for tracking items
        self._media_items = current_value if isinstance(current_value, list) else []

        # Display current items
        self._refresh_media_items(items_container, field_name)

        # Add item button
        add_btn = ctk.CTkButton(
            editor_frame,
            text="➕ Add Media Item",
            height=32,
            font=("Arial", 12),
            command=lambda: self._add_media_item(items_container, field_name)
        )
        add_btn.pack(pady=(0, 15))

        return editor_frame

    def _refresh_media_items(self, container, field_name: str):
        """Refresh the media items display"""
        # Clear existing widgets
        for widget in container.winfo_children():
            widget.destroy()

        for i, item in enumerate(self._media_items):
            self._create_media_item_widget(container, i, item, field_name)

    def _create_media_item_widget(self, parent, index: int, item: dict, field_name: str):
        """Create widget for a single media item"""
        item_frame = ctk.CTkFrame(parent, fg_color=("gray80", "gray30"))
        item_frame.pack(fill="x", pady=5)

        # Header with remove button
        header_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=(10, 5))

        item_label = ctk.CTkLabel(
            header_frame,
            text=f"🖼️ Media Item {index + 1}",
            font=("Arial", 12, "bold")
        )
        item_label.pack(side="left")

        remove_btn = ctk.CTkButton(
            header_frame,
            text="❌",
            width=30,
            height=25,
            fg_color="red",
            command=lambda: self._remove_media_item(index, parent, field_name)
        )
        remove_btn.pack(side="right")

        # Fields
        fields_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
        fields_frame.pack(fill="x", padx=10, pady=(0, 10))

        # Header field
        ctk.CTkLabel(fields_frame, text="Header:", font=("Arial", 11)).pack(anchor="w", pady=(5, 2))
        header_entry = ctk.CTkEntry(fields_frame, height=32, font=("Arial", 11))
        header_entry.pack(fill="x", pady=(0, 5))
        header_entry.insert(0, item.get('header', f'Media {index + 1}'))

        # Source field
        ctk.CTkLabel(fields_frame, text="Source:", font=("Arial", 11)).pack(anchor="w", pady=(5, 2))
        source_frame = ctk.CTkFrame(fields_frame, fg_color="transparent")
        source_frame.pack(fill="x", pady=(0, 5))

        source_entry = ctk.CTkEntry(source_frame, height=32, font=("Arial", 11))
        source_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        source_entry.insert(0, item.get('source', ''))

        browse_btn = ctk.CTkButton(
            source_frame,
            text="📁",
            width=35,
            height=32,
            command=lambda: self._browse_media_file(source_entry, index, field_name)
        )
        browse_btn.pack(side="right")

        # Caption field
        ctk.CTkLabel(fields_frame, text="Caption:", font=("Arial", 11)).pack(anchor="w", pady=(5, 2))
        caption_entry = ctk.CTkEntry(fields_frame, height=32, font=("Arial", 11))
        caption_entry.pack(fill="x", pady=(0, 5))
        caption_entry.insert(0, item.get('caption', ''))

        # Bind change events
        header_entry.bind("<KeyRelease>",
                          lambda e: self._update_media_item(index, 'header', header_entry.get(), field_name))
        source_entry.bind("<KeyRelease>",
                          lambda e: self._update_media_item(index, 'source', source_entry.get(), field_name))
        caption_entry.bind("<KeyRelease>",
                           lambda e: self._update_media_item(index, 'caption', caption_entry.get(), field_name))

    def _add_media_item(self, container, field_name: str):
        """Add new media item"""
        new_item = {
            'type': 'image',
            'source': '',
            'caption': f'Image {len(self._media_items) + 1}',
            'alt_text': '',
            'header': f'Media {len(self._media_items) + 1}'
        }
        self._media_items.append(new_item)
        self._refresh_media_items(container, field_name)
        self._on_property_change(field_name, self._media_items)

    def _remove_media_item(self, index: int, container, field_name: str):
        """Remove media item"""
        if 0 <= index < len(self._media_items):
            self._media_items.pop(index)
            self._refresh_media_items(container, field_name)
            self._on_property_change(field_name, self._media_items)

    def _update_media_item(self, index: int, key: str, value: str, field_name: str):
        """Update a specific field of a media item"""
        if 0 <= index < len(self._media_items):
            self._media_items[index][key] = value
            self._on_property_change(field_name, self._media_items)

    def _browse_media_file(self, entry_widget, index: int, field_name: str):
        """Browse for media file"""
        filename = filedialog.askopenfilename(
            title="Select Media File",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.gif *.bmp *.webp"),
                ("Video files", "*.mp4 *.avi *.mov *.wmv"),
                ("All files", "*.*")
            ]
        )
        if filename:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, filename)
            self._update_media_item(index, 'source', filename, field_name)

    def _create_tab_list_editor(self, parent, field_name: str, module: Module):
        """Create editor for tab management"""
        if not isinstance(module, TabModule):
            return ctk.CTkLabel(parent, text="Error: Not a tab module")

        editor_frame = ctk.CTkFrame(parent, fg_color=("gray85", "gray25"))
        editor_frame.pack(fill="x")

        # Header
        header_label = ctk.CTkLabel(
            editor_frame,
            text="Tab Management",
            font=("Arial", 13, "bold")
        )
        header_label.pack(pady=(15, 10))

        # Tabs list
        tabs_container = ctk.CTkFrame(editor_frame, fg_color="transparent")
        tabs_container.pack(fill="x", padx=15, pady=(0, 15))

        for i, tab_name in enumerate(module.content_data['tabs']):
            tab_frame = ctk.CTkFrame(tabs_container, fg_color=("gray80", "gray30"))
            tab_frame.pack(fill="x", pady=2)

            # Tab info
            info_frame = ctk.CTkFrame(tab_frame, fg_color="transparent")
            info_frame.pack(fill="x", padx=10, pady=8)

            tab_label = ctk.CTkLabel(
                info_frame,
                text=f"📑 {tab_name}",
                font=("Arial", 12),
                anchor="w"
            )
            tab_label.pack(side="left", fill="x", expand=True)

            # Module count
            module_count = len(module.sub_modules.get(tab_name, []))
            count_label = ctk.CTkLabel(
                info_frame,
                text=f"({module_count} modules)",
                font=("Arial", 11),
                text_color="gray"
            )
            count_label.pack(side="left", padx=(10, 10))

            # Select button
            select_btn = ctk.CTkButton(
                info_frame,
                text="Select",
                width=70,
                height=25,
                font=("Arial", 11),
                command=lambda tn=tab_name: self.app.select_tab(module, tn)
            )
            select_btn.pack(side="right", padx=(0, 5))

        # Add tab button
        add_tab_btn = ctk.CTkButton(
            editor_frame,
            text="➕ Add New Tab",
            height=32,
            font=("Arial", 12),
            command=lambda: self._add_new_tab(module)
        )
        add_tab_btn.pack(pady=(0, 15))

        return editor_frame

    def _create_table_editor(self, parent, field_name: str, current_value: Any):
        """Create basic table editor"""
        # For now, use JSON editor - can be improved later
        editor_frame = ctk.CTkFrame(parent, fg_color=("gray85", "gray25"))
        editor_frame.pack(fill="x")

        label = ctk.CTkLabel(
            editor_frame,
            text="Table Data (JSON format):",
            font=("Arial", 12, "bold")
        )
        label.pack(pady=(15, 5), padx=15, anchor="w")

        text_widget = ctk.CTkTextbox(
            editor_frame,
            height=150,
            font=("Courier", 11)
        )
        text_widget.pack(fill="x", padx=15, pady=(0, 15))

        # Format current value as JSON
        try:
            if current_value:
                formatted_json = json.dumps(current_value, indent=2)
                text_widget.insert("1.0", formatted_json)
        except:
            text_widget.insert("1.0", str(current_value))

        text_widget.bind("<KeyRelease>", lambda e: self._on_table_change(field_name, text_widget))

        return text_widget

    def _on_table_change(self, field_name: str, text_widget):
        """Handle table data changes"""
        try:
            content = text_widget.get("1.0", "end-1c")
            if content.strip():
                data = json.loads(content)
                self._on_property_change(field_name, data)
        except json.JSONDecodeError:
            # Invalid JSON, don't update
            pass

    def _add_new_tab(self, tab_module: TabModule):
        """Add a new tab to the TabModule"""
        dialog = ctk.CTkInputDialog(text="Enter new tab name:", title="Add Tab")
        tab_name = dialog.get_input()

        if tab_name and tab_name not in tab_module.content_data['tabs']:
            tab_module.add_tab(tab_name)
            self.app.canvas_panel._refresh_tab_module(tab_module)
            self.app.set_modified(True)
            # Trigger preview update for new tab
            self.app.preview_manager.request_preview_update()
            # Refresh properties to show the new tab
            self.show_module_properties(tab_module)

    def _move_module_from_tab(self):
        """Move current module from tab to main canvas"""
        if self.current_module and self.current_parent_tab:
            tab_module, tab_name = self.current_parent_tab
            if self.app.move_module_from_tab(self.current_module, tab_module, tab_name):
                self.clear()

    def _duplicate_module(self):
        """Duplicate the current module"""
        if self.current_module:
            try:
                # Create new module of same type
                from modules.module_factory import ModuleFactory
                new_module = ModuleFactory.create_module(self.current_module.module_type)

                # Copy content data
                new_module.content_data = self.current_module.content_data.copy()

                # Add suffix to distinguishable fields
                if 'title' in new_module.content_data:
                    new_module.content_data['title'] += " (Copy)"
                elif 'header' in new_module.content_data:
                    new_module.content_data['header'] += " (Copy)"

                # Add to appropriate location
                if self.current_parent_tab:
                    tab_module, tab_name = self.current_parent_tab
                    if tab_module.add_module_to_tab(tab_name, new_module):
                        self.app.canvas_panel.add_module_to_tab_widget(tab_module, tab_name, new_module)
                else:
                    new_module.position = len(self.app.active_modules)
                    self.app.active_modules.append(new_module)
                    self.app.canvas_panel.add_module_widget(new_module)

                self.app.set_modified(True)
                # Trigger preview update for duplicated module
                self.app.preview_manager.request_preview_update()
                messagebox.showinfo("Success", "Module duplicated successfully!")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to duplicate module: {str(e)}")

    def _delete_module(self):
        """Delete the current module with confirmation"""
        if self.current_module:
            result = messagebox.askyesno(
                "Confirm Delete",
                f"Are you sure you want to delete this {self.current_module.display_name}?"
            )
            if result:
                self.app.remove_module(self.current_module.id)

    def _on_property_change(self, field_name: str, value: Any):
        """Handle property value changes (enhanced with live preview)"""
        if self.current_module:
            self.app.update_module_property(self.current_module, field_name, value)

            # Update module preview immediately for real-time feedback
            if hasattr(self, 'module_preview'):
                # Small delay to prevent excessive updates during typing
                self.scroll_frame.after(300, self.module_preview.update_preview)

    def _browse_file(self, field_name: str, entry_widget: ctk.CTkEntry):
        """Open file browser and update the entry widget"""

        # Define file type categories
        MEDIA_FILETYPES = [
            ("Image files", "*.jpg *.jpeg *.png *.gif *.bmp *.webp"),
            ("Video files", "*.mp4 *.avi *.mov *.wmv"),
            ("All files", "*.*")
        ]

        IMAGE_FILETYPES = [
            ("Image files", "*.jpg *.jpeg *.png *.gif *.bmp *.webp"),
            ("All files", "*.*")
        ]

        ALL_FILETYPES = [("All files", "*.*")]

        # Categorize fields by expected file types
        media_fields = {
            'source',  # Media module
            'issue_media_source',  # Issue card - issue media
            'solution_single_media_source'  # Issue card - solution media
        }

        image_only_fields = {
            'logo_path',
            'background_image'
        }

        # Determine appropriate file types
        if field_name in media_fields:
            filetypes = MEDIA_FILETYPES
        elif field_name in image_only_fields:
            filetypes = IMAGE_FILETYPES
        else:
            filetypes = ALL_FILETYPES

        filename = filedialog.askopenfilename(
            title=f"Select {field_name.replace('_', ' ').title()}",
            filetypes=filetypes
        )

        if filename:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, filename)
            self._on_property_change(field_name, filename)

    def show_tab_properties(self, tab_module: 'TabModule', tab_name: str):
        """Display properties for a selected tab within a TabModule"""
        self.clear()
        self.current_module = None
        self.current_parent_tab = (tab_module, tab_name)

        # Main container
        main_container = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=15, pady=15)

        # Header Section for Tab
        header_frame = ctk.CTkFrame(main_container, fg_color=("gray90", "gray20"), corner_radius=8)
        header_frame.pack(fill="x", pady=(0, 20))

        header_content = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_content.pack(fill="x", padx=20, pady=15)

        # Tab info
        title_frame = ctk.CTkFrame(header_content, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, 10))

        icon_label = ctk.CTkLabel(title_frame, text="📑", font=("Arial", 24))
        icon_label.pack(side="left", padx=(0, 15))

        info_frame = ctk.CTkFrame(title_frame, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True)

        name_label = ctk.CTkLabel(
            info_frame,
            text=f"Tab: {tab_name}",
            font=("Arial", 18, "bold"),
            anchor="w"
        )
        name_label.pack(anchor="w")

        # Module count
        module_count = len(tab_module.sub_modules.get(tab_name, []))
        count_label = ctk.CTkLabel(
            info_frame,
            text=f"{module_count} modules in this tab",
            font=("Arial", 12),
            text_color="gray",
            anchor="w"
        )
        count_label.pack(anchor="w", pady=(2, 0))

        # Tab action buttons
        self._create_tab_action_buttons(header_content, tab_module, tab_name)

        # Show modules in this tab
        self._show_tab_modules_improved(main_container, tab_module, tab_name)

    def _create_tab_action_buttons(self, parent, tab_module: 'TabModule', tab_name: str):
        """Create action buttons for tab management"""
        buttons_frame = ctk.CTkFrame(parent, fg_color="transparent")
        buttons_frame.pack(fill="x")

        # Rename tab button
        rename_btn = ctk.CTkButton(
            buttons_frame,
            text="✏️ Rename Tab",
            width=120,
            height=32,
            font=("Arial", 12),
            command=lambda: self._rename_tab(tab_module, tab_name)
        )
        rename_btn.pack(side="left", padx=(0, 10))

        # Delete tab button (only if more than one tab)
        if len(tab_module.content_data['tabs']) > 1:
            delete_tab_btn = ctk.CTkButton(
                buttons_frame,
                text="🗑️ Delete Tab",
                width=110,
                height=32,
                font=("Arial", 12),
                fg_color="red",
                hover_color="darkred",
                command=lambda: self._delete_tab(tab_module, tab_name)
            )
            delete_tab_btn.pack(side="right")

    def _show_tab_modules_improved(self, parent, tab_module: 'TabModule', tab_name: str):
        """Show improved list of modules in the selected tab"""
        modules_section = ctk.CTkFrame(parent, fg_color=("gray90", "gray20"), corner_radius=8)
        modules_section.pack(fill="both", expand=True)

        # Section header
        section_header = ctk.CTkFrame(modules_section, fg_color="transparent")
        section_header.pack(fill="x", padx=20, pady=(20, 10))

        modules_label = ctk.CTkLabel(
            section_header,
            text="Modules in this Tab",
            font=("Arial", 16, "bold")
        )
        modules_label.pack(side="left")

        # Add module button
        add_module_btn = ctk.CTkButton(
            section_header,
            text="➕ Add Module",
            width=120,
            height=32,
            font=("Arial", 12),
            fg_color="green",
            hover_color="darkgreen",
            command=lambda: self._set_add_module_context(tab_module, tab_name)
        )
        add_module_btn.pack(side="right")

        # Modules list
        modules_container = ctk.CTkScrollableFrame(
            modules_section,
            height=300,
            fg_color=("gray85", "gray15")
        )
        modules_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # List modules in this tab
        if tab_name in tab_module.sub_modules:
            modules = sorted(tab_module.sub_modules[tab_name], key=lambda m: m.position)
            if modules:
                for i, module in enumerate(modules):
                    self._create_module_list_item(modules_container, module, i + 1, tab_module, tab_name)
            else:
                self._create_empty_tab_message(modules_container)
        else:
            self._create_empty_tab_message(modules_container)

    def _create_module_list_item(self, parent, module: Module, position: int, tab_module: 'TabModule', tab_name: str):
        """Create a list item for a module in the tab"""
        item_frame = ctk.CTkFrame(parent, fg_color=("gray80", "gray25"))
        item_frame.pack(fill="x", pady=3)

        content_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
        content_frame.pack(fill="x", padx=15, pady=10)

        # Module icon and info
        info_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True)

        # Icon and name
        icon_map = {
            'header': '📄', 'text': '📝', 'media': '🖼️', 'step_card': '📋',
            'table': '📊', 'disclaimer': '⚠️', 'section_title': '🎯',
            'issue_card': '🔧', 'footer': '📍', 'tabs': '📑', 'media_grid': '🎬'
        }
        icon = icon_map.get(module.module_type, '📦')

        title_label = ctk.CTkLabel(
            info_frame,
            text=f"{position}. {icon} {module.display_name}",
            font=("Arial", 13, "bold"),
            anchor="w"
        )
        title_label.pack(anchor="w")

        # Preview text
        preview_text = self._get_module_preview_text(module)
        if preview_text:
            preview_label = ctk.CTkLabel(
                info_frame,
                text=preview_text,
                font=("Arial", 11),
                text_color="gray",
                anchor="w",
                wraplength=300
            )
            preview_label.pack(anchor="w", pady=(2, 0))

        # Action buttons
        buttons_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        buttons_frame.pack(side="right")

        select_btn = ctk.CTkButton(
            buttons_frame,
            text="Select",
            width=70,
            height=28,
            font=("Arial", 11),
            command=lambda: self.app.select_module(module, (tab_module, tab_name))
        )
        select_btn.pack(side="right")

    def _create_empty_tab_message(self, parent):
        """Create message for empty tabs"""
        empty_frame = ctk.CTkFrame(parent, fg_color="transparent")
        empty_frame.pack(expand=True, fill="both", pady=50)

        empty_icon = ctk.CTkLabel(
            empty_frame,
            text="📝",
            font=("Arial", 48),
            text_color="gray"
        )
        empty_icon.pack(pady=(20, 10))

        empty_label = ctk.CTkLabel(
            empty_frame,
            text="This tab is empty\n\nDrag modules here or click 'Add Module' to get started",
            font=("Arial", 14),
            text_color="gray",
            justify="center"
        )
        empty_label.pack()

    def _get_module_preview_text(self, module: Module) -> str:
        """Get preview text for a module"""
        if module.module_type == 'text':
            content = module.content_data.get('content', '')
            return content[:100] + "..." if len(content) > 100 else content
        elif module.module_type == 'media':
            source = module.content_data.get('source', 'No source')
            return f"Source: {os.path.basename(source) if source else 'No source'}"
        elif module.module_type == 'table':
            title = module.content_data.get('title', 'Untitled')
            return f"Title: {title}"
        elif module.module_type == 'section_title':
            title = module.content_data.get('title', 'Untitled')
            return f"Title: {title}"
        return ""

    def _set_add_module_context(self, tab_module: 'TabModule', tab_name: str):
        """Set context for adding modules to this tab"""
        self.app.selected_tab_context = (tab_module, tab_name)
        messagebox.showinfo(
            "Add Module Mode",
            f"Now drag modules from the left panel into the '{tab_name}' tab, "
            "or they will be automatically added to this tab when you select them."
        )

    def _rename_tab(self, tab_module: 'TabModule', tab_name: str):
        """Rename the selected tab"""
        dialog = ctk.CTkInputDialog(text=f"Rename tab '{tab_name}':", title="Rename Tab")
        dialog.get_input_widget().insert(0, tab_name)  # Pre-fill current name
        new_name = dialog.get_input()

        if new_name and new_name != tab_name and new_name not in tab_module.content_data['tabs']:
            tab_module.rename_tab(tab_name, new_name)
            self.app.canvas_panel._refresh_tab_module(tab_module)
            self.app.set_modified(True)
            # Trigger preview update for renamed tab
            self.app.preview_manager.request_preview_update()
            # Refresh the properties panel with the new tab name
            self.show_tab_properties(tab_module, new_name)
        elif new_name == tab_name:
            # No change needed
            pass
        elif new_name in tab_module.content_data['tabs']:
            messagebox.showerror("Error", f"A tab named '{new_name}' already exists.")

    def _delete_tab(self, tab_module: 'TabModule', tab_name: str):
        """Delete the selected tab with confirmation"""
        if len(tab_module.content_data['tabs']) <= 1:
            messagebox.showerror("Error", "Cannot delete the last tab.")
            return

        module_count = len(tab_module.sub_modules.get(tab_name, []))

        if module_count > 0:
            result = messagebox.askyesno(
                "Confirm Delete",
                f"Tab '{tab_name}' contains {module_count} modules.\n\n"
                "Deleting this tab will permanently remove all modules in it.\n\n"
                "Are you sure you want to continue?"
            )
        else:
            result = messagebox.askyesno(
                "Confirm Delete",
                f"Are you sure you want to delete the tab '{tab_name}'?"
            )

        if result:
            tab_module.remove_tab(tab_name)
            self.app.canvas_panel._refresh_tab_module(tab_module)
            self.app.set_modified(True)
            # Trigger preview update for deleted tab
            self.app.preview_manager.request_preview_update()
            # Clear properties panel
            self.clear()
