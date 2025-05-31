# modules/footer_module.py
from modules.base_module import Module
from typing import Dict, Any


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
            'background_image': None,
            'additional_text': '',
            'show_copyright': True
        }

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
            'background_image': 'file',
            'additional_text': 'textarea',
            'show_copyright': 'checkbox'
        }

