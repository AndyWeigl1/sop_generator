from modules.base_module import Module
from typing import Dict, Any, List


# modules/header_module.py
class HeaderModule(Module):
    """Module for SOP header with title, subtitle, and logo"""

    def __init__(self):
        super().__init__('header', 'Header')
        self.content_data = self.get_default_content()

    def get_default_content(self) -> Dict[str, Any]:
        return {
            'title': 'Standard Operating Procedure',
            'subtitle': 'Process Name',
            'date': 'Last Updated: MM/DD/YYYY',
            'logo_path': 'assets/kodiak.png',
            'document_label': 'Standard Operating Procedure'
        }

    def get_media_references(self) -> List[str]:
        """Return all media file paths used by this module"""
        media_refs = []

        logo_path = self.content_data.get('logo_path', '')
        if logo_path and logo_path.strip():
            cleaned_path = logo_path.strip()

            # Skip if already a URI/URL
            if not cleaned_path.startswith(('file://', 'data:', 'http')):
                media_refs.append(cleaned_path)

        return media_refs

        return media_refs

    def update_media_references(self, path_mapping: Dict[str, str]):
        """Update all media paths using the provided mapping"""
        logo_path = self.content_data.get('logo_path', '')

        if logo_path and logo_path.strip():
            # Skip if already a URI/URL
            if logo_path.startswith(('file://', 'data:', 'http')):
                return

            # Find matching path using multiple strategies
            new_path = self._find_matching_path_in_mapping(logo_path, path_mapping)

            if new_path:
                print(f"   ✅ Updated logo_path: {logo_path} -> {new_path[:50]}...")
                self.content_data['logo_path'] = new_path
            else:
                print(f"   ❌ No mapping found for logo_path: {logo_path}")

    def render_to_html(self) -> str:
        """Generate HTML for header module"""
        logo_html = ''
        if self.content_data.get('logo_path'):
            logo_html = f'''
            <div class="logo-container">
                <img src="{self.content_data['logo_path']}" alt="Logo">
            </div>'''

        return f'''
        <div class="document-label">{self.content_data['document_label']}</div>
        <div class="header">
            <div class="header-content">
                <h1>{self.content_data['title']}</h1>
                <p>{self.content_data['date']}</p>
            </div>
            {logo_html}
        </div>'''

    def get_property_fields(self) -> Dict[str, str]:
        return {
            'title': 'text',
            'subtitle': 'text',
            'date': 'text',
            # 'logo_path': 'file',
            'document_label': 'text'
        }
