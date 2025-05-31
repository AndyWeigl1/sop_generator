# app/sop_builder.py
import customtkinter as ctk
from typing import List, Optional, Dict
from modules.base_module import Module
from modules.module_factory import ModuleFactory
from gui.main_window import MainWindow, AVAILABLE_MODULES
from gui.canvas_panel import CanvasPanel
from gui.properties_panel import PropertiesPanel
import json
from pathlib import Path
from tkinter import filedialog, messagebox
from utils.html_generator import HTMLGenerator
from utils.project_manager import ProjectManager


class SOPBuilderApp:
    """Main application class for SOP Builder"""

    def __init__(self):
        self.root = ctk.CTk()

        # Data structures
        self.active_modules: List[Module] = []  # Module instances in current SOP
        self.current_project_path: Optional[Path] = None
        self.selected_module: Optional[Module] = None
        self.is_modified = False

        # Initialize components
        self.main_window = MainWindow(self)
        self.html_generator = HTMLGenerator()
        self.project_manager = ProjectManager()

        # Create GUI panels
        self.canvas_panel = CanvasPanel(self.main_window.canvas, self)
        self.properties_panel = PropertiesPanel(self.main_window.properties_content, self)

        # Setup
        self._setup_menu_handlers()
        self._populate_module_library()

    def _setup_menu_handlers(self):
        """Connect menu buttons to their handlers"""
        self.main_window.new_btn.configure(command=self.new_project)
        self.main_window.open_btn.configure(command=self.open_project)
        self.main_window.save_btn.configure(command=self.save_project)
        self.main_window.export_btn.configure(command=self.export_to_html)
        self.main_window.preview_toggle.configure(command=self.toggle_preview)

    def _setup_base_template(self):
        """Create the base SOP template with Header, Tab, and Section Title"""
        try:
            # 1. Add Header Module
            header_module = ModuleFactory.create_module('header')
            header_module.position = 0
            header_module.update_content('title', 'Standard Operating Procedure')
            header_module.update_content('subtitle', 'Process Name')
            header_module.update_content('date', 'Last Updated: MM/DD/YYYY')

            self.active_modules.append(header_module)
            self.canvas_panel.add_module_widget(header_module)

            # 2. Add Tab Module
            tab_module = ModuleFactory.create_module('tabs')
            tab_module.position = 1
            # Set up default tabs
            tab_module.update_content('tabs', ['Instructions', 'Common Issues'])
            tab_module.update_content('active_tab', 0)

            self.active_modules.append(tab_module)
            self.canvas_panel.add_module_widget(tab_module)

            # 3. Add Section Title Module (this would typically go inside a tab)
            section_title_module = ModuleFactory.create_module('section_title')
            section_title_module.position = 2
            section_title_module.update_content('title', 'Getting Started')
            section_title_module.update_content('subtitle', 'Follow these steps to complete the process')
            section_title_module.update_content('style', 'default')
            section_title_module.update_content('size', 'large')

            self.active_modules.append(section_title_module)
            self.canvas_panel.add_module_widget(section_title_module)

            # Update positions for all modules
            self._update_module_positions()

            # Mark as not modified since this is the base template
            self.set_modified(False)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to create base template: {str(e)}")

    def _populate_module_library(self):
        """Populate the module library panel"""
        self.main_window.populate_module_library(AVAILABLE_MODULES)

    def add_module_to_canvas(self, module_type: str):
        """Add a new module instance to the SOP"""
        try:
            # Create module instance
            module = ModuleFactory.create_module(module_type)
            module.position = len(self.active_modules)

            # Add to active modules
            self.active_modules.append(module)

            # Add to canvas
            self.canvas_panel.add_module_widget(module)

            # Select the new module
            self.select_module(module)

            # Mark as modified
            self.set_modified(True)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to add module: {str(e)}")

    def select_module(self, module: Module):
        """Select a module and show its properties"""
        self.selected_module = module
        self.properties_panel.show_module_properties(module)
        self.canvas_panel.highlight_module(module)

    def remove_module(self, module_id: str):
        """Remove a module from the SOP"""
        # Find and remove module
        module_to_remove = None
        for module in self.active_modules:
            if module.id == module_id:
                module_to_remove = module
                break

        if module_to_remove:
            self.active_modules.remove(module_to_remove)
            self.canvas_panel.remove_module_widget(module_id)

            # Clear selection if this module was selected
            if self.selected_module == module_to_remove:
                self.selected_module = None
                self.properties_panel.clear()

            # Update positions
            self._update_module_positions()
            self.set_modified(True)

    def reorder_modules(self, module_id: str, new_position: int):
        """Reorder modules in the SOP"""
        # Find module
        module_index = None
        for i, module in enumerate(self.active_modules):
            if module.id == module_id:
                module_index = i
                break

        if module_index is not None:
            # Move module to new position
            module = self.active_modules.pop(module_index)
            self.active_modules.insert(new_position, module)

            # Update positions
            self._update_module_positions()

            # Refresh canvas
            self.canvas_panel.refresh_order()
            self.set_modified(True)

    def _update_module_positions(self):
        """Update position values for all modules"""
        for i, module in enumerate(self.active_modules):
            module.position = i

    def new_project(self):
        """Create a new SOP project with base template"""
        if self.is_modified:
            response = messagebox.askyesnocancel(
                "Save Changes?",
                "Do you want to save changes to the current project?"
            )
            if response is None:  # Cancel
                return
            elif response:  # Yes
                self.save_project()

        # Clear current project
        self.active_modules.clear()
        self.canvas_panel.clear()
        self.properties_panel.clear()
        self.current_project_path = None
        self.selected_module = None

        # Update title
        self.root.title("SOP Builder - New Project")

        # Create base template
        self._setup_base_template()

    def create_blank_project(self):
        """Create a completely blank project (for advanced users)"""
        if self.is_modified:
            response = messagebox.askyesnocancel(
                "Save Changes?",
                "Do you want to save changes to the current project?"
            )
            if response is None:  # Cancel
                return
            elif response:  # Yes
                self.save_project()

        # Clear current project
        self.active_modules.clear()
        self.canvas_panel.clear()
        self.properties_panel.clear()
        self.current_project_path = None
        self.selected_module = None
        self.set_modified(False)

        # Update title
        self.root.title("SOP Builder - Blank Project")

    def open_project(self):
        """Open an existing project"""
        filename = filedialog.askopenfilename(
            title="Open SOP Project",
            filetypes=[("SOP Project", "*.sopx"), ("All Files", "*.*")]
        )

        if filename:
            try:
                # Load project
                project_data = self.project_manager.load_project(filename)

                # Clear current
                self.active_modules.clear()
                self.canvas_panel.clear()

                # Load modules
                for module_data in project_data['modules']:
                    module = self.project_manager.deserialize_module(module_data)
                    self.active_modules.append(module)
                    self.canvas_panel.add_module_widget(module)

                self.current_project_path = Path(filename)
                self.set_modified(False)
                self.root.title(f"SOP Builder - {self.current_project_path.name}")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to open project: {str(e)}")

    def save_project(self, save_as=False):
        """Save current project"""
        if not self.current_project_path or save_as:
            filename = filedialog.asksaveasfilename(
                title="Save SOP Project",
                defaultextension=".sopx",
                filetypes=[("SOP Project", "*.sopx"), ("All Files", "*.*")]
            )
            if filename:
                self.current_project_path = Path(filename)
            else:
                return

        try:
            # Save project
            project_data = {
                'version': '1.0',
                'modules': [self.project_manager.serialize_module(m) for m in self.active_modules]
            }

            self.project_manager.save_project(self.current_project_path, project_data)
            self.set_modified(False)
            self.root.title(f"SOP Builder - {self.current_project_path.name}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save project: {str(e)}")

    def export_to_html(self):
        """Export current SOP to HTML file with theme support"""
        if not self.active_modules:
            messagebox.showwarning("No Content", "Please add some modules before exporting.")
            return

        # Create export dialog with options
        export_dialog = ExportDialog(self.root, self.html_generator.get_available_themes())
        self.root.wait_window(export_dialog.dialog)

        if not export_dialog.result:
            return  # User cancelled

        filename = export_dialog.filename
        embed_css = export_dialog.embed_css
        selected_theme = export_dialog.selected_theme

        if filename:
            try:
                # Set the theme
                self.html_generator.set_theme(selected_theme)

                # Get output directory
                output_path = Path(filename)
                output_dir = output_path.parent

                # Generate HTML
                html_content = self.html_generator.generate_html(
                    self.active_modules,
                    output_dir=output_dir,
                    embed_theme=embed_css
                )

                # Save to file
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(html_content)

                messagebox.showinfo("Success", f"SOP exported successfully to:\n{filename}")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to export HTML: {str(e)}")

    def toggle_preview(self):
        """Toggle between edit and preview modes"""
        preview_mode = self.main_window.preview_toggle.get()
        self.canvas_panel.set_preview_mode(preview_mode)

    def set_modified(self, modified: bool):
        """Set the modified state of the project"""
        self.is_modified = modified
        title = self.root.title()

        if modified and not title.endswith("*"):
            self.root.title(title + " *")
        elif not modified and title.endswith(" *"):
            self.root.title(title[:-2])

    def update_module_property(self, module: Module, property_name: str, value: any):
        """Update a module property"""
        module.update_content(property_name, value)
        self.canvas_panel.update_module_preview(module)
        self.set_modified(True)

    def run(self):
        """Start the application"""
        # Set window close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Start with a new project
        self.new_project()

        # Start the main loop
        self.root.mainloop()

    def on_closing(self):
        """Handle window closing event"""
        if self.is_modified:
            response = messagebox.askyesnocancel(
                "Save Changes?",
                "Do you want to save changes before closing?"
            )
            if response is None:  # Cancel
                return
            elif response:  # Yes
                self.save_project()

        self.root.destroy()


class ExportDialog:
    """Dialog for export options"""

    def __init__(self, parent, available_themes):
        self.result = False
        self.filename = None
        self.embed_css = False
        self.selected_theme = "kodiak"

        # Create dialog window
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Export SOP")
        self.dialog.geometry("500x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (300 // 2)
        self.dialog.geometry(f"+{x}+{y}")

        self._create_widgets(available_themes)

    def _create_widgets(self, available_themes):
        """Create dialog widgets"""
        # Main frame
        main_frame = ctk.CTkFrame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Theme selection
        theme_label = ctk.CTkLabel(main_frame, text="Select Theme:", font=("Arial", 14))
        theme_label.pack(pady=(0, 5))

        self.theme_var = ctk.StringVar(value="kodiak")
        theme_menu = ctk.CTkComboBox(
            main_frame,
            values=available_themes or ["kodiak"],
            variable=self.theme_var,
            width=200
        )
        theme_menu.pack(pady=(0, 20))

        # CSS embedding option
        self.embed_var = ctk.BooleanVar(value=False)
        embed_check = ctk.CTkCheckBox(
            main_frame,
            text="Embed CSS in HTML file (for standalone use)",
            variable=self.embed_var
        )
        embed_check.pack(pady=(0, 20))

        # Info label
        info_label = ctk.CTkLabel(
            main_frame,
            text="Note: If CSS is not embedded, theme files will be copied to the export location.",
            font=("Arial", 11),
            text_color="gray"
        )
        info_label.pack(pady=(0, 20))

        # Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(20, 0))

        export_btn = ctk.CTkButton(
            button_frame,
            text="Export",
            command=self._export,
            width=100
        )
        export_btn.pack(side="right", padx=(10, 0))

        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self._cancel,
            width=100,
            fg_color="gray"
        )
        cancel_btn.pack(side="right")

    def _export(self):
        """Handle export button click"""
        self.filename = filedialog.asksaveasfilename(
            title="Export SOP as HTML",
            defaultextension=".html",
            filetypes=[("HTML Files", "*.html"), ("All Files", "*.*")]
        )

        if self.filename:
            self.embed_css = self.embed_var.get()
            self.selected_theme = self.theme_var.get()
            self.result = True
            self.dialog.destroy()

    def _cancel(self):
        """Handle cancel button click"""
        self.result = False
        self.dialog.destroy()
