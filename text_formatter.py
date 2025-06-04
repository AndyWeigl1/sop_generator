# utils/text_formatter.py
"""
Text Formatting Utility

Provides shared text formatting functionality for all modules that need to
process text with bold, bullet points, and numbered lists.
"""

import re
from typing import Optional


class TextFormatter:
    """Shared text formatting utility for consistent text processing across modules"""

    @staticmethod
    def format_text_content(text: str) -> str:
        """
        Format text content with bullets, numbers, and bold formatting.

        This method processes text to convert:
        - **text** to <strong>text</strong>
        - Lines starting with • into <ul><li> elements
        - Lines starting with numbers (1., 2., etc) into <ol><li> elements
        - Regular lines into <p> elements

        Args:
            text: Raw text content to format

        Returns:
            HTML-formatted text string
        """
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

    @staticmethod
    def format_for_list(text: str) -> str:
        """
        Format text specifically for list display (used in text_module.py)

        Args:
            text: Raw text content

        Returns:
            HTML list elements without wrapper tags
        """
        if not text:
            return ''

        # Apply bold formatting first
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)

        lines = text.split('\n')
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

        return content_html

    @staticmethod
    def format_for_paragraphs(text: str) -> str:
        """
        Format text for paragraph display with embedded lists

        Args:
            text: Raw text content

        Returns:
            HTML with paragraphs and embedded lists
        """
        if not text:
            return ''

        # Apply bold formatting first
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)

        # Split by double newlines for paragraphs
        paragraphs = text.split('\n\n')
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

        return content_html