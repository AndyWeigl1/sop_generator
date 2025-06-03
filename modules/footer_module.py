# modules/footer_module.py
from modules.base_module import Module
from typing import Dict, Any, List


class FooterModule(Module):
    """Module for page footer with copyright and revision info"""

    def __init__(self):
        super().__init__('footer', 'Footer')
        self.content_data = self.get_default_content()

    def get_default_content(self) -> Dict[str, Any]:
        return {
            'organization': 'Your Organization',
            'department': 'Department Name',
            'revision_date': 'MM.DD.YYYY',
            'background_image': 'assets/mountains.png',
            'additional_text': '',
            'show_copyright': True
        }

    def get_media_references(self) -> List[str]:
        """Return all media file paths used by this module"""
        media_refs = []

        background_image = self.content_data.get('background_image', '')
        if background_image and background_image.strip():
            cleaned_path = background_image.strip()

            # Skip if already a URI/URL
            if not cleaned_path.startswith(('file://', 'data:', 'http')):
                media_refs.append(cleaned_path)

        return media_refs

    def update_media_references(self, path_mapping: Dict[str, str]):
        """Update all media paths using the provided mapping"""
        background_image = self.content_data.get('background_image', '')

        if background_image and background_image.strip():
            # Skip if already a URI/URL
            if background_image.startswith(('file://', 'data:', 'http')):
                return

            # Find matching path using multiple strategies
            new_path = self._find_matching_path_in_mapping(background_image, path_mapping)

            if new_path:
                print(f"   ✅ Updated background_image: {background_image} -> {new_path[:50]}...")
                self.content_data['background_image'] = new_path
            else:
                print(f"   ❌ No mapping found for background_image: {background_image}")

    def render_to_html(self) -> str:
        """Generate HTML for footer"""
        # Build footer text
        footer_parts = []

        if self.content_data.get('show_copyright'):
            import datetime
            year = datetime.datetime.now().year
            footer_parts.append(f'© {year} {self.content_data["organization"]}')

        if self.content_data.get('department'):
            footer_parts.append(self.content_data['department'])

        if self.content_data.get('revision_date'):
            footer_parts.append(f'Rev. {self.content_data["revision_date"]}')

        footer_text = ' | '.join(footer_parts)

        # Additional text
        additional_html = ''
        if self.content_data.get('additional_text'):
            additional_html = f'<div class="footer-additional">{self.content_data["additional_text"]}</div>'

        # Background image
        bg_img_html = ''
        if self.content_data.get('background_image'):
            bg_img_html = f'''
            <img src="{self.content_data['background_image']}" 
                 alt="Footer background" 
                 class="footer-image">'''

        return f'''
        <div class="footer">
            {bg_img_html}
            <div class="footer-content">
                {footer_text}
                {additional_html}
            </div>
        </div>'''

    def get_property_fields(self) -> Dict[str, str]:
        return {
            'organization': 'text',
            'department': 'text',
            'revision_date': 'text',
            # 'background_image': 'file',
            'additional_text': 'textarea',
            'show_copyright': 'checkbox'
        }

