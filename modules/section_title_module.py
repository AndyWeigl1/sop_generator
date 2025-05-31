# modules/section_title_module.py
from modules.base_module import Module
from typing import Dict, Any


class SectionTitleModule(Module):
    """Module for section titles with optional subtitles"""

    def __init__(self):
        super().__init__('section_title', 'Section Title')
        self.content_data = self.get_default_content()

    def get_default_content(self) -> Dict[str, Any]:
        return {
            'title': 'Section Title',
            'subtitle': '',
            'style': 'default',  # 'default', 'centered', 'underlined'
            'size': 'large'  # 'small', 'medium', 'large'
        }

    def render_to_html(self) -> str:
        """Generate HTML for section title"""
        subtitle_html = ''
        if self.content_data.get('subtitle'):
            subtitle_html = f'<p>{self.content_data["subtitle"]}</p>'

        # Determine heading tag based on size
        heading_tag = {
            'small': 'h4',
            'medium': 'h3',
            'large': 'h2'
        }.get(self.content_data.get('size', 'large'), 'h2')

        style_class = f'section-title-{self.content_data.get("style", "default")}'

        return f'''
        <div class="section-title {style_class}">
            <{heading_tag}>{self.content_data['title']}</{heading_tag}>
            {subtitle_html}
        </div>'''

    def get_property_fields(self) -> Dict[str, str]:
        return {
            'title': 'text',
            'subtitle': 'text',
            'style': 'dropdown:default,centered,underlined',
            'size': 'dropdown:small,medium,large'
        }
