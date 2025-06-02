# utils/html_generator.py
from typing import List, Dict, Optional, Set, Tuple, Any
from modules.base_module import Module
from modules.complex_module import TabModule
from pathlib import Path
import shutil
import os
import base64
import mimetypes
import copy
import re


class HTMLGenerator:
    """Generate HTML from arranged modules with theme support"""

    def __init__(self):
        self.theme_name = "kodiak"
        self.themes_dir = Path("assets/themes")
        self.base_template = self._load_base_template()

        # Media field mapping for different module types
        self.MEDIA_FIELD_MAPPING = {
            'media': ['source'],
            'header': ['logo_path'],
            'footer': ['background_image'],
            'media_grid': ['items'],  # Special handling for list
            'issue_card': [
                'issue_media_source',
                'solution_single_media_source',
                'solution_media_items'
            ],
        }

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
        """Copy media files referenced in modules to output directory"""
        assets_dir = output_dir / "Assets"
        assets_dir.mkdir(exist_ok=True)

        copied_files = []

        def process_module(module):
            if module.module_type == 'media':
                source = module.content_data.get('source', '')
                if source and os.path.exists(source):
                    # Copy file to Assets directory
                    filename = os.path.basename(source)
                    dest_path = assets_dir / filename

                    try:
                        shutil.copy2(source, dest_path)
                        copied_files.append(filename)
                        # Update the module's source to point to the new location
                        module.content_data['source'] = f"Assets/{filename}"
                    except Exception as e:
                        print(f"Warning: Could not copy media file {source}: {e}")

            # Handle TabModules recursively
            elif hasattr(module, 'get_all_nested_modules'):
                for nested_module in module.get_all_nested_modules():
                    process_module(nested_module)

        for module in modules:
            process_module(module)

        if copied_files:
            print(f"Copied {len(copied_files)} media files to Assets folder: {copied_files}")

    def generate_html(self, modules: List[Module], title: str = "Standard Operating Procedure",
                      output_dir: Optional[Path] = None, embed_theme: bool = False,
                      embed_media: bool = False,  # NEW
                      progress_callback=None) -> str:  # NEW
        """
        Generate complete HTML from modules with enhanced embedding options
        """
        # For Phase 1, just pass through - media embedding will be implemented in Phase 3
        if embed_media:
            print(f"Media embedding requested for {len(modules)} modules")
            # TODO: Implement in Phase 3

        # Copy media files before generating HTML
        if output_dir:
            self._copy_media_files(modules, output_dir)

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
            # Read and embed the CSS file content
            theme_css_content = self._load_theme_css()
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

        # Combine everything
        html = self.base_template.format(
            title=title,
            theme_css=theme_css_ref,
            custom_styles=custom_styles,
            content=content_html,
            scripts=scripts
        )

        return html

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

        # For modules that already have card styling (like step_card), use them as-is
        if module.module_type == 'step_card':
            return module_content

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

    def _load_theme_css(self) -> str:
        """Load CSS content from theme file"""
        theme_path = self.themes_dir / f"{self.theme_name}.css"
        if theme_path.exists():
            with open(theme_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            # Fallback to default styles if theme not found
            return self._generate_default_styles()

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

// Image modal functionality
function openImageModal(img) {
    const modal = document.getElementById('imageModal') || createModal();
    const modalImg = modal.querySelector('img');
    modal.style.display = "block";
    modalImg.src = img.src;
    document.body.style.overflow = 'hidden'; // Prevent background scrolling
}

function createModal() {
    const modal = document.createElement('div');
    modal.id = 'imageModal';
    modal.className = 'modal';
    modal.innerHTML = '<div class="modal-content"><img src="" alt="Enlarged image"></div>';

    modal.onclick = function(event) {
        if (event.target === modal) {
            modal.style.display = "none";
            document.body.style.overflow = 'auto';
        }
    };

    document.body.appendChild(modal);
    return modal;
}

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

    def embed_asset(self, file_path: str) -> str:
        """Convert file to base64 data URL"""
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


    def get_available_themes(self) -> List[str]:
        """Get list of available themes"""
        if not self.themes_dir.exists():
            return []

        return [f.stem for f in self.themes_dir.glob("*.css")]
