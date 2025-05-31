# app/sop_builder.py
import customtkinter as ctk
from typing import List, Optional
from modules.base_module import Module


class SOPBuilderApp:
    """Main application class for SOP Builder"""

    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("SOP Builder")
        self.root.geometry("1400x800")

        # Data structures
        self.available_modules = []  # Module classes
        self.active_modules = []  # Module instances in current SOP
        self.current_project = None
        self.selected_module = None

        # Initialize UI
        self._setup_ui()
        self._load_module_types()

    def _setup_ui(self):
        """Initialize the main UI layout"""
        # Configure grid weights
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        # Create main panels
        self._create_menu_bar()
        self._create_module_panel()
        self._create_canvas_panel()
        self._create_properties_panel()

    def _create_menu_bar(self):
        """Create top menu bar"""
        # Implementation for menu bar
        pass

    def _create_module_panel(self):
        """Create left panel with available modules"""
        # Implementation for module panel
        pass

    def _create_canvas_panel(self):
        """Create central canvas for drag-drop"""
        # Implementation for canvas panel
        pass

    def _create_properties_panel(self):
        """Create right panel for module properties"""
        # Implementation for properties panel
        pass

    def _load_module_types(self):
        """Load all available module types"""
        # Dynamically load module classes
        pass

    def add_module(self, module_type: str):
        """Add a new module instance to the SOP"""
        # Create module instance and add to canvas
        pass

    def remove_module(self, module_id: str):
        """Remove a module from the SOP"""
        pass

    def reorder_modules(self, module_id: str, new_position: int):
        """Reorder modules in the SOP"""
        pass

    def export_to_html(self, filepath: str):
        """Export current SOP to HTML file"""
        # Compile all modules and base template
        pass

    def save_project(self, filepath: str):
        """Save current project state"""
        pass

    def load_project(self, filepath: str):
        """Load project from file"""
        pass

    def run(self):
        """Start the application"""
        self.root.mainloop()