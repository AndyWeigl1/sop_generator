# gui/main_window.py - Enhanced with drag and drop from module library
import customtkinter as ctk
from typing import Dict, List
import tkinter as tk


class ResizablePanedWindow(ctk.CTkFrame):
    """Custom resizable paned window for CustomTkinter using grid layout"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        # Initial proportions (as percentages)
        self.left_weight = 60  # 65% for canvas
        self.right_weight = 22  # 35% for properties panel (increased from ~25%)
        self.min_left_percent = 30  # Minimum 30% for canvas
        self.min_right_percent = 25  # Minimum 25% for properties

        # Configure grid
        self.grid_columnconfigure(0, weight=self.left_weight, minsize=400)  # Canvas column
        self.grid_columnconfigure(1, weight=0, minsize=8)  # Splitter column
        self.grid_columnconfigure(2, weight=self.right_weight, minsize=350)  # Properties column
        self.grid_rowconfigure(0, weight=1)

        # Create frames
        self.left_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 2))

        # Create splitter
        self.splitter = ctk.CTkFrame(self, width=8, fg_color="gray30")
        self.splitter.grid(row=0, column=1, sticky="ns")

        self.right_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.right_frame.grid(row=0, column=2, sticky="nsew", padx=(2, 0))

        # Drag state
        self.dragging = False
        self.drag_start_x = 0
        self.start_left_weight = 0
        self.start_right_weight = 0

        # Configure splitter cursor and events
        self.splitter.configure(cursor="sb_h_double_arrow")
        self.splitter.bind("<Button-1>", self.start_drag)
        self.splitter.bind("<B1-Motion>", self.on_drag)
        self.splitter.bind("<ButtonRelease-1>", self.end_drag)
        self.splitter.bind("<Enter>", self.on_splitter_enter)
        self.splitter.bind("<Leave>", self.on_splitter_leave)

        # Track mouse globally during drag for better UX
        self.root_widget = self._get_root_widget()

    def _get_root_widget(self):
        """Get the root widget"""
        widget = self
        while widget.master:
            widget = widget.master
        return widget

    def start_drag(self, event):
        """Start dragging the splitter"""
        self.dragging = True
        self.drag_start_x = event.x_root
        self.start_left_weight = self.left_weight
        self.start_right_weight = self.right_weight
        self.splitter.configure(fg_color="blue")  # Visual feedback

        # Bind global mouse events for smooth dragging
        self.root_widget.bind("<B1-Motion>", self.on_global_drag, add=True)
        self.root_widget.bind("<ButtonRelease-1>", self.on_global_release, add=True)

        # Prevent event propagation
        return "break"

    def on_drag(self, event):
        """Handle splitter dragging"""
        if not self.dragging:
            return

        self._update_weights_from_drag(event.x_root)

    def on_global_drag(self, event):
        """Handle global drag motion"""
        if self.dragging:
            self._update_weights_from_drag(event.x_root)
            return "break"

    def on_global_release(self, event):
        """Handle global mouse release"""
        if self.dragging:
            self.end_drag(event)
            return "break"

    def _update_weights_from_drag(self, current_x):
        """Update column weights based on drag position"""
        if not self.dragging:
            return

        # Calculate movement as percentage of total width
        delta_x = current_x - self.drag_start_x
        total_width = self.winfo_width()

        if total_width <= 0:
            return

        # Convert pixel movement to weight change
        weight_change = (delta_x / total_width) * 100

        # Calculate new weights
        new_left_weight = max(self.min_left_percent, self.start_left_weight + weight_change)
        new_right_weight = max(self.min_right_percent, self.start_right_weight - weight_change)

        # Ensure weights are reasonable
        total_weight = new_left_weight + new_right_weight
        if total_weight > 0:
            # Normalize weights to ensure they add up properly
            self.left_weight = new_left_weight
            self.right_weight = new_right_weight

            # Update grid weights
            self.grid_columnconfigure(0, weight=int(self.left_weight))
            self.grid_columnconfigure(2, weight=int(self.right_weight))

    def end_drag(self, event):
        """End dragging the splitter"""
        if self.dragging:
            self.dragging = False
            self.splitter.configure(fg_color="gray30")

            # Unbind global mouse events
            try:
                self.root_widget.unbind("<B1-Motion>")
                self.root_widget.unbind("<ButtonRelease-1>")
            except:
                pass  # Events might not be bound

        return "break"

    def on_splitter_enter(self, event):
        """Visual feedback when hovering over splitter"""
        if not self.dragging:
            self.splitter.configure(fg_color="gray40")

    def on_splitter_leave(self, event):
        """Remove visual feedback when leaving splitter"""
        if not self.dragging:
            self.splitter.configure(fg_color="gray30")

    def get_panel_widths(self):
        """Get current panel widths for display"""
        total_width = self.winfo_width()
        if total_width > 0:
            left_width = int((self.left_weight / (self.left_weight + self.right_weight)) * total_width)
            right_width = total_width - left_width - 8  # Account for splitter
            return left_width, right_width
        return 800, 400  # Default values


class MainWindow:
    """Main window layout for SOP Builder with enhanced drag and drop support"""

    def __init__(self, app_instance):
        self.app = app_instance
        self.root = app_instance.root

        # Configure main window
        self.root.title("SOP Builder - Professional SOP Creation Tool")
        self.root.geometry("1400x700")  # Slightly wider to accommodate larger properties panel
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Drag and drop state for module library
        self.library_drag_data = None
        self.library_drag_preview = None
        self.is_dragging_from_library = False

        self._create_layout()

    def _create_layout(self):
        """Create the main window layout with resizable panels"""

        # 1. TOP MENU BAR
        self.menu_frame = ctk.CTkFrame(self.root, height=50, fg_color="gray25")
        self.menu_frame.grid(row=0, column=0, columnspan=3, sticky="ew")
        self.menu_frame.grid_propagate(False)

        # Menu buttons with improved styling
        button_style = {
            "height": 35,
            "font": ("Arial", 12, "bold"),
            "corner_radius": 6
        }

        self.new_btn = ctk.CTkButton(self.menu_frame, text="📄 New Project", width=130, **button_style)
        self.new_btn.pack(side="left", padx=8, pady=8)

        # Add Blank Project button
        self.blank_btn = ctk.CTkButton(
            self.menu_frame,
            text="📋 Blank",
            width=100,
            fg_color="gray40",
            hover_color="gray50",
            **button_style
        )
        self.blank_btn.pack(side="left", padx=2)

        self.open_btn = ctk.CTkButton(self.menu_frame, text="📂 Open", width=100, **button_style)
        self.open_btn.pack(side="left", padx=8)

        self.save_btn = ctk.CTkButton(self.menu_frame, text="💾 Save", width=100, **button_style)
        self.save_btn.pack(side="left", padx=8)

        self.export_btn = ctk.CTkButton(
            self.menu_frame,
            text="🌐 Export HTML",
            width=140,
            fg_color="green",
            hover_color="darkgreen",
            **button_style
        )
        self.export_btn.pack(side="left", padx=8)

        # Status indicator
        self.status_label = ctk.CTkLabel(
            self.menu_frame,
            text="Ready - Drag modules from left panel to canvas",
            font=("Arial", 11),
            text_color="gray"
        )
        self.status_label.pack(side="right", padx=20)

        # Version info
        version_label = ctk.CTkLabel(
            self.menu_frame,
            text="v2.1",
            font=("Arial", 10),
            text_color="gray"
        )
        version_label.pack(side="right", padx=15)

        # 2. MAIN CONTENT AREA WITH THREE PANELS
        # Left panel (fixed width), Center+Right panels (resizable)

        # Left panel - Module Library (fixed width)
        self.module_panel = ctk.CTkFrame(self.root, width=280, fg_color="gray20")
        self.module_panel.grid(row=1, column=0, sticky="nsew", padx=(8, 4), pady=8)
        self.module_panel.grid_propagate(False)

        # Create resizable center+right area
        self.main_content_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.main_content_frame.grid(row=1, column=1, sticky="nsew", padx=(4, 8), pady=8)

        # Create resizable paned window for canvas and properties
        self.paned_window = ResizablePanedWindow(self.main_content_frame, fg_color="transparent")
        self.paned_window.pack(fill="both", expand=True)

        # 3. CANVAS PANEL (in left side of paned window)
        self.canvas_frame = ctk.CTkFrame(self.paned_window.left_frame, fg_color="gray10")
        self.canvas_frame.pack(fill="both", expand=True)

        # Canvas header
        canvas_header_frame = ctk.CTkFrame(self.canvas_frame, height=50, fg_color="gray15")
        canvas_header_frame.pack(fill="x", padx=8, pady=(8, 0))
        canvas_header_frame.pack_propagate(False)

        canvas_title = ctk.CTkLabel(
            canvas_header_frame,
            text="🎨 SOP Canvas",
            font=("Arial", 16, "bold")
        )
        canvas_title.pack(side="left", padx=15, pady=12)

        # Preview toggle with better styling
        self.preview_toggle = ctk.CTkSwitch(
            canvas_header_frame,
            text="👁️ Preview Mode",
            font=("Arial", 12)
        )
        self.preview_toggle.pack(side="right", padx=15, pady=12)

        # Canvas workspace (scrollable)
        self.canvas = ctk.CTkScrollableFrame(
            self.canvas_frame,
            fg_color="gray12",
            corner_radius=8
        )
        self.canvas.pack(fill="both", expand=True, padx=8, pady=8)

        # 4. PROPERTIES PANEL (in right side of paned window)
        self.properties_panel = ctk.CTkFrame(self.paned_window.right_frame, fg_color="gray20")
        self.properties_panel.pack(fill="both", expand=True)

        # Properties header
        props_header_frame = ctk.CTkFrame(self.properties_panel, fg_color="gray25", height=50)
        props_header_frame.pack(fill="x", padx=8, pady=(8, 0))
        props_header_frame.pack_propagate(False)

        props_header = ctk.CTkLabel(
            props_header_frame,
            text="⚙️ Module Properties",
            font=("Arial", 16, "bold")
        )
        props_header.pack(side="left", padx=15, pady=12)

        # Properties panel width indicator
        self.width_indicator = ctk.CTkLabel(
            props_header_frame,
            text="",
            font=("Arial", 10),
            text_color="gray"
        )
        self.width_indicator.pack(side="right", padx=15, pady=12)

        # Properties content
        self.properties_content = ctk.CTkFrame(
            self.properties_panel,
            fg_color="gray15",
            corner_radius=8
        )
        self.properties_content.pack(fill="both", expand=True, padx=8, pady=8)

        # 5. MODULE LIBRARY CONTENT
        self._create_module_library()

        # Configure grid weights
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(1, weight=1)  # Make main content area expandable

        # Update width indicator initially
        self.root.after(100, self.update_width_indicator)

    def _create_module_library(self):
        """Create the module library in the left panel"""
        # Module panel header
        header_frame = ctk.CTkFrame(self.module_panel, fg_color="gray25", height=50)
        header_frame.pack(fill="x", padx=8, pady=(8, 0))
        header_frame.pack_propagate(False)

        module_header = ctk.CTkLabel(
            header_frame,
            text="📦 Content Modules",
            font=("Arial", 16, "bold")
        )
        module_header.pack(pady=12)

        # Instructions label
        instructions_frame = ctk.CTkFrame(self.module_panel, fg_color="transparent")
        instructions_frame.pack(fill="x", padx=8, pady=(5, 0))

        instructions_label = ctk.CTkLabel(
            instructions_frame,
            text="💡 Drag modules to canvas or click to add",
            font=("Arial", 10),
            text_color="lightblue",
            wraplength=250
        )
        instructions_label.pack(pady=3)

        # Search/filter frame
        search_frame = ctk.CTkFrame(self.module_panel, fg_color="transparent")
        search_frame.pack(fill="x", padx=8, pady=(8, 0))

        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="🔍 Search modules...",
            height=32,
            font=("Arial", 11)
        )
        self.search_entry.pack(fill="x", pady=5)

        # Module categories
        self._create_module_categories()

    def _create_module_categories(self):
        """Create categorized module library with drag and drop support"""
        # Main modules container
        self.module_list = ctk.CTkScrollableFrame(
            self.module_panel,
            fg_color="gray15",
            corner_radius=8
        )
        self.module_list.pack(fill="both", expand=True, padx=8, pady=8)

        # Module categories with better organization
        categories = {
            "📄 Structure": [
                {'name': '📄 Header', 'type': 'header', 'desc': 'Document title and logo'},
                {'name': '🎯 Section Title', 'type': 'section_title', 'desc': 'Section headings'},
                {'name': '📑 Tab Section', 'type': 'tabs', 'desc': 'Organize content in tabs'},
                {'name': '📍 Footer', 'type': 'footer', 'desc': 'Document footer with info'},
            ],
            "📝 Content": [
                {'name': '📝 Text Content', 'type': 'text', 'desc': 'Paragraphs and formatted text'},
                {'name': '⚠️ Disclaimer Box', 'type': 'disclaimer', 'desc': 'Important notices and warnings'},
                {'name': '🔧 Issue Card', 'type': 'issue_card', 'desc': 'Common problems and solutions'},
            ],
            "📊 Data & Media": [
                {'name': '🖼️ Media Item', 'type': 'media', 'desc': 'Single image or video with caption'},
                {'name': '🎬 Media Grid', 'type': 'media_grid', 'desc': 'Multiple images in grid layout'},
                {'name': '📊 Table', 'type': 'table', 'desc': 'Data tables and charts'},
            ]
        }

        for category_name, modules in categories.items():
            self._create_category_section(category_name, modules)

    def _create_category_section(self, category_name: str, modules: List[Dict]):
        """Create a category section with modules"""
        # Category header
        category_frame = ctk.CTkFrame(self.module_list, fg_color="gray20")
        category_frame.pack(fill="x", pady=(5, 0))

        category_label = ctk.CTkLabel(
            category_frame,
            text=category_name,
            font=("Arial", 13, "bold"),
            anchor="w"
        )
        category_label.pack(side="left", padx=12, pady=8)

        # Modules in category
        for module in modules:
            self._create_module_button(module)

    def _create_module_button(self, module_info: Dict):
        """Create an enhanced module button with drag and drop support"""
        module_frame = ctk.CTkFrame(self.module_list, fg_color="gray18")
        module_frame.pack(fill="x", pady=2, padx=5)

        # Main button area
        button_area = ctk.CTkFrame(module_frame, fg_color="transparent")
        button_area.pack(fill="x", padx=8, pady=6)

        # Module button with drag handle
        button_container = ctk.CTkFrame(button_area, fg_color="transparent")
        button_container.pack(fill="x")

        # Drag handle
        drag_handle = ctk.CTkLabel(
            button_container,
            text="⋮⋮",
            font=("Arial", 12, "bold"),
            text_color="white",
            width=25,
            height=40,
            fg_color="gray30",
            corner_radius=3,
            cursor="hand2"
        )
        drag_handle.pack(side="left", padx=(0, 5))

        # Module button
        module_btn = ctk.CTkButton(
            button_container,
            text=module_info['name'],
            height=40,
            font=("Arial", 12, "bold"),
            fg_color="gray25",
            hover_color="gray30",
            anchor="w",
            command=lambda: self.app.add_module_to_canvas(module_info['type'])
        )
        module_btn.pack(side="left", fill="x", expand=True)

        # Description
        if 'desc' in module_info:
            desc_label = ctk.CTkLabel(
                button_area,
                text=module_info['desc'],
                font=("Arial", 10),
                text_color="gray",
                anchor="w",
                wraplength=220
            )
            desc_label.pack(fill="x", pady=(3, 0))

        # Enable drag and drop for this module button
        self._enable_module_library_drag(drag_handle, module_btn, module_info)

        # Hover effects
        def on_enter(event):
            module_btn.configure(fg_color="gray35")
            drag_handle.configure(fg_color="gray40")

        def on_leave(event):
            module_btn.configure(fg_color="gray25")
            drag_handle.configure(fg_color="gray30")

        module_btn.bind("<Enter>", on_enter)
        module_btn.bind("<Leave>", on_leave)
        drag_handle.bind("<Enter>", on_enter)
        drag_handle.bind("<Leave>", on_leave)

    def _enable_module_library_drag(self, drag_handle: ctk.CTkLabel, module_btn: ctk.CTkButton, module_info: Dict):
        """Enable drag and drop from module library"""

        def start_library_drag(event):
            """Start dragging a module from the library"""
            self.is_dragging_from_library = True
            self.library_drag_data = {
                'module_type': module_info['type'],
                'module_name': module_info['name'],
                'start_x': event.x_root,
                'start_y': event.y_root,
                'source_widget': drag_handle
            }

            # Create drag preview
            self._create_library_drag_preview(event.x_root, event.y_root, module_info['name'])

            # Visual feedback on source
            try:
                drag_handle.configure(fg_color="blue")
                module_btn.configure(fg_color="blue")
            except tk.TclError:
                pass

            # Bind global drag events
            try:
                self.root.bind('<B1-Motion>', on_library_drag_motion)
                self.root.bind('<ButtonRelease-1>', end_library_drag)
            except tk.TclError:
                self._cleanup_library_drag()
                return

            # Update status
            self.set_status("Dragging module - drop on canvas to add", "lightblue")

        def on_library_drag_motion(event):
            """Handle drag motion from library"""
            if not self.library_drag_data or not self.is_dragging_from_library:
                return

            # Update drag preview position
            if self.library_drag_preview:
                try:
                    self.library_drag_preview.geometry(f"250x50+{event.x_root + 10}+{event.y_root + 10}")
                except:
                    pass

            # Check if we're over the canvas and provide visual feedback
            try:
                widget_under_cursor = self.root.winfo_containing(event.x_root, event.y_root)
                self._update_library_drop_feedback(widget_under_cursor)
            except tk.TclError:
                pass

        def end_library_drag(event):
            """End library drag and handle drop"""
            if not self.library_drag_data or not self.is_dragging_from_library:
                return

            try:
                # Find drop target
                drop_target = self.root.winfo_containing(event.x_root, event.y_root)

                # Debug: Print what we're dropping on
                # print(f"Drop target: {drop_target}")
                # print(f"Drop target class: {drop_target.__class__.__name__ if drop_target else 'None'}")

                # Check if dropped on canvas area
                if self._is_canvas_drop_target(drop_target):
                    # Check if canvas panel can handle the drop more specifically
                    if hasattr(self.app, 'canvas_panel'):
                        success = self.app.canvas_panel.handle_library_drop(drop_target,
                                                                            self.library_drag_data['module_type'])
                        if success:
                            self.set_status(f"Added {self.library_drag_data['module_name']} to canvas", "green")
                        else:
                            # Fallback to app method
                            module_type = self.library_drag_data['module_type']
                            self.app.add_module_to_canvas(module_type)
                            self.set_status(f"Added {self.library_drag_data['module_name']} to canvas", "green")
                    else:
                        # Fallback if no canvas panel
                        module_type = self.library_drag_data['module_type']
                        self.app.add_module_to_canvas(module_type)
                        self.set_status(f"Added {self.library_drag_data['module_name']} to canvas", "green")
                else:
                    self.set_status("Drop cancelled - drag to canvas area to add modules", "orange")

            except tk.TclError:
                self.set_status("Drop cancelled", "orange")

            # Cleanup
            self._cleanup_library_drag()

        # Bind drag initiation to drag handle
        try:
            drag_handle.bind('<Button-1>', start_library_drag)
        except tk.TclError:
            pass

    def _create_library_drag_preview(self, x: int, y: int, module_name: str):
        """Create drag preview for library modules"""
        try:
            self.library_drag_preview = ctk.CTkToplevel(self.root)
            self.library_drag_preview.overrideredirect(True)
            self.library_drag_preview.attributes('-alpha', 0.8)
            self.library_drag_preview.geometry(f"250x50+{x + 10}+{y + 10}")

            # Preview content
            preview_frame = ctk.CTkFrame(self.library_drag_preview, fg_color="lightblue", corner_radius=8)
            preview_frame.pack(fill="both", expand=True, padx=2, pady=2)

            preview_label = ctk.CTkLabel(
                preview_frame,
                text=f"➕ {module_name}",
                font=("Arial", 12, "bold"),
                text_color="white"
            )
            preview_label.pack(expand=True)

            instruction_label = ctk.CTkLabel(
                preview_frame,
                text="Drop on canvas to add",
                font=("Arial", 9),
                text_color="white"
            )
            instruction_label.pack()

        except Exception as e:
            print(f"Error creating library drag preview: {e}")
            self.library_drag_preview = None

    def _update_library_drop_feedback(self, widget_under_cursor):
        """Update visual feedback when dragging from library"""
        # For now, we'll let the canvas panel handle detailed drop zone highlighting
        # But we can update the cursor or preview here if needed
        pass

    def _is_canvas_drop_target(self, widget) -> bool:
        """Check if the widget is a valid drop target for library modules"""
        if not widget:
            return False

        # Check if widget is part of the canvas area
        current = widget
        while current:
            try:
                # Check if this widget is marked as a canvas drop zone
                if hasattr(current, '_is_canvas_drop_zone') and current._is_canvas_drop_zone:
                    return True

                # Check if this is the canvas scrollable frame or its children
                if (hasattr(self.app, 'canvas_panel') and
                        hasattr(self.app.canvas_panel, 'modules_frame') and
                        current == self.app.canvas_panel.modules_frame):
                    return True

                # Check if this is the main canvas area
                if current == self.canvas:
                    return True

                # Check if this is the canvas frame
                if current == self.canvas_frame:
                    return True

                # Check if this is a tab drop zone
                if hasattr(current, '_drop_zone_info'):
                    return True

                # Check if current widget is a child of the canvas
                if (hasattr(self.app, 'canvas_panel') and
                        hasattr(self.app.canvas_panel, 'parent') and
                        current == self.app.canvas_panel.parent):
                    return True

                current = current.master
            except (tk.TclError, AttributeError):
                break

        return False

    def _cleanup_library_drag(self):
        """Clean up library drag state"""
        self.is_dragging_from_library = False

        # Destroy drag preview
        if self.library_drag_preview:
            try:
                self.library_drag_preview.destroy()
            except:
                pass
            self.library_drag_preview = None

        # Reset source widget appearance
        if self.library_drag_data and self.library_drag_data.get('source_widget'):
            source_widget = self.library_drag_data['source_widget']
            try:
                if self._safe_widget_exists(source_widget):
                    source_widget.configure(fg_color="gray30")
                    # Find the associated button and reset it too
                    parent = source_widget.master
                    if parent and self._safe_widget_exists(parent):
                        for child in parent.winfo_children():
                            if isinstance(child, ctk.CTkButton) and self._safe_widget_exists(child):
                                child.configure(fg_color="gray25")
                                break
            except (tk.TclError, AttributeError):
                pass

        # Unbind global events
        try:
            self.root.unbind('<B1-Motion>')
            self.root.unbind('<ButtonRelease-1>')
        except:
            pass

        self.library_drag_data = None

    def _safe_widget_exists(self, widget):
        """Safely check if a widget exists and hasn't been destroyed"""
        if widget is None:
            return False
        try:
            return widget.winfo_exists()
        except tk.TclError:
            return False

    def update_width_indicator(self):
        """Update the properties panel width indicator"""
        if hasattr(self, 'paned_window') and hasattr(self, 'width_indicator'):
            try:
                left_width, right_width = self.paned_window.get_panel_widths()
                self.width_indicator.configure(text=f"{right_width}px wide")
            except:
                self.width_indicator.configure(text="400px wide")
            # Schedule next update
            self.root.after(500, self.update_width_indicator)

    def set_status(self, message: str, color: str = "gray"):
        """Update the status indicator"""
        if hasattr(self, 'status_label'):
            self.status_label.configure(text=message, text_color=color)

    def populate_module_library(self, modules: List[Dict[str, str]]):
        """Populate the module library (now handled by _create_module_categories)"""
        # This method is kept for compatibility but modules are now organized by category
        pass


# Updated module information with clearer descriptions
AVAILABLE_MODULES = [
    # Structure modules
    {'name': '📄 Header', 'type': 'header', 'category': 'structure'},
    {'name': '🎯 Section Title', 'type': 'section_title', 'category': 'structure'},
    {'name': '📑 Tab Section', 'type': 'tabs', 'category': 'structure'},
    {'name': '📍 Footer', 'type': 'footer', 'category': 'structure'},

    # Content modules
    {'name': '📝 Text Content', 'type': 'text', 'category': 'content'},
    {'name': '⚠️ Disclaimer Box', 'type': 'disclaimer', 'category': 'content'},
    {'name': '🔧 Issue Card', 'type': 'issue_card', 'category': 'content'},

    # Data & Media modules
    {'name': '🖼️ Media Item', 'type': 'media', 'category': 'media'},
    {'name': '🎬 Media Grid', 'type': 'media_grid', 'category': 'media'},
    {'name': '📊 Table', 'type': 'table', 'category': 'data'},
]
