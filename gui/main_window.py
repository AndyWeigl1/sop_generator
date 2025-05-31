# gui/main_window.py
import customtkinter as ctk
from typing import Dict, List


class MainWindow:
    """Main window layout for SOP Builder"""

    def __init__(self, app_instance):
        self.app = app_instance
        self.root = app_instance.root

        # Configure main window
        self.root.title("SOP Builder - Professional SOP Creation Tool")
        self.root.geometry("1600x900")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self._create_layout()

    def _create_layout(self):
        """Create the main window layout"""

        # 1. TOP MENU BAR
        self.menu_frame = ctk.CTkFrame(self.root, height=40, fg_color="gray25")
        self.menu_frame.grid(row=0, column=0, columnspan=3, sticky="ew")
        self.menu_frame.grid_propagate(False)

        # Menu buttons
        self.new_btn = ctk.CTkButton(self.menu_frame, text="New", width=80)
        self.new_btn.pack(side="left", padx=5, pady=5)

        # Add Blank Project button
        self.blank_btn = ctk.CTkButton(
            self.menu_frame,
            text="Blank",
            width=80,
            fg_color="gray40",
            hover_color="gray50"
        )
        self.blank_btn.pack(side="left", padx=2)

        self.open_btn = ctk.CTkButton(self.menu_frame, text="Open", width=80)
        self.open_btn.pack(side="left", padx=5)

        self.save_btn = ctk.CTkButton(self.menu_frame, text="Save", width=80)
        self.save_btn.pack(side="left", padx=5)

        self.export_btn = ctk.CTkButton(self.menu_frame, text="Export HTML", width=100)
        self.export_btn.pack(side="left", padx=5)

        # 2. LEFT PANEL - Module Library
        self.module_panel = ctk.CTkFrame(self.root, width=250, fg_color="gray20")
        self.module_panel.grid(row=1, column=0, sticky="nsew", padx=(5, 0), pady=5)
        self.module_panel.grid_propagate(False)

        # Module panel header
        module_header = ctk.CTkLabel(self.module_panel, text="Content Modules",
                                     font=("Arial", 16, "bold"))
        module_header.pack(pady=10)

        # Module list (scrollable)
        self.module_list = ctk.CTkScrollableFrame(self.module_panel, fg_color="gray15")
        self.module_list.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # 3. CENTER PANEL - Canvas/Workspace
        self.canvas_frame = ctk.CTkFrame(self.root, fg_color="gray10")
        self.canvas_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

        # Canvas header
        canvas_header_frame = ctk.CTkFrame(self.canvas_frame, height=40, fg_color="gray15")
        canvas_header_frame.pack(fill="x")
        canvas_header_frame.pack_propagate(False)

        canvas_title = ctk.CTkLabel(canvas_header_frame, text="SOP Canvas",
                                    font=("Arial", 14))
        canvas_title.pack(side="left", padx=10)

        # Preview toggle
        self.preview_toggle = ctk.CTkSwitch(canvas_header_frame, text="Preview Mode")
        self.preview_toggle.pack(side="right", padx=10)

        # Canvas workspace (scrollable)
        self.canvas = ctk.CTkScrollableFrame(self.canvas_frame, fg_color="gray12")
        self.canvas.pack(fill="both", expand=True, padx=10, pady=10)

        # 4. RIGHT PANEL - Properties
        self.properties_panel = ctk.CTkFrame(self.root, width=300, fg_color="gray20")
        self.properties_panel.grid(row=1, column=2, sticky="nsew", padx=(0, 5), pady=5)
        self.properties_panel.grid_propagate(False)

        # Properties header
        props_header = ctk.CTkLabel(self.properties_panel, text="Module Properties",
                                    font=("Arial", 16, "bold"))
        props_header.pack(pady=10)

        # Properties content
        self.properties_content = ctk.CTkScrollableFrame(self.properties_panel,
                                                         fg_color="gray15")
        self.properties_content.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Configure grid weights
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

    def populate_module_library(self, modules: List[Dict[str, str]]):
        """Populate the module library with available modules"""
        for module in modules:
            module_btn = ctk.CTkButton(
                self.module_list,
                text=module['name'],
                height=40,
                fg_color="gray25",
                hover_color="gray30",
                anchor="w",
                command=lambda m=module: self.app.add_module_to_canvas(m['type'])
            )
            module_btn.pack(fill="x", pady=2)

            # Add icon if available
            if module.get('icon'):
                module_btn.configure(image=module['icon'], compound="left")


# Example of module button configuration
AVAILABLE_MODULES = [
    {'name': '📄 Text Content', 'type': 'text'},
    {'name': '🖼️ Media Container', 'type': 'media'},
    {'name': '🎬 Media Grid', 'type': 'media_grid'},
    {'name': '📊 Table', 'type': 'table'},
    {'name': '📋 Step Card', 'type': 'step_card'},
    {'name': '⚠️ Disclaimer Box', 'type': 'disclaimer'},
    {'name': '📑 Tab Section', 'type': 'tabs'},
    {'name': '🔧 Issue Card', 'type': 'issue_card'},
    {'name': '🎯 Section Title', 'type': 'section_title'},
    {'name': '📌 Header', 'type': 'header'},
    {'name': '📍 Footer', 'type': 'footer'},
]

# Visual representation of layout:
"""
+------------------------------------------------------------------+
|  [New] [Open] [Save] [Export HTML]                    [Settings] |
+------------------+--------------------------------+--------------+
| Content Modules  |         SOP Canvas             |  Properties  |
|                  |  [Preview Mode Toggle]         |              |
| 📄 Text Content  |                                |  Selected:   |
| 🖼️ Media         |  +------------------------+   |  Step Card   |
| 📊 Table         |  | Header Module          |   |              |
| 📋 Step Card     |  +------------------------+   |  Number: [1] |
| ⚠️ Disclaimer    |                                |              |
| 📑 Tabs          |  +------------------------+   |  Title:      |
| 🔧 Issue Card    |  | Step Card Module       |   |  [________] |
| 🎯 Section Title |  | 1. Configure Settings  |   |              |
|                  |  +------------------------+   |  Content:    |
|                  |                                |  [________] |
|                  |  +------------------------+   |  [________] |
|                  |  | Media Module           |   |              |
|                  |  | [Image Preview]        |   |  Type:       |
|                  |  +------------------------+   |  [Dropdown]  |
|                  |                                |              |
+------------------+--------------------------------+--------------+
"""