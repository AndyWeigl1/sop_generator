# app/sop_builder.py - Enhanced with event-driven preview updates
import customtkinter as ctk
from typing import List, Optional, Dict, Tuple
from modules.base_module import Module
from modules.module_factory import ModuleFactory
from gui.main_window import MainWindow, AVAILABLE_MODULES
from gui.canvas_panel import CanvasPanel
from gui.properties_panel import PropertiesPanel
from modules.complex_module import TabModule
from pathlib import Path
from tkinter import filedialog, messagebox
from utils.html_generator import HTMLGenerator
from utils.project_manager import ProjectManager
from utils.media_discovery import MediaDiscoveryService
from utils.base64_embedder import Base64EmbedderService
from gui.preview_manager import DocumentPreviewManager


class SOPBuilderApp:
    """Main application class for SOP Builder with event-driven preview updates"""

    def __init__(self):
        self.root = ctk.CTk()

        # Data structures
        self.active_modules: List[Module] = []  # Module instances in current SOP
        self.current_project_path: Optional[Path] = None
        self.selected_module: Optional[Module] = None
        self.is_modified = False

        # Tab context tracking
        self.selected_tab_context: Optional[Tuple[TabModule, str]] = None  # (TabModule, tab_name)

        # Initialize components
        self.main_window = MainWindow(self)
        self.html_generator = HTMLGenerator()
        self.project_manager = ProjectManager()
        self.preview_manager = DocumentPreviewManager(self)

        # Create GUI panels
        self.canvas_panel = CanvasPanel(self.main_window.canvas, self)
        self.properties_panel = PropertiesPanel(self.main_window.properties_content, self)

        # Setup
        self._setup_menu_handlers()
        self._populate_module_library()
        self._setup_enhanced_drag_drop()
        self._setup_enhanced_preview()

    def _setup_enhanced_drag_drop(self):
        """Set up enhanced drag and drop integration between library and canvas"""
        # Override the main window's drop handling to integrate with canvas
        original_is_canvas_drop_target = self.main_window._is_canvas_drop_target

        def enhanced_is_canvas_drop_target(widget):
            """Enhanced canvas drop target detection"""
            if original_is_canvas_drop_target(widget):
                return True

            # Also check if it's a valid drop zone using canvas panel logic
            drop_zone = self.canvas_panel._find_library_drop_zone(widget)
            return drop_zone is not None

        self.main_window._is_canvas_drop_target = enhanced_is_canvas_drop_target

        # Enhance the library cleanup to also clear canvas highlights
        original_cleanup = self.main_window._cleanup_library_drag

        def enhanced_cleanup():
            """Enhanced cleanup that also clears canvas highlights"""
            original_cleanup()
            # Only call canvas cleanup if canvas_panel exists and has the method
            if hasattr(self, 'canvas_panel') and hasattr(self.canvas_panel, '_clear_library_drop_highlight'):
                try:
                    self.canvas_panel._clear_library_drop_highlight()
                except Exception as e:
                    print(f"Error clearing canvas highlights: {e}")

        self.main_window._cleanup_library_drag = enhanced_cleanup

    def _setup_menu_handlers(self):
        """Connect menu buttons to their handlers"""
        self.main_window.new_btn.configure(command=self.new_project)
        self.main_window.blank_btn.configure(command=self.create_blank_project)  # Connect blank button
        self.main_window.open_btn.configure(command=self.open_project)
        self.main_window.save_btn.configure(command=self.save_project)
        self.main_window.export_btn.configure(command=self.export_to_html)
        self.main_window.preview_toggle.configure(command=self.toggle_preview)

    def _setup_enhanced_preview(self):
        """Setup enhanced preview functionality"""
        # Replace the broken preview toggle with working functionality
        original_command = self.main_window.preview_toggle.cget("command")
        self.main_window.preview_toggle.configure(command=self.toggle_canvas_preview_mode)

        # Add live preview button to menu
        live_preview_btn = ctk.CTkButton(
            self.main_window.menu_frame,
            text="👁️ Live Preview",
            width=130,
            height=35,
            font=("Arial", 12, "bold"),
            fg_color="purple",
            hover_color="darkmagenta",
            command=self.preview_manager.toggle_live_preview
        )
        # Insert before export button
        live_preview_btn.pack(side="left", padx=8, before=self.main_window.export_btn)

    def toggle_canvas_preview_mode(self):
        """Toggle canvas preview mode (fixed version)"""
        preview_mode = self.main_window.preview_toggle.get()

        if preview_mode:
            # Enter preview mode - simplify view
            self.canvas_panel.set_preview_mode(True)
            self.main_window.set_status("Canvas Preview Mode - editing disabled", "orange")
        else:
            # Exit preview mode - restore editing
            self.canvas_panel.set_preview_mode(False)
            self.main_window.set_status("Edit mode - drag modules from left panel to canvas", "green")

    def _setup_base_template(self):
        """Create the base SOP template with Header, Tab Section (with content), and Footer"""
        try:
            # 1. Add Header Module
            header_module = ModuleFactory.create_module('header')
            header_module.position = 0
            header_module.update_content('title', 'Standard Operating Procedure')
            header_module.update_content('subtitle', 'Process Name')
            header_module.update_content('date', 'Last Updated: MM/DD/YYYY')
            header_module.update_content('logo_path', 'assets/kodiak.png')

            self.active_modules.append(header_module)
            self.canvas_panel.add_module_widget(header_module)

            # 2. Add Tab Module
            tab_module = ModuleFactory.create_module('tabs')
            tab_module.position = 1
            # Set up default tabs (Instructions and Common Issues)
            tab_module.update_content('tabs', ['Instructions', 'Common Issues'])
            tab_module.update_content('active_tab', 0)

            # 3. Create modules for the Instructions tab
            # 3a. Create Disclaimer Box for Instructions tab
            disclaimer_module = ModuleFactory.create_module('disclaimer')
            disclaimer_module.position = 0  # Position within the Instructions tab
            disclaimer_module.update_content('label', 'IMPORTANT!')
            disclaimer_module.update_content('title', 'Before You Begin:')
            disclaimer_module.update_content('content', 'Important information or warnings go here...')
            disclaimer_module.update_content('type', 'warning')
            disclaimer_module.update_content('icon', True)

            # 3b. Create Section Title for Instructions tab
            section_title_module = ModuleFactory.create_module('section_title')
            section_title_module.position = 1  # Position within the Instructions tab
            section_title_module.update_content('title', 'Getting Started')
            section_title_module.update_content('subtitle', 'Follow these steps to complete the process')
            section_title_module.update_content('style', 'default')
            section_title_module.update_content('size', 'large')

            # Add modules to the Instructions tab
            tab_module.add_module_to_tab('Instructions', disclaimer_module)
            tab_module.add_module_to_tab('Instructions', section_title_module)
            # Common Issues tab remains empty as requested

            self.active_modules.append(tab_module)
            self.canvas_panel.add_module_widget(tab_module, with_nested=True)

            # 4. Add Footer Module
            footer_module = ModuleFactory.create_module('footer')
            footer_module.position = 2
            footer_module.update_content('organization', 'Your Organization')
            footer_module.update_content('department', 'Department Name')
            footer_module.update_content('revision_date', 'MM.DD.YYYY')
            footer_module.update_content('background_image', 'assets/mountains.png')  # Add this line
            footer_module.update_content('show_copyright', True)

            self.active_modules.append(footer_module)
            self.canvas_panel.add_module_widget(footer_module)

            # Update positions for all modules
            self._update_module_positions()

            # Mark as not modified since this is the base template
            self.set_modified(False)

            # Update status to show enhanced functionality
            self.main_window.set_status("Ready - Drag modules from left panel to canvas", "green")

            # Trigger preview update for the initial template
            self.preview_manager.request_preview_update()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to create base template: {str(e)}")

    def _populate_module_library(self):
        """Populate the module library panel"""
        self.main_window.populate_module_library(AVAILABLE_MODULES)

    def add_module_to_canvas(self, module_type: str):
        """Add a new module instance to the SOP or to a selected tab (enhanced for drag and drop)"""
        try:
            # Create module instance
            module = ModuleFactory.create_module(module_type)

            # Check if we should add to a tab or to the main canvas
            if self.selected_tab_context:
                tab_module, tab_name = self.selected_tab_context
                # Add to the selected tab
                if tab_module.add_module_to_tab(tab_name, module):
                    # Update canvas to show the module in the tab
                    self.canvas_panel.add_module_to_tab_widget(tab_module, tab_name, module)
                    # Select the new module
                    self.select_module(module, parent_tab=(tab_module, tab_name))

                    # Update status with success message
                    self.main_window.set_status(f"Added {module.display_name} to '{tab_name}' tab", "green")
                else:
                    messagebox.showerror("Error", f"Failed to add module to tab '{tab_name}'")
                    return
            else:
                # Add to main canvas (existing behavior)
                module.position = len(self.active_modules)
                self.active_modules.append(module)
                self.canvas_panel.add_module_widget(module)
                self.select_module(module)

                # Update status with success message
                self.main_window.set_status(f"Added {module.display_name} to main canvas", "green")

            # Mark as modified and trigger preview update
            self.set_modified(True)
            self.preview_manager.request_preview_update()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to add module: {str(e)}")
            self.main_window.set_status("Failed to add module", "red")

    def select_module(self, module: Module, parent_tab: Optional[Tuple[TabModule, str]] = None):
        """Select a module and show its properties"""
        self.selected_module = module

        # Update context based on selection
        if isinstance(module, TabModule):
            # When selecting a TabModule, clear tab context
            self.selected_tab_context = None
        elif parent_tab:
            # When selecting a module within a tab, maintain that context
            self.selected_tab_context = parent_tab

        self.properties_panel.show_module_properties(module, parent_tab)
        self.canvas_panel.highlight_module(module)

    def select_tab(self, tab_module: TabModule, tab_name: str):
        """Select a specific tab within a TabModule (enhanced for drag and drop feedback)"""
        self.selected_tab_context = (tab_module, tab_name)
        self.selected_module = None
        self.properties_panel.show_tab_properties(tab_module, tab_name)
        self.canvas_panel.highlight_tab(tab_module, tab_name)

        # Provide visual feedback that this tab is the active target
        self.main_window.set_status(f"Selected '{tab_name}' tab - drag modules here to add them", "lightblue")

    def remove_module(self, module_id: str):
        """Remove a module from the SOP (from main canvas or from a tab)"""
        removed_something = False
        removed_display_name = ""

        # First check if it's in a tab
        for module_iter in self.active_modules:
            if isinstance(module_iter, TabModule):
                tab_name = module_iter.find_module_tab(module_id)
                if tab_name:
                    # Remove from tab
                    removed_module = module_iter.remove_module_from_tab(tab_name, module_id)
                    if removed_module:
                        removed_display_name = removed_module.display_name
                        self.canvas_panel.remove_module_from_tab_widget(module_iter, tab_name, module_id)
                        # Clear selection if this was selected
                        if self.selected_module and self.selected_module.id == module_id:
                            self.selected_module = None
                            self.properties_panel.clear()
                        removed_something = True
                        break

        # If not in a tab, check main canvas
        if not removed_something:
            module_to_remove = None
            for module_iter_main in self.active_modules:
                if module_iter_main.id == module_id:
                    module_to_remove = module_iter_main
                    break

            if module_to_remove:
                removed_display_name = module_to_remove.display_name
                self.active_modules.remove(module_to_remove)
                self.canvas_panel.remove_module_widget(module_id)

                # Clear selection if this module was selected
                if self.selected_module == module_to_remove:
                    self.selected_module = None
                    self.selected_tab_context = None
                    self.properties_panel.clear()

                # Update positions
                self._update_module_positions()
                removed_something = True

        if removed_something:
            self.set_modified(True)
            self.preview_manager.request_preview_update()  # Trigger preview update
            self.main_window.set_status(f"Removed {removed_display_name}", "orange")

    def move_module_to_tab(self, module: Module, target_tab: TabModule, tab_name: str):
        """Move a module from main canvas to a tab (enhanced with better feedback)"""
        # Remove from main canvas
        if module in self.active_modules:
            self.active_modules.remove(module)
            self.canvas_panel.remove_module_widget(module.id)

            # Add to tab
            if target_tab.add_module_to_tab(tab_name, module):
                self.canvas_panel.add_module_to_tab_widget(target_tab, tab_name, module)
                self._update_module_positions()
                self.set_modified(True)
                self.preview_manager.request_preview_update()  # Trigger preview update
                self.main_window.set_status(f"Moved {module.display_name} to '{tab_name}' tab", "green")
                return True
        return False

    def move_module_from_tab(self, module: Module, source_tab: TabModule, tab_name: str):
        """Move a module from a tab to the main canvas (enhanced with better feedback)"""
        removed_module = source_tab.remove_module_from_tab(tab_name, module.id)
        if removed_module:
            self.canvas_panel.remove_module_from_tab_widget(source_tab, tab_name, module.id)

            # Add to main canvas
            removed_module.position = len(self.active_modules)
            self.active_modules.append(removed_module)
            self.canvas_panel.add_module_widget(removed_module)

            self._update_module_positions()
            self.set_modified(True)
            self.preview_manager.request_preview_update()  # Trigger preview update
            self.main_window.set_status(f"Moved {module.display_name} to main canvas", "green")
            return True
        return False

    def get_all_modules_flat(self) -> List[Module]:
        """Get all modules including nested ones in a flat list"""
        all_modules = []
        for module in self.active_modules:
            all_modules.append(module)
            if isinstance(module, TabModule):
                all_modules.extend(module.get_all_nested_modules())
        return all_modules

    def find_module_by_id(self, module_id: str) -> Optional[Tuple[Module, Optional[Tuple[TabModule, str]]]]:
        """Find a module by ID and return it with its parent context if in a tab"""
        # Check main canvas
        for module_iter in self.active_modules:
            if module_iter.id == module_id:
                return (module_iter, None)

            # Check within tabs
            if isinstance(module_iter, TabModule):
                tab_name = module_iter.find_module_tab(module_id)
                if tab_name:
                    # Find the actual module in the tab
                    if tab_name in module_iter.sub_modules:
                        for sub_module in module_iter.sub_modules[tab_name]:
                            if sub_module.id == module_id:
                                return (sub_module, (module_iter, tab_name))
        return None

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
            self.preview_manager.request_preview_update()  # Trigger preview update

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
        self.selected_tab_context = None

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
        self.selected_tab_context = None
        self.set_modified(False)

        # Update title
        self.root.title("SOP Builder - Blank Project")

        # Update status for blank project
        self.main_window.set_status("Blank project - Drag modules from left panel to start building", "blue")

        # Trigger preview update for blank project
        self.preview_manager.request_preview_update()

    def open_project(self, filename_str=None):
        """Open an existing project with tab hierarchy"""
        if not filename_str:
            filename_str = filedialog.askopenfilename(
                title="Open SOP Project",
                filetypes=[("SOP Project", "*.sopx"), ("All Files", "*.*")]
            )

        if filename_str:
            try:
                # Load project
                project_data = self.project_manager.load_project(filename_str)

                # Clear current
                self.active_modules.clear()
                self.canvas_panel.clear()
                self.selected_tab_context = None

                # Load modules with hierarchy
                for module_data in project_data['modules']:
                    module = self.project_manager.deserialize_module(module_data)
                    self.active_modules.append(module)
                    self.canvas_panel.add_module_widget(module, with_nested=True)

                self.current_project_path = Path(filename_str)
                self.set_modified(False)
                self.root.title(f"SOP Builder - {self.current_project_path.name}")
                self.main_window.set_status(f"Opened {self.current_project_path.name}", "green")

                # Trigger preview update for opened project
                self.preview_manager.request_preview_update()

            except Exception as e:
                messagebox.showerror("Error", f"Failed to open project: {str(e)}")
                self.main_window.set_status("Failed to open project", "red")

    def save_project(self, save_as=False):
        """Save current project with tab hierarchy"""
        if not self.current_project_path or save_as:
            filename_str = filedialog.asksaveasfilename(
                title="Save SOP Project",
                defaultextension=".sopx",
                filetypes=[("SOP Project", "*.sopx"), ("All Files", "*.*")]
            )
            if filename_str:
                self.current_project_path = Path(filename_str)
            else:
                return

        if not self.current_project_path:
            return

        try:
            # Save project with hierarchy
            project_data = {
                'version': '1.1',
                'modules': [self.project_manager.serialize_module(m) for m in self.active_modules]
            }

            self.project_manager.save_project(self.current_project_path, project_data)
            self.set_modified(False)
            self.root.title(f"SOP Builder - {self.current_project_path.name}")
            self.main_window.set_status(f"Saved {self.current_project_path.name}", "green")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save project: {str(e)}")
            self.main_window.set_status("Failed to save project", "red")

    def export_to_html(self):
        """Export current SOP to HTML file with enhanced media embedding"""
        if not self.active_modules:
            messagebox.showwarning("No Content", "Please add some modules before exporting.")
            return

        # Create enhanced export dialog with modules for media discovery
        export_dialog = ExportDialog(self.root, self.html_generator.get_available_themes(), self.active_modules)
        self.root.wait_window(export_dialog.dialog)

        if not export_dialog.result:
            return  # User cancelled

        filename = export_dialog.filename
        embed_css = export_dialog.embed_css
        embed_media = export_dialog.embed_media
        embed_css_assets = export_dialog.embed_css_assets  # NEW - Get the CSS assets option
        selected_theme = export_dialog.selected_theme

        if filename:
            try:
                # Set the theme
                self.html_generator.set_theme(selected_theme)

                # Get output directory
                output_path = Path(filename)
                output_dir = output_path.parent

                # Create progress dialog for media embedding if enabled
                progress_dialog = None
                progress_callback = None

                if embed_media:
                    # Create a simple progress tracking function
                    def create_progress_callback():
                        progress_info = {'current': 0, 'total': 0, 'dialog': None}

                        def progress_callback(current, total, current_file):
                            # Update progress info
                            progress_info['current'] = current
                            progress_info['total'] = total

                            # Create progress dialog on first call
                            if not progress_info['dialog']:
                                progress_info['dialog'] = self._create_progress_dialog(total)

                            # Update the dialog
                            try:
                                dialog = progress_info['dialog']
                                if dialog and dialog.winfo_exists():
                                    # Update progress bar
                                    progress_percent = (current / total) * 100 if total > 0 else 0
                                    dialog.progress_bar.set(progress_percent / 100)

                                    # Update status text
                                    file_name = Path(current_file).name
                                    status_text = f"Embedding {current}/{total}: {file_name}"
                                    dialog.status_label.configure(text=status_text)

                                    # Update the dialog
                                    dialog.update()

                                    # Close dialog when complete
                                    if current >= total:
                                        dialog.after(1000, dialog.destroy)  # Close after 1 second
                            except Exception as e:
                                print(f"Progress dialog error: {e}")

                        return progress_callback

                    progress_callback = create_progress_callback()

                # Show initial status
                if embed_media:
                    self.main_window.set_status("Preparing media embedding...", "blue")
                else:
                    self.main_window.set_status("Generating HTML...", "blue")

                # Generate HTML with enhanced options - UPDATED CALL
                html_content = self.html_generator.generate_html(
                    self.active_modules,
                    title="Standard Operating Procedure",
                    output_dir=output_dir if not embed_media else None,  # No output_dir if embedding everything
                    embed_theme=embed_css,
                    embed_media=embed_media,
                    embed_css_assets=embed_css_assets,  # NEW PARAMETER
                    progress_callback=progress_callback
                )

                # Save to file
                self.main_window.set_status("Saving HTML file...", "blue")
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(html_content)

                # Generate success message with embedding info
                success_msg = f"SOP exported successfully to:\n{filename}"

                if embed_media and hasattr(export_dialog, 'size_stats'):
                    stats = export_dialog.size_stats
                    if stats['total_files'] > 0:
                        success_msg += f"\n\n✅ {stats['valid_files']} media files embedded"
                        if embed_css:
                            success_msg += "\n✅ CSS embedded"
                        if embed_css_assets:
                            success_msg += "\n✅ CSS assets embedded"
                        if embed_css and embed_css_assets and embed_media:
                            success_msg += "\n✅ Completely self-contained HTML file created"

                        # Add size information
                        if stats['total_embedded_size_mb'] > 0:
                            success_msg += f"\n📊 Final file size: ~{stats['total_embedded_size_mb']:.1f}MB"

                messagebox.showinfo("Export Successful", success_msg)
                self.main_window.set_status(f"Exported to {Path(filename).name}", "green")

            except Exception as e:
                error_msg = f"Failed to export HTML: {str(e)}"
                messagebox.showerror("Export Error", error_msg)
                self.main_window.set_status("Export failed", "red")
                print(f"Export error details: {e}")

                # Print additional error info for debugging
                import traceback
                traceback.print_exc()

    def _create_progress_dialog(self, total_files: int):
        """Create a progress dialog for media embedding"""
        try:
            # Create progress dialog
            progress_dialog = ctk.CTkToplevel(self.root)
            progress_dialog.title("Embedding Media Files")
            progress_dialog.geometry("450x150")
            progress_dialog.transient(self.root)
            progress_dialog.grab_set()

            # Center the dialog
            progress_dialog.update_idletasks()
            x = (progress_dialog.winfo_screenwidth() // 2) - (450 // 2)
            y = (progress_dialog.winfo_screenheight() // 2) - (150 // 2)
            progress_dialog.geometry(f"+{x}+{y}")

            # Main frame
            main_frame = ctk.CTkFrame(progress_dialog, fg_color="transparent")
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)

            # Title
            title_label = ctk.CTkLabel(
                main_frame,
                text="🔄 Embedding Media Files",
                font=("Arial", 16, "bold")
            )
            title_label.pack(pady=(0, 15))

            # Progress bar
            progress_bar = ctk.CTkProgressBar(main_frame, width=400, height=20)
            progress_bar.pack(pady=(0, 10))
            progress_bar.set(0)

            # Store reference to progress bar
            progress_dialog.progress_bar = progress_bar

            # Status label
            status_label = ctk.CTkLabel(
                main_frame,
                text=f"Starting embedding process for {total_files} files...",
                font=("Arial", 12)
            )
            status_label.pack(pady=(0, 10))

            # Store reference to status label
            progress_dialog.status_label = status_label

            # Info label
            info_label = ctk.CTkLabel(
                main_frame,
                text="💡 Large files may take longer to process",
                font=("Arial", 10),
                text_color="gray"
            )
            info_label.pack()

            # Make sure dialog is visible
            progress_dialog.update()

            return progress_dialog

        except Exception as e:
            print(f"Error creating progress dialog: {e}")
            return None

    def _create_export_progress_callback(self):
        """Create a progress callback for media embedding (enhanced version)"""

        # This is the existing method that can now work with the new progress dialog
        def progress_callback(current, total, current_file):
            # For now, just print progress - the new dialog method above provides better UI
            print(f"Embedding media: {current}/{total} - {Path(current_file).name}")

        return progress_callback

    def toggle_preview(self):
        """Toggle between edit and preview modes"""
        preview_mode = self.main_window.preview_toggle.get()
        self.canvas_panel.set_preview_mode(preview_mode)

        if preview_mode:
            self.main_window.set_status("Preview mode - drag and drop disabled", "orange")
        else:
            self.main_window.set_status("Edit mode - drag modules from left panel to canvas", "green")

    def set_modified(self, modified: bool):
        """Set the modified state of the project"""
        self.is_modified = modified
        title = self.root.title()

        if modified and not title.endswith("*"):
            self.root.title(title + " *")
        elif not modified and title.endswith(" *"):
            self.root.title(title[:-2])

    def update_module_property(self, module: Module, property_name: str, value: any):
        """Update a module property (enhanced with preview updates)"""
        module.update_content(property_name, value)

        # Update canvas preview
        self.canvas_panel.update_module_preview(module)

        # Update live preview if enabled
        self.preview_manager.request_preview_update()

        # Handle special tab module updates
        if isinstance(module, TabModule) and property_name == 'tabs':
            self.canvas_panel._refresh_tab_module(module)

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

        # Close live preview if active
        if hasattr(self, 'preview_manager'):
            self.preview_manager.close_preview()

        self.root.destroy()


# Keep the existing ExportDialog class unchanged
class ExportDialog:
    """Enhanced dialog for export options including media embedding"""

    def __init__(self, parent, available_themes: List[str], modules: List):
        self.result = False
        self.filename = None
        self.embed_css = False
        self.embed_media = False
        self.embed_css_assets = False  # NEW - Initialize this
        self.selected_theme = "kodiak"
        self.modules = modules

        # Import the new services
        from utils.media_discovery import MediaDiscoveryService
        from utils.base64_embedder import Base64EmbedderService

        self.media_discovery = MediaDiscoveryService()
        self.base64_embedder = Base64EmbedderService()

        # Discover media files
        self.discovered_media = self.media_discovery.discover_all_media(modules)
        self.size_stats = self.media_discovery.estimate_embedded_size()

        # Create dialog window
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Export SOP")
        self.dialog.geometry("600x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (500 // 2)
        self.dialog.geometry(f"+{x}+{y}")

        self._create_widgets(available_themes)

    def _create_widgets(self, available_themes: List[str]):
        """Create dialog widgets with enhanced options"""
        # Main frame with scrollable content
        main_frame = ctk.CTkScrollableFrame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="📄 Export Standard Operating Procedure",
            font=("Arial", 18, "bold")
        )
        title_label.pack(pady=(0, 20))

        # Theme selection section
        self._create_theme_section(main_frame, available_themes)

        # CSS options section (UPDATED)
        self._create_css_section(main_frame)

        # Media embedding section
        self._create_media_section(main_frame)

        # Export summary section
        self._create_summary_section(main_frame)

        # Buttons
        self._create_buttons(main_frame)

    def _create_theme_section(self, parent, available_themes: List[str]):
        """Create theme selection section"""
        theme_frame = ctk.CTkFrame(parent, fg_color="transparent")
        theme_frame.pack(fill="x", pady=(0, 15))

        theme_label = ctk.CTkLabel(
            theme_frame,
            text="🎨 Select Theme:",
            font=("Arial", 14, "bold")
        )
        theme_label.pack(anchor="w", pady=(0, 5))

        self.theme_var = ctk.StringVar(value="kodiak")
        theme_menu = ctk.CTkComboBox(
            theme_frame,
            values=available_themes or ["kodiak"],
            variable=self.theme_var,
            width=200,
            command=self._on_theme_change
        )
        theme_menu.pack(anchor="w")

    def _create_css_section(self, parent):
        """Create CSS options section with asset embedding (COMPLETE VERSION)"""
        css_frame = ctk.CTkFrame(parent, fg_color="transparent")
        css_frame.pack(fill="x", pady=(0, 15))

        css_label = ctk.CTkLabel(
            css_frame,
            text="🎭 CSS Options:",
            font=("Arial", 14, "bold")
        )
        css_label.pack(anchor="w", pady=(0, 5))

        # Embed CSS checkbox
        self.embed_css_var = ctk.BooleanVar(value=False)
        embed_css_check = ctk.CTkCheckBox(
            css_frame,
            text="Embed CSS in HTML file (for standalone use)",
            variable=self.embed_css_var,
            command=self._update_summary
        )
        embed_css_check.pack(anchor="w", pady=2)

        # NEW: CSS assets embedding checkbox
        self.embed_css_assets_var = ctk.BooleanVar(value=False)
        embed_css_assets_check = ctk.CTkCheckBox(
            css_frame,
            text="Embed CSS assets (fonts, background images)",
            variable=self.embed_css_assets_var,
            command=self._update_summary
        )
        embed_css_assets_check.pack(anchor="w", pady=2)

        css_info = ctk.CTkLabel(
            css_frame,
            text="💡 CSS assets include fonts (Gin_Round.otf) and background images\n"
                 "   If unchecked, theme files will be copied alongside the HTML file",
            font=("Arial", 11),
            text_color="gray",
            justify="left"
        )
        css_info.pack(anchor="w", pady=(5, 0))


    def _create_media_section(self, parent):
        """Create media embedding section (NEW)"""
        media_frame = ctk.CTkFrame(parent, fg_color=("gray90", "gray20"))
        media_frame.pack(fill="x", pady=(0, 15), padx=5)

        # Media section header
        media_header = ctk.CTkFrame(media_frame, fg_color="transparent")
        media_header.pack(fill="x", padx=15, pady=(15, 10))

        media_title = ctk.CTkLabel(
            media_header,
            text="🖼️ Media Embedding:",
            font=("Arial", 14, "bold")
        )
        media_title.pack(side="left")

        # Media stats badge
        if self.size_stats['total_files'] > 0:
            stats_text = f"{self.size_stats['valid_files']}/{self.size_stats['total_files']} files"
            stats_color = "green" if self.size_stats['valid_files'] == self.size_stats['total_files'] else "orange"
        else:
            stats_text = "No media files"
            stats_color = "gray"

        stats_badge = ctk.CTkLabel(
            media_header,
            text=stats_text,
            font=("Arial", 11),
            text_color=stats_color
        )
        stats_badge.pack(side="right")

        # Media embedding checkbox
        self.embed_media_var = ctk.BooleanVar(value=False)
        embed_media_check = ctk.CTkCheckBox(
            media_frame,
            text="Embed all media files as base64 data URLs",
            variable=self.embed_media_var,
            command=self._on_media_embed_change
        )
        embed_media_check.pack(anchor="w", padx=15, pady=5)

        # Media details frame (initially hidden)
        self.media_details_frame = ctk.CTkFrame(media_frame, fg_color="transparent")

        if self.size_stats['total_files'] > 0:
            self._create_media_details()
        else:
            no_media_label = ctk.CTkLabel(
                self.media_details_frame,
                text="📝 No media files found in current SOP",
                font=("Arial", 11),
                text_color="gray"
            )
            no_media_label.pack(pady=10)

        self.media_details_frame.pack(fill="x", padx=15, pady=(0, 15))

    def _create_media_details(self):
        """Create detailed media information display"""
        # Size information
        size_info_frame = ctk.CTkFrame(self.media_details_frame, fg_color="transparent")
        size_info_frame.pack(fill="x", pady=5)

        size_text = (
            f"📊 Total: {self.size_stats['total_files']} files "
            f"({self.size_stats['total_original_size_mb']:.1f}MB)\n"
            f"🔄 Embedded size: ~{self.size_stats['total_embedded_size_mb']:.1f}MB "
            f"(+{self.size_stats['size_increase_percent']:.0f}%)"
        )

        size_label = ctk.CTkLabel(
            size_info_frame,
            text=size_text,
            font=("Arial", 11),
            justify="left"
        )
        size_label.pack(anchor="w")

        # Warnings for large files
        if self.size_stats['exceeds_warning_threshold']:
            warning_frame = ctk.CTkFrame(self.media_details_frame, fg_color="orange")
            warning_frame.pack(fill="x", pady=5)

            warning_text = "⚠️ Large file size detected. Embedded HTML may be slow to load."
            if self.size_stats['exceeds_size_limit']:
                warning_text = "🚫 Total size exceeds recommended limit. Consider reducing media files."
                warning_frame.configure(fg_color="red")

            warning_label = ctk.CTkLabel(
                warning_frame,
                text=warning_text,
                font=("Arial", 11, "bold"),
                text_color="white"
            )
            warning_label.pack(pady=8)

        # Large files list
        if self.size_stats['large_files']:
            large_files_frame = ctk.CTkFrame(self.media_details_frame, fg_color="transparent")
            large_files_frame.pack(fill="x", pady=5)

            large_files_label = ctk.CTkLabel(
                large_files_frame,
                text=f"📋 Large files ({len(self.size_stats['large_files'])}):",
                font=("Arial", 11, "bold")
            )
            large_files_label.pack(anchor="w")

            for large_file in self.size_stats['large_files'][:3]:  # Show first 3
                file_name = Path(large_file['path']).name
                file_text = f"   • {file_name} ({large_file['size_mb']:.1f}MB)"
                file_label = ctk.CTkLabel(
                    large_files_frame,
                    text=file_text,
                    font=("Arial", 10),
                    text_color="gray"
                )
                file_label.pack(anchor="w")

            if len(self.size_stats['large_files']) > 3:
                more_label = ctk.CTkLabel(
                    large_files_frame,
                    text=f"   ... and {len(self.size_stats['large_files']) - 3} more",
                    font=("Arial", 10),
                    text_color="gray"
                )
                more_label.pack(anchor="w")

        # Benefits explanation
        benefits_frame = ctk.CTkFrame(self.media_details_frame, fg_color="transparent")
        benefits_frame.pack(fill="x", pady=5)

        benefits_text = (
            "✅ Benefits: Single file sharing, no asset folders, works offline\n"
            "⚠️ Drawbacks: Larger file size, slower loading for large media"
        )

        benefits_label = ctk.CTkLabel(
            benefits_frame,
            text=benefits_text,
            font=("Arial", 10),
            text_color="gray",
            justify="left"
        )
        benefits_label.pack(anchor="w")

    def _create_summary_section(self, parent):
        """Create export summary section"""
        self.summary_frame = ctk.CTkFrame(parent, fg_color=("gray85", "gray25"))
        self.summary_frame.pack(fill="x", pady=(0, 15))

        summary_label = ctk.CTkLabel(
            self.summary_frame,
            text="📋 Export Summary:",
            font=("Arial", 14, "bold")
        )
        summary_label.pack(anchor="w", padx=15, pady=(15, 5))

        self.summary_text = ctk.CTkLabel(
            self.summary_frame,
            text="",
            font=("Arial", 11),
            justify="left",
            anchor="w"
        )
        self.summary_text.pack(anchor="w", padx=15, pady=(0, 15))

        self._update_summary()

    def _create_buttons(self, parent):
        """Create action buttons"""
        button_frame = ctk.CTkFrame(parent, fg_color="transparent")
        button_frame.pack(fill="x", pady=(20, 0))

        export_btn = ctk.CTkButton(
            button_frame,
            text="📄 Export HTML",
            command=self._export,
            width=120,
            height=35,
            font=("Arial", 12, "bold"),
            fg_color="green",
            hover_color="darkgreen"
        )
        export_btn.pack(side="right", padx=(10, 0))

        cancel_btn = ctk.CTkButton(
            button_frame,
            text="❌ Cancel",
            command=self._cancel,
            width=100,
            height=35,
            font=("Arial", 12),
            fg_color="gray",
            hover_color="darkgray"
        )
        cancel_btn.pack(side="right")

    def _on_theme_change(self, value):
        """Handle theme selection change"""
        self._update_summary()

    def _on_media_embed_change(self):
        """Handle media embedding checkbox change"""
        self._update_summary()

    def _update_summary(self):
        """Update the export summary display (UPDATED for CSS assets)"""
        summary_parts = []

        # Theme info
        theme_name = self.theme_var.get()
        summary_parts.append(f"🎨 Theme: {theme_name}")

        # CSS embedding
        if self.embed_css_var.get():
            if self.embed_css_assets_var.get():
                summary_parts.append("🎭 CSS: Embedded with assets (fonts, images)")
            else:
                summary_parts.append("🎭 CSS: Embedded in HTML (external assets)")
        else:
            summary_parts.append("🎭 CSS: External file (copied)")

        # Media embedding
        if self.embed_media_var.get() and self.size_stats['total_files'] > 0:
            summary_parts.append(
                f"🖼️ Media: {self.size_stats['valid_files']} files embedded "
                f"(~{self.size_stats['total_embedded_size_mb']:.1f}MB)"
            )
        elif self.size_stats['total_files'] > 0:
            summary_parts.append(
                f"🖼️ Media: {self.size_stats['total_files']} files copied to Assets folder"
            )
        else:
            summary_parts.append("🖼️ Media: No media files")

        # File structure
        if (self.embed_css_var.get() and self.embed_css_assets_var.get() and
                self.embed_media_var.get()):
            summary_parts.append("📁 Output: Single HTML file (completely self-contained)")
        elif (self.embed_css_var.get() or self.embed_css_assets_var.get() or
              self.embed_media_var.get()):
            summary_parts.append("📁 Output: HTML file + minimal assets")
        else:
            summary_parts.append("📁 Output: HTML file + Assets folder")

        summary_text = "\n".join(summary_parts)
        self.summary_text.configure(text=summary_text)

    def _export(self):
        """Handle export button click (UPDATED)"""
        # Check for size warnings if media embedding is enabled
        if (self.embed_media_var.get() and
                self.size_stats['total_files'] > 0 and
                self.size_stats['exceeds_warning_threshold']):

            size_mb = self.size_stats['total_embedded_size_mb']
            warning_msg = (
                f"The embedded file will be approximately {size_mb:.1f}MB.\n\n"
                "Large embedded files may:\n"
                "• Take longer to load in web browsers\n"
                "• Use more memory\n"
                "• Be difficult to share via email\n\n"
                "Do you want to continue?"
            )

            if self.size_stats['exceeds_size_limit']:
                warning_msg = (
                    f"WARNING: The embedded file will be {size_mb:.1f}MB!\n\n"
                    "This exceeds recommended limits and may:\n"
                    "• Fail to load in some browsers\n"
                    "• Cause performance issues\n"
                    "• Be rejected by email systems\n\n"
                    "Consider unchecking media embedding or reducing file sizes.\n\n"
                    "Continue anyway?"
                )

            result = messagebox.askyesno("Large File Warning", warning_msg)
            if not result:
                return

        # Get export filename
        self.filename = filedialog.asksaveasfilename(
            title="Export SOP as HTML",
            defaultextension=".html",
            filetypes=[("HTML Files", "*.html"), ("All Files", "*.*")]
        )

        if self.filename:
            self.embed_css = self.embed_css_var.get()
            self.embed_media = self.embed_media_var.get()
            self.embed_css_assets = self.embed_css_assets_var.get()  # NOW PROPERLY DEFINED
            self.selected_theme = self.theme_var.get()
            self.result = True
            self.dialog.destroy()

    def _cancel(self):
        """Handle cancel button click"""
        self.result = False
        self.dialog.destroy()
