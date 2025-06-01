# modules/text_module.py
from modules.base_module import Module
from typing import Dict, Any
import re


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

    def _format_text_content(self, text: str) -> str:
        """Apply text formatting for bold, bullets, and numbers"""
        if not text:
            return ''

        # Apply bold formatting
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)

        return text

    def render_to_html(self) -> str:
        """Generate HTML for text module"""
        header_html = ''
        if self.content_data.get('header'):
            header_html = f'<h3>{self.content_data["header"]}</h3>'

        content = self.content_data['content']

        # Apply text formatting
        content = self._format_text_content(content)

        # Format content based on type
        if self.content_data['format'] == 'list':
            # Enhanced list processing to handle both bullet and numbered lists
            lines = content.split('\n')
            content_html = ''
            current_list = None

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Check for bullet points
                if line.startswith('• '):
                    if current_list != 'ul':
                        if current_list:
                            content_html += f'</{current_list}>'
                        content_html += '<ul>'
                        current_list = 'ul'
                    content_html += f'<li>{line[2:]}</li>'

                # Check for numbered items
                elif re.match(r'^\d+\.\s', line):
                    if current_list != 'ol':
                        if current_list:
                            content_html += f'</{current_list}>'
                        content_html += '<ol>'
                        current_list = 'ol'
                    item_content = re.sub(r'^\d+\.\s', '', line)
                    content_html += f'<li>{item_content}</li>'

                # Regular list item (for backward compatibility)
                else:
                    if current_list != 'ul':
                        if current_list:
                            content_html += f'</{current_list}>'
                        content_html += '<ul>'
                        current_list = 'ul'
                    content_html += f'<li>{line}</li>'

            # Close any open list
            if current_list:
                content_html += f'</{current_list}>'

        elif self.content_data['format'] == 'blockquote':
            content_html = f'<blockquote>{content}</blockquote>'
        else:  # paragraph
            # Split by double newlines for paragraphs
            paragraphs = content.split('\n\n')
            content_html = ''
            for para in paragraphs:
                if para.strip():
                    # Check if paragraph contains list items
                    if '• ' in para or re.search(r'\d+\.\s', para):
                        # Process as a list within paragraphs
                        lines = para.split('\n')
                        para_content = ''
                        list_html = ''
                        current_list = None

                        for line in lines:
                            line = line.strip()
                            if line.startswith('• '):
                                if current_list != 'ul':
                                    if current_list:
                                        list_html += f'</{current_list}>'
                                    list_html += '<ul>'
                                    current_list = 'ul'
                                list_html += f'<li>{line[2:]}</li>'
                            elif re.match(r'^\d+\.\s', line):
                                if current_list != 'ol':
                                    if current_list:
                                        list_html += f'</{current_list}>'
                                    list_html += '<ol>'
                                    current_list = 'ol'
                                item_content = re.sub(r'^\d+\.\s', '', line)
                                list_html += f'<li>{item_content}</li>'
                            else:
                                if current_list:
                                    list_html += f'</{current_list}>'
                                    content_html += list_html
                                    list_html = ''
                                    current_list = None
                                if line:
                                    para_content += line + ' '

                        # Close any remaining list
                        if current_list:
                            list_html += f'</{current_list}>'
                            content_html += list_html

                        # Add any remaining paragraph content
                        if para_content.strip():
                            content_html += f'<p>{para_content.strip()}</p>'
                    else:
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
            'content': 'textarea:formatted',  # Enable formatting toolbar
            'format': 'dropdown:paragraph,list,blockquote',
            'style': 'dropdown:normal,emphasized,code'
        }


