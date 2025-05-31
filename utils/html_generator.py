# utils/html_generator.py
from typing import List, Dict, Optional, Set
from modules.base_module import Module
from modules.complex_modules import TabModule
import base64
from pathlib import Path
import shutil


class HTMLGenerator:
    """Generate HTML from arranged modules with theme support"""

    def __init__(self):
        self.theme_name = "kodiak"  # Default theme
        self.themes_dir = Path("assets/themes")
        self.base_template = self._load_base_template()

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

    def generate_html(self, modules: List[Module], title: str = "Standard Operating Procedure",
                      output_dir: Optional[Path] = None, embed_theme: bool = False) -> str:
        """
        Generate complete HTML from modules with proper hierarchical rendering

        Args:
            modules: List of top-level modules only (nested modules are handled by their parents)
            title: Document title
            output_dir: Directory where HTML will be saved (for relative CSS paths)
            embed_theme: If True, embed CSS inline; if False, link to external file
        """
        # Sort top-level modules by position
        sorted_modules = sorted(modules, key=lambda m: m.position)

        # Track which modules have been rendered to avoid duplicates
        rendered_module_ids: Set[str] = set()

        # Separate modules by type for proper structure
        header_modules = []
        tab_modules = []
        content_modules = []
        footer_modules = []

        for module in sorted_modules:
            if module.module_type == 'header':
                header_modules.append(module)
            elif module.module_type == 'tabs': # Assuming TabModule has module_type 'tabs'
                tab_modules.append(module)
            elif module.module_type == 'footer':
                footer_modules.append(module)
            else:
                content_modules.append(module)

        # Generate HTML sections
        content_html = ""

        # Add header modules (outside content-wrapper)
        for module in header_modules:
            content_html += f'\n {module.render_to_html()}'
            rendered_module_ids.add(module.id)

        # Check if we have tabs - if so, create content-wrapper
        has_tabs = any(isinstance(m, TabModule) for m in tab_modules) # More robust check
        if has_tabs: # Check if tab_modules list itself is populated by TabModule instances
            content_html += '\n\n <div class="content-wrapper">'

        # Add tab modules - they will render their own nested content
        for tab_module_candidate in tab_modules:
            if isinstance(tab_module_candidate, TabModule): # Ensure it's a TabModule
                content_html += f'\n {tab_module_candidate.render_to_html()}'
                rendered_module_ids.add(tab_module_candidate.id)

                # Mark all nested modules as rendered
                for nested_module in tab_module_candidate.get_all_nested_modules(): # Assuming this method exists
                    rendered_module_ids.add(nested_module.id)
            else:
                # If it's not a TabModule but ended up in tab_modules, render it as a content module
                 content_html += f'\n {tab_module_candidate.render_to_html()}'
                 rendered_module_ids.add(tab_module_candidate.id)


        if has_tabs: # Close content-wrapper only if it was opened
            content_html += '\n </div>'

        # Add any content modules that aren't inside tabs
        # Only render modules that haven't been rendered as part of a tab
        for module in content_modules:
            if module.id not in rendered_module_ids:
                content_html += f'\n {module.render_to_html()}'
                rendered_module_ids.add(module.id)

        # Add footer modules (outside content-wrapper)
        for module in footer_modules:
            if module.id not in rendered_module_ids: # Check if already rendered (e.g. if it was miscategorized)
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
                # Use relative path to themes directory if output_dir is not specified
                # This might be problematic if the HTML is not saved relative to the project structure.
                # A more robust solution might involve absolute paths or ensuring output_dir.
                theme_css_ref = f"assets/themes/{self.theme_name}.css" # This assumes HTML is in project root
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
    // Handle all tab containers on the page
    const tabContainers = document.querySelectorAll('.tabs');

    tabContainers.forEach((tabContainer, containerIndex) => {
        const tabs = tabContainer.querySelectorAll('.tab');
        // Assuming section-content are direct children of the tabContainer's parent
        // or need a more specific selector if nested deeper.
        const parentElement = tabContainer.closest('.content-wrapper') || tabContainer.parentElement;
        const sections = Array.from(parentElement.querySelectorAll('.section-content'));

        // Filter sections that are specifically for this tab set, if necessary
        // This part can be tricky if multiple tab sets are in the same parentElement.
        // For simplicity, assuming a direct correspondence or a unique class per tab set's sections.

        tabs.forEach((tab, index) => {
            tab.addEventListener('click', () => {
                // Remove active class from all tabs in this specific container
                tabs.forEach(t => t.classList.remove('active'));

                // Remove active class from all sections related to this tab container
                // This needs to be precise. If sections are globally selected,
                // you might hide sections from other tab groups.
                // A common pattern is sections having an ID linked to the tab or a shared parent.
                sections.forEach(s => s.classList.remove('active'));

                // Add active class to clicked tab
                tab.classList.add('active');

                // Add active class to the corresponding section
                // This relies on the order of tabs matching the order of sections.
                // Or sections could have data-attributes linking them to tabs.
                if (sections[index]) { // Check if a corresponding section exists
                    sections[index].classList.add('active');
                } else {
                    // console.warn(`No section found for tab index ${index} in container ${containerIndex}`);
                }
            });
        });

        // Optionally, activate the first tab by default if none are active
        if (tabs.length > 0 && !tabContainer.querySelector('.tab.active')) {
            tabs[0].click(); // Simulate a click to activate the first tab and its content
        }
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
    modal.className = 'modal'; // Ensure CSS for .modal is defined
    // Modal content structure
    modal.innerHTML = '<div class="modal-content"><span class="close-button">&times;</span><img src="" alt="Enlarged image"></div>';

    // Close modal on click outside image (on modal background) or on close button
    const closeButton = modal.querySelector('.close-button');
    closeButton.onclick = function() {
        modal.style.display = "none";
        document.body.style.overflow = 'auto';
    };
    modal.onclick = function(event) {
        // Close only if the click is on the modal background itself, not on its children (like the image)
        if (event.target === modal) {
            modal.style.display = "none";
            document.body.style.overflow = 'auto';
        }
    };
    document.body.appendChild(modal);
    return modal;
}

// Add click handlers to images that should be modal
// Consider a more specific selector if not all images in .media-content are modal-triggering
document.querySelectorAll('.media-content img').forEach(img => {
    // Check if it already has an onclick to avoid re-binding if script runs multiple times
    if (img.onclick === null) { 
        img.style.cursor = 'pointer';
        img.onclick = function() { openImageModal(this); };
    }
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

// Escape key to close modal
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' || e.key === 'Esc') { // 'Esc' for older browsers
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
