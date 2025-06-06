# modules/disclaimer_module.py
from modules.base_module import Module
from typing import Dict, Any
from utils.text_formatter import TextFormatter  # NEW IMPORT


class DisclaimerModule(Module):
    """Module for disclaimers, warnings, and important notices"""

    def __init__(self):
        super().__init__('disclaimer', 'Disclaimer Box')
        self.content_data = self.get_default_content()

    def get_default_content(self) -> Dict[str, Any]:
        return {
            'label': 'IMPORTANT!',
            'title': 'Before You Begin:',
            'content': 'Important information or warnings go here...',
            'type': 'warning',  # 'warning', 'info', 'danger', 'success'
            'icon': True
        }

    def render_to_html(self) -> str:
        """Generate HTML for disclaimer box with enhanced text formatting"""
        # Icon mapping based on type
        icon_map = {
            'warning': '⚠️',
            'info': 'ℹ️',
            'danger': '🚫',
            'success': '✅'
        }

        icon_html = ''
        if self.content_data.get('icon'):
            icon = icon_map.get(self.content_data.get('type', 'warning'), '⚠️')
            icon_html = f'<span class="disclaimer-icon">{icon}</span>'

        title_html = ''
        if self.content_data.get('title'):
            title_html = f'<strong>{self.content_data["title"]}</strong>'

        # Apply enhanced text formatting - USING TextFormatter NOW
        content = self.content_data['content']
        content_html = TextFormatter.format_text_content(content)

        type_class = f'disclaimer-{self.content_data.get("type", "warning")}'

        return f'''
        <div class="disclaimer-box {type_class}">
            {icon_html}
            {title_html}
            {content_html}
        </div>'''

    def get_property_fields(self) -> Dict[str, str]:
        return {
            'label': 'text',
            'title': 'text',
            'content': 'textarea:formatted',  # Enable formatting toolbar
            'type': 'dropdown:warning,info,danger,success',
            'icon': 'checkbox'
        }
