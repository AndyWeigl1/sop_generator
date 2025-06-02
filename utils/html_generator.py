# utils/html_generator.py - Phase 3: Enhanced with Media Embedding - FIXED
from typing import List, Dict, Optional, Set, Tuple, Any, Callable
from modules.base_module import Module
from modules.complex_module import TabModule
from pathlib import Path
import shutil
import os
import base64
import mimetypes
import copy
import re

# Import Phase 1 and Phase 2 services
from utils.media_discovery import MediaDiscoveryService
from utils.base64_embedder import Base64EmbedderService
from utils.module_content_updater import ModuleContentUpdater


class HTMLGenerator:
    """Generate HTML from arranged modules with theme support and media embedding"""

    def __init__(self):
        self.theme_name = "kodiak"
        self.themes_dir = Path("assets/themes")
        self.base_template = self._load_base_template()

        # Initialize Phase 1 and Phase 2 services
        self.media_discovery = MediaDiscoveryService()
        self.base64_embedder = Base64EmbedderService()
        self.module_updater = ModuleContentUpdater()

    def _load_base_template(self) -> str:
        """Load the base HTML template with external CSS support"""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="{theme_css}">
    {custom_styles}
</head>
<body>
    <div class="container">
        {content}
    </div>
    {scripts}
</body>
</html>'''

    def set_theme(self, theme_name: str):
        """Set the active theme"""
        theme_path = self.themes_dir / f"{theme_name}.css"
        if theme_path.exists():
            self.theme_name = theme_name
        else:
            raise ValueError(f"Theme '{theme_name}' not found in {self.themes_dir}")

    def _copy_media_files(self, modules: List[Module], output_dir: Path):
        """Copy media files referenced in modules to output directory (traditional method)"""
        assets_dir = output_dir / "Assets"
        assets_dir.mkdir(exist_ok=True)

        copied_files = []

        def process_module(module):
            # Get media references using the new Phase 2 method
            if hasattr(module, 'get_media_references'):
                media_refs = module.get_media_references()
                path_mapping = {}

                for media_path in media_refs:
                    if media_path and os.path.exists(media_path):
                        # Copy file to Assets directory
                        filename = os.path.basename(media_path)
                        dest_path = assets_dir / filename

                        try:
                            shutil.copy2(media_path, dest_path)
                            copied_files.append(filename)
                            # Map original path to new relative path
                            path_mapping[media_path] = f"Assets/{filename}"
                        except Exception as e:
                            print(f"Warning: Could not copy media file {media_path}: {e}")

                # Update the module's media references
                if path_mapping and hasattr(module, 'update_media_references'):
                    module.update_media_references(path_mapping)

        for module in modules:
            process_module(module)

        if copied_files:
            print(f"Copied {len(copied_files)} media files to Assets folder: {copied_files}")

    # Update the main generate_html method signature
    def generate_html(self, modules: List[Module], title: str = "Standard Operating Procedure",
                      output_dir: Optional[Path] = None, embed_theme: bool = False,
                      embed_media: bool = False,
                      embed_css_assets: bool = False,  # NEW PARAMETER
                      progress_callback: Optional[Callable[[int, int, str], None]] = None) -> str:
        """
        Generate complete HTML from modules with enhanced embedding options

        Args:
            modules: List of modules to render
            title: HTML document title
            output_dir: Output directory for assets (if not embedding)
            embed_theme: Whether to embed CSS in HTML
            embed_media: Whether to embed media as base64 data URLs
            embed_css_assets: Whether to embed CSS assets (fonts, images) as base64  # NEW
            progress_callback: Optional callback for progress updates (current, total, filename)

        Returns:
            Complete HTML string
        """

        # Step 1: Create working copies of modules to avoid modifying originals
        working_modules = self.module_updater.create_modules_copy_for_export(modules)

        try:
            # Step 2: Handle media embedding or copying
            if embed_media:
                print("🔄 Starting media embedding process...")
                working_modules = self._embed_all_media(working_modules, progress_callback)
            elif output_dir:
                # Traditional file copying
                print("📁 Copying media files to Assets folder...")
                self._copy_media_files(working_modules, output_dir)

            # Step 3: Generate HTML content from processed modules
            html_content = self._generate_html_content(
                working_modules, title, output_dir, embed_theme, embed_css_assets  # PASS THE NEW PARAMETER
            )

            print("✅ HTML generation completed successfully")
            return html_content

        except Exception as e:
            print(f"❌ Error during HTML generation: {e}")
            # In case of error, try to restore original state
            self.module_updater.clear_backup()
            raise
        finally:
            # Clean up working copies
            self.module_updater.clear_backup()

    def _embed_all_media(self, modules: List[Module],
                         progress_callback: Optional[Callable[[int, int, str], None]] = None) -> List[Module]:
        """
        Process all modules and embed their media as base64 data URLs

        Args:
            modules: List of modules to process
            progress_callback: Optional progress callback

        Returns:
            Updated modules with embedded media
        """

        # Step 1: Validate embedding feasibility
        can_embed, reason = self._validate_embedding_feasibility(modules)
        if not can_embed:
            raise ValueError(f"Media embedding not feasible: {reason}")

        # Step 2: Discover all media files
        print("🔍 Discovering media files...")
        discovered_media = self.media_discovery.discover_all_media(modules)

        if not discovered_media:
            print("ℹ️ No media files found to embed")
            return modules

        # Step 3: Filter to embeddable files only
        embeddable_files = self.media_discovery.get_embeddable_files()
        problematic_files = self.media_discovery.get_problematic_files()

        if problematic_files:
            print(f"⚠️ Found {len(problematic_files)} problematic files that will be skipped:")
            for path, info in problematic_files.items():
                print(f"   - {Path(path).name}: {info.error_message}")

        if not embeddable_files:
            print("⚠️ No valid files found for embedding")
            return modules

        # Step 4: Convert files to base64
        print(f"🔄 Converting {len(embeddable_files)} files to base64...")
        file_paths = list(embeddable_files.keys())

        # Create progress wrapper if callback provided
        def embedding_progress(current, total, current_file):
            if progress_callback:
                progress_callback(current, total, current_file)
            print(f"   📄 ({current}/{total}) {Path(current_file).name}")

        # Perform batch conversion
        conversion_results = self.base64_embedder.embed_multiple_files(
            file_paths,
            progress_callback=embedding_progress
        )

        # Step 5: Filter successful conversions
        successful_conversions = {
            path: data_url for path, data_url in conversion_results.items()
            if data_url  # Only include successful conversions (non-empty)
        }

        failed_conversions = {
            path: data_url for path, data_url in conversion_results.items()
            if not data_url  # Failed conversions have empty strings
        }

        if failed_conversions:
            print(f"⚠️ Failed to convert {len(failed_conversions)} files:")
            for path in failed_conversions.keys():
                print(f"   - {Path(path).name}")

        if not successful_conversions:
            print("❌ No files were successfully converted to base64")
            return modules

        print(f"✅ Successfully converted {len(successful_conversions)} files to base64")

        # Step 6: Update module references
        print("🔄 Updating module media references...")
        updated_modules = self.module_updater.update_all_media_references(
            modules, successful_conversions
        )

        # Step 7: Validate updates
        validation_result = self.module_updater.validate_media_updates(
            updated_modules, successful_conversions
        )

        print(f"📊 Media reference update summary:")
        print(f"   - Total references: {validation_result['total_references']}")
        print(f"   - Successfully updated: {len(validation_result['found'])}")
        print(f"   - Not found in mapping: {len(validation_result['missing'])}")

        if validation_result['missing']:
            print("⚠️ Some media references were not updated:")
            for missing_path in validation_result['missing']:
                print(f"   - {Path(missing_path).name}")

        return updated_modules

    def _validate_embedding_feasibility(self, modules: List[Module]) -> Tuple[bool, str]:
        """
        Check if media embedding is practical for the given modules

        Args:
            modules: List of modules to validate

        Returns:
            Tuple of (can_embed, reason)
        """
        try:
            # Discover media and get size estimates
            discovered_media = self.media_discovery.discover_all_media(modules)
            size_stats = self.media_discovery.estimate_embedded_size(discovered_media)

            # Check if no media files
            if size_stats['total_files'] == 0:
                return True, "No media files to embed"

            # Check if no valid files
            if size_stats['valid_files'] == 0:
                return False, "No valid media files found for embedding"

            # Check total size limits
            if size_stats['exceeds_size_limit']:
                size_mb = size_stats['total_embedded_size_mb']
                return False, f"Total embedded size ({size_mb:.1f}MB) exceeds safe limits"

            # All checks passed
            return True, f"Ready to embed {size_stats['valid_files']} files ({size_stats['total_embedded_size_mb']:.1f}MB)"

        except Exception as e:
            return False, f"Error validating embedding feasibility: {str(e)}"

    # Update the _generate_html_content method
    def _generate_html_content(self, modules: List[Module], title: str,
                               output_dir: Optional[Path], embed_theme: bool,
                               embed_css_assets: bool = False) -> str:  # ADD THE NEW PARAMETER
        """
        Generate the HTML content from processed modules

        Args:
            modules: Processed modules (with embedded or copied media)
            title: HTML document title
            output_dir: Output directory (may be None if embedding everything)
            embed_theme: Whether to embed CSS
            embed_css_assets: Whether to embed CSS assets as base64

        Returns:
            Complete HTML string
        """
        # Sort top-level modules by position
        sorted_modules = sorted(modules, key=lambda m: m.position)

        # Track which modules have been rendered to avoid duplicates
        rendered_module_ids: Set[str] = set()

        # Separate modules by type for proper structure
        header_modules = []
        tab_modules = []
        footer_modules = []
        other_modules = []

        for module in sorted_modules:
            if module.module_type == 'header':
                header_modules.append(module)
            elif module.module_type == 'tabs':
                tab_modules.append(module)
            elif module.module_type == 'footer':
                footer_modules.append(module)
            else:
                other_modules.append(module)

        # Generate HTML sections
        content_html = ""

        # Add header modules (outside content-wrapper)
        for module in header_modules:
            content_html += f'\n {module.render_to_html()}'
            rendered_module_ids.add(module.id)

        # Check if we have tabs
        has_tabs = len(tab_modules) > 0

        if has_tabs:
            # If we have tabs, ALL non-header/footer content goes inside content-wrapper
            content_html += '\n\n <div class="content-wrapper">'

            # For each tab module, render with proper card structure
            for tab_module in tab_modules:
                if isinstance(tab_module, TabModule):
                    # Generate the complete tab structure with cards
                    content_html += f'\n {self._render_tab_module_with_cards(tab_module)}'
                    rendered_module_ids.add(tab_module.id)

                    # Mark all nested modules as rendered
                    for nested_module in tab_module.get_all_nested_modules():
                        rendered_module_ids.add(nested_module.id)

            # Close content-wrapper
            content_html += '\n </div>'
        else:
            # No tabs - render other modules directly with card structure
            if other_modules:
                content_html += '\n\n<div class="steps-container">'
                step_number = 1
                for module in other_modules:
                    if module.id not in rendered_module_ids:
                        content_html += f'\n {self._wrap_module_in_card(module, step_number)}'
                        rendered_module_ids.add(module.id)
                        step_number += 1
                content_html += '\n</div>'

        # Add footer modules (outside content-wrapper)
        for module in footer_modules:
            if module.id not in rendered_module_ids:
                content_html += f'\n {module.render_to_html()}'
                rendered_module_ids.add(module.id)

        # Handle theme CSS
        if embed_theme:
            # Read and embed the CSS file content with assets
            theme_css_content = self._load_theme_css(embed_assets=embed_css_assets)  # PASS THE PARAMETER
            theme_css_ref = ""
            custom_styles = f"<style>\n{theme_css_content}\n</style>"
        else:
            # Link to external CSS file
            if output_dir:
                # Copy theme CSS to output directory
                self._copy_theme_to_output(output_dir)
                theme_css_ref = f"{self.theme_name}.css"
            else:
                # Use relative path to themes directory
                theme_css_ref = f"assets/themes/{self.theme_name}.css"
            custom_styles = ""

        # Generate JavaScript
        scripts = self._generate_scripts()

        # Add back-to-top button to content
        content_html += '\n\n<!-- Back to Top Button -->\n<a href="#" class="back-to-top" id="backToTop"></a>'

        # Combine everything
        html = self.base_template.format(
            title=title,
            theme_css=theme_css_ref,
            custom_styles=custom_styles,
            content=content_html,
            scripts=scripts
        )

        return html

    def _load_theme_css(self, embed_assets: bool = False) -> str:
        """Load CSS content from theme file and optionally embed assets"""
        theme_path = self.themes_dir / f"{self.theme_name}.css"

        if not theme_path.exists():
            return self._generate_default_styles()

        with open(theme_path, 'r', encoding='utf-8') as f:
            css_content = f.read()

        # If embedding assets, process CSS for asset references
        if embed_assets:
            from utils.css_asset_embedder import CSSAssetEmbedder
            css_embedder = CSSAssetEmbedder()

            print(f"🎨 Processing CSS assets for {self.theme_name} theme...")
            css_content = css_embedder.embed_css_assets(css_content, theme_path)

        return css_content

    def _render_tab_module_with_cards(self, tab_module: 'TabModule') -> str:
        """Generate HTML for TabModule with proper card structure"""
        # Ensure sub_modules exist for all tabs
        for tab in tab_module.content_data['tabs']:
            if tab not in tab_module.sub_modules:
                tab_module.sub_modules[tab] = []

        # Generate tab buttons
        tab_buttons = ''
        for i, tab in enumerate(tab_module.content_data['tabs']):
            active_class = 'active' if i == tab_module.content_data['active_tab'] else ''
            tab_buttons += f'<button class="tab {active_class}">{tab}</button>\n'

        # Start building the HTML
        html = f'''
    <div class="tabs">
        {tab_buttons}
    </div>'''

        # Generate ALL section-content divs for ALL tabs with card structure
        for i, tab in enumerate(tab_module.content_data['tabs']):
            active_class = 'active' if i == tab_module.content_data['active_tab'] else ''

            # Get modules for this tab and organize them
            tab_modules = []
            if tab in tab_module.sub_modules:
                tab_modules = sorted(tab_module.sub_modules[tab], key=lambda m: m.position)

            # Group modules by sections (disclaimer + section_title + following modules)
            sections = self._group_modules_by_sections(tab_modules)

            # Generate content for this tab
            content = ''
            for section in sections:
                content += self._render_section_with_cards(section)

            # If no content, show placeholder
            if not content:
                content = '<p style="color: gray; text-align: center;">No content in this tab yet.</p>'

            # Add the section-content div
            html += f'''
    <div class="section-content {active_class}">
        {content}
    </div>'''

        return html

    def _render_section_with_cards(self, section_modules: List[Module]) -> str:
        """Render a section with proper card structure"""
        if not section_modules:
            return ''

        html = ''
        step_number = 1
        steps_container_open = False

        for module in section_modules:
            if module.module_type == 'disclaimer':
                # Disclaimers go outside steps-container
                if steps_container_open:
                    html += '\n</div>'  # Close steps-container
                    steps_container_open = False
                html += f'\n{module.render_to_html()}'

            elif module.module_type == 'section_title':
                # Section titles go outside steps-container
                if steps_container_open:
                    html += '\n</div>'  # Close steps-container
                    steps_container_open = False
                html += f'\n{module.render_to_html()}'

            else:
                # Other modules go inside steps-container as cards
                if not steps_container_open:
                    html += '\n<div class="steps-container">'
                    steps_container_open = True
                    step_number = 1  # Reset step numbering for each new container

                html += f'\n{self._wrap_module_in_card(module, step_number)}'
                step_number += 1

        # Close steps-container if it's open
        if steps_container_open:
            html += '\n</div>'

        return html

    def _wrap_module_in_card(self, module: Module, step_number: int) -> str:
        """Wrap a module's content in a step card"""
        module_content = module.render_to_html()

        # For other modules, wrap them in a card
        return f'''
    <div class="step-card">
        <div class="step-number">{step_number}</div>
        {module_content}
    </div>'''

    def _group_modules_by_sections(self, modules: List[Module]) -> List[List[Module]]:
        """Group modules into sections based on section_title modules"""
        if not modules:
            return []

        sections = []
        current_section = []

        for module in modules:
            if module.module_type == 'section_title' and current_section:
                # Start a new section, but first close the current one
                sections.append(current_section)
                current_section = [module]
            else:
                current_section.append(module)

        # Add the last section
        if current_section:
            sections.append(current_section)

        return sections

    def _copy_theme_to_output(self, output_dir: Path):
        """Copy theme CSS file to output directory"""
        theme_source = self.themes_dir / f"{self.theme_name}.css"
        theme_dest = output_dir / f"{self.theme_name}.css"

        if theme_source.exists():
            # Create output directory if it doesn't exist
            output_dir.mkdir(parents=True, exist_ok=True)

            # Copy the CSS file
            shutil.copy2(theme_source, theme_dest)

            # Also copy any assets referenced in the CSS (like fonts, images)
            self._copy_theme_assets(output_dir)

    def _copy_theme_assets(self, output_dir: Path):
        """Copy theme-related assets (fonts, images) to output directory"""
        assets_dir = Path("assets")
        output_assets_dir = output_dir / "Assets"

        # List of asset files referenced in Kodiak theme
        kodiak_assets = [
            "Gin_Round.otf",
            "background.jpg",
            "bear_red.png",
            "bear_paw.png",
            "Mountains.png",
            "Kodiak.png"
        ]

        # Create Assets directory in output
        output_assets_dir.mkdir(parents=True, exist_ok=True)

        # Copy each asset if it exists
        for asset in kodiak_assets:
            source = assets_dir / asset
            if source.exists():
                shutil.copy2(source, output_assets_dir / asset)

    def _generate_default_styles(self) -> str:
        """Generate default CSS styles as fallback"""
        return '''
        :root {
            --primary-color: #2c3e50;
            --secondary-color: #3498db;
            --background-color: #ecf0f1;
            --text-color: #2c3e50;
            --border-color: #bdc3c7;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            background-color: var(--background-color);
            color: var(--text-color);
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
            background-color: white;
            min-height: 100vh;
        }
        '''

    def _generate_scripts(self) -> str:
        """Generate JavaScript for interactive elements including tab functionality"""
        return '''
    <script>
    // Tab functionality
    document.addEventListener('DOMContentLoaded', function() {
        const tabs = document.querySelectorAll('.tab');
        const sections = document.querySelectorAll('.section-content');
    
        tabs.forEach((tab, index) => {
            tab.addEventListener('click', () => {
                // Remove active class from all tabs and sections
                tabs.forEach(t => t.classList.remove('active'));
                sections.forEach(s => s.classList.remove('active'));
    
                // Add active class to clicked tab and corresponding section
                tab.classList.add('active');
                sections[index].classList.add('active');
            });
        });
    });
    
    // Image modal functionality - FIXED VERSION (matches working Lineage implementation)
    document.addEventListener('DOMContentLoaded', function() {
        // Create modal if it doesn't exist
        if (!document.getElementById('imageModal')) {
            const modal = document.createElement('div');
            modal.id = 'imageModal';
            modal.className = 'modal';
            modal.innerHTML = '<div class="modal-content"><img id="modalImage" src="" alt="Enlarged image"></div>';
            document.body.appendChild(modal);
        }
    
        const modal = document.getElementById('imageModal');
        const modalImg = document.getElementById('modalImage');
    
        function closeModal() {
            modal.style.display = "none";
            document.body.style.overflow = 'auto';
        }
    
        // Close on any click within modal
        modal.addEventListener('click', closeModal);
    
        // Make functions globally available
        window.openImageModal = function(img) {
            modal.style.display = "block";
            modalImg.src = img.src;
            document.body.style.overflow = 'hidden';
        };
    });
    
    // Back to top functionality
    window.onscroll = function() {
        const backToTopButton = document.getElementById('backToTop');
        if (backToTopButton) {
            if (document.body.scrollTop > 500 || document.documentElement.scrollTop > 500) {
                backToTopButton.classList.add('visible');
            } else {
                backToTopButton.classList.remove('visible');
            }
        }
    };
    
    // Smooth scroll for Back to Top button
    document.addEventListener('DOMContentLoaded', function() {
        const backToTopButton = document.getElementById('backToTop');
        if (backToTopButton) {
            backToTopButton.addEventListener('click', function(e) {
                e.preventDefault();
                window.scrollTo({
                    top: 0,
                    behavior: 'smooth'
                });
            });
        }
    })
    
    // Escape key to close modal
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' || e.key === 'Esc') {
            const modal = document.getElementById('imageModal');
            if (modal && modal.style.display === 'block') {
                modal.style.display = 'none';
                document.body.style.overflow = 'auto';
            }
        }
    });
    </script>
    '''

    def get_available_themes(self) -> List[str]:
        """Get list of available themes"""
        if not self.themes_dir.exists():
            return []

        return [f.stem for f in self.themes_dir.glob("*.css")]

    # Legacy method for backward compatibility (now unused with new embedding)
    def embed_asset(self, file_path: str) -> str:
        """Convert file to base64 data URL (legacy method, use Base64EmbedderService instead)"""
        try:
            path = Path(file_path)
            if not path.exists():
                return file_path

            mime_types = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.svg': 'image/svg+xml',
                '.mp4': 'video/mp4',
                '.webm': 'video/webm'
            }

            mime_type = mime_types.get(path.suffix.lower(), 'application/octet-stream')

            with open(path, 'rb') as f:
                data = base64.b64encode(f.read()).decode('utf-8')

            return f"data:{mime_type};base64,{data}"

        except Exception as e:
            print(f"Error embedding asset {file_path}: {e}")
            return file_path
