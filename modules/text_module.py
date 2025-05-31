# modules/text_module.py
from modules.base_module import Module
from typing import Dict, Any


class TextModule(Module):
    """Module for text content with formatting options"""

    def __init__(self):
        super().__init__('text', 'Text Content')
        self.content_data = self.get_default_content()

    def get_default_content(self) -> Dict[str, Any]:
        return {
            'content': 'Enter your text content here...',
            'format': 'paragraph',  # 'paragraph', 'list', 'blockquote'
            'header': '',
            'style': 'normal'  # 'normal', 'emphasized', 'code'
        }

    def render_to_html(self) -> str:
        """Generate HTML for text module"""
        header_html = ''
        if self.content_data.get('header'):
            header_html = f'<h3>{self.content_data["header"]}</h3>'

        content = self.content_data['content']

        # Format content based on type
        if self.content_data['format'] == 'list':
            # Split by newlines and create list items
            items = content.split('\n')
            content_html = '<ul>'
            for item in items:
                if item.strip():
                    content_html += f'<li>{item.strip()}</li>'
            content_html += '</ul>'
        elif self.content_data['format'] == 'blockquote':
            content_html = f'<blockquote>{content}</blockquote>'
        else:  # paragraph
            # Split by double newlines for paragraphs
            paragraphs = content.split('\n\n')
            content_html = ''
            for para in paragraphs:
                if para.strip():
                    content_html += f'<p>{para.strip()}</p>'

        # Apply style classes
        style_class = f'text-{self.content_data["style"]}' if self.content_data['style'] != 'normal' else ''

        return f'''
        <div class="text-module {style_class}">
            {header_html}
            <div class="text-content">
                {content_html}
            </div>
        </div>'''

    def get_property_fields(self) -> Dict[str, str]:
        return {
            'header': 'text',
            'content': 'textarea',
            'format': 'dropdown:paragraph,list,blockquote',
            'style': 'dropdown:normal,emphasized,code'
        }