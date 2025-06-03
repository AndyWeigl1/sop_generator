# modules/disclaimer_module.py
from modules.base_module import Module
from typing import Dict, Any
import re


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

    def _format_text_content(self, text: str) -> str:
        """Apply text formatting for bold, bullets, and numbers (copied from text_module)"""
        if not text:
            return ''

        lines = text.split('\n')
        formatted_lines = []
        in_list = False
        list_type = None

        for line in lines:
            stripped_line = line.strip()

            if not stripped_line:
                # Empty line - close any open lists
                if in_list:
                    formatted_lines.append(f'</{list_type}>')
                    in_list = False
                    list_type = None
                formatted_lines.append('')
                continue

            # Process bold text
            formatted_line = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', stripped_line)

            # Check for bullet points
            if formatted_line.startswith('• '):
                if not in_list or list_type != 'ul':
                    if in_list:
                        formatted_lines.append(f'</{list_type}>')
                    formatted_lines.append('<ul>')
                    in_list = True
                    list_type = 'ul'
                formatted_lines.append(f'<li>{formatted_line[2:]}</li>')

            # Check for numbered items
            elif re.match(r'^\d+\.\s', formatted_line):
                if not in_list or list_type != 'ol':
                    if in_list:
                        formatted_lines.append(f'</{list_type}>')
                    formatted_lines.append('<ol>')
                    in_list = True
                    list_type = 'ol'
                content = re.sub(r'^\d+\.\s', '', formatted_line)
                formatted_lines.append(f'<li>{content}</li>')

            else:
                # Regular paragraph
                if in_list:
                    formatted_lines.append(f'</{list_type}>')
                    in_list = False
                    list_type = None
                formatted_lines.append(f'<p>{formatted_line}</p>')

        # Close any remaining open list
        if in_list:
            formatted_lines.append(f'</{list_type}>')

        return '\n'.join(formatted_lines)

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

        # Apply enhanced text formatting
        content = self.content_data['content']
        content_html = self._format_text_content(content)

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
