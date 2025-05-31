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
        """Create a new SOP project"""
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
        self.root.title("SOP Builder - New Project")

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
        """Export current SOP to HTML file"""
        if not self.active_modules:
            messagebox.showwarning("No Content", "Please add some modules before exporting.")
            return

        filename = filedialog.asksaveasfilename(
            title="Export SOP as HTML",
            defaultextension=".html",
            filetypes=[("HTML Files", "*.html"), ("All Files", "*.*")]
        )

        if filename:
            try:
                # Generate HTML
                html_content = self.html_generator.generate_html(self.active_modules)

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


