# modules/table_module.py - Enhanced with multiple content and table sections
from modules.base_module import Module
from typing import Dict, Any, List
import json
import re


class TableModule(Module):
    """Enhanced module for displaying mixed content and tables with formatting support"""

    def __init__(self):
        super().__init__('table', 'Table Section')
        self.content_data = self.get_default_content()

    def get_default_content(self) -> Dict[str, Any]:
        return {
            'header': 'Table Section',  # Optional main header
            'sections': [
                {
                    'type': 'content',
                    'content': 'Enter your content here. You can use **bold text**, bullet points, and numbered lists.\n\n• Bullet point 1\n• Bullet point 2'
                },
                {
                    'type': 'table',
                    'title': 'Data Table',
                    'headers': ['Column 1', 'Column 2', 'Column 3'],
                    'rows': [
                        ['Row 1 Col 1', 'Row 1 Col 2', 'Row 1 Col 3'],
                        ['Row 2 Col 1', 'Row 2 Col 2', 'Row 2 Col 3']
                    ],
                    'hover_effect': True,
                    'compact': False
                }
            ]
        }

    def _format_text_content(self, text: str) -> str:
        """Format text content with bullets, numbers, and bold (copied from text_module)"""
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

    def _render_table_section(self, section: Dict[str, Any]) -> str:
        """Render a single table section"""
        # Table title
        title_html = ''
        if section.get('title'):
            title_html = f'<h4>{section["title"]}</h4>'

        # Build table HTML
        table_classes = ['custom-table']
        if section.get('hover_effect', True):
            table_classes.append('hover-effect')
        if section.get('compact', False):
            table_classes.append('compact')

        table_html = f'<table class="{" ".join(table_classes)}">'

        # Headers
        headers = section.get('headers', [])
        if headers:
            table_html += '<thead><tr>'
            for header in headers:
                table_html += f'<th>{header}</th>'
            table_html += '</tr></thead>'

        # Body
        table_html += '<tbody>'
        rows = section.get('rows', [])
        for row in rows:
            table_html += '<tr>'
            for cell in row:
                table_html += f'<td>{cell}</td>'
            table_html += '</tr>'
        table_html += '</tbody></table>'

        return f'''
        <div class="table-section">
            {title_html}
            <div class="table-container">
                {table_html}
            </div>
        </div>'''

    def _render_content_section(self, section: Dict[str, Any]) -> str:
        """Render a single content section"""
        content = section.get('content', '')
        if not content:
            return ''

        formatted_content = self._format_text_content(content)

        return f'''
        <div class="content-section">
            {formatted_content}
        </div>'''

    def render_to_html(self) -> str:
        """Generate HTML for enhanced table module"""
        # Main header
        header_html = ''
        if self.content_data.get('header'):
            header_html = f'<h3>{self.content_data["header"]}</h3>'

        # Process all sections
        sections_html = ''
        sections = self.content_data.get('sections', [])

        for section in sections:
            section_type = section.get('type', 'content')

            if section_type == 'table':
                sections_html += self._render_table_section(section)
            elif section_type == 'content':
                sections_html += self._render_content_section(section)

        return f'''
        <div class="enhanced-table-module">
            {header_html}
            {sections_html}
        </div>'''

    def get_property_fields(self) -> Dict[str, str]:
        return {
            'header': 'text',
            'sections': 'sections_editor'  # Custom editor for sections
        }

    def update_content(self, key: str, value: Any):
        """Update specific content field with special handling for sections"""
        if key == 'sections' and isinstance(value, list):
            # Validate and clean sections data
            cleaned_sections = []
            for section in value:
                if isinstance(section, dict) and 'type' in section:
                    if section['type'] == 'table':
                        # Ensure table has required fields
                        cleaned_section = {
                            'type': 'table',
                            'title': section.get('title', 'Table'),
                            'headers': section.get('headers', ['Column 1', 'Column 2']),
                            'rows': section.get('rows', [['Data 1', 'Data 2']]),
                            'hover_effect': section.get('hover_effect', True),
                            'compact': section.get('compact', False)
                        }
                    elif section['type'] == 'content':
                        # Ensure content has required fields
                        cleaned_section = {
                            'type': 'content',
                            'content': section.get('content', 'Enter content here...')
                        }
                    else:
                        continue  # Skip unknown types

                    cleaned_sections.append(cleaned_section)

            self.content_data[key] = cleaned_sections
        elif key == 'sections' and isinstance(value, str):
            # Handle JSON string input (fallback)
            try:
                parsed_sections = json.loads(value)
                self.update_content('sections', parsed_sections)
            except json.JSONDecodeError:
                # If JSON parsing fails, keep existing data
                pass
        else:
            self.content_data[key] = value
