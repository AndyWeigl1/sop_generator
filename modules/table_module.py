# modules/table_module.py
from modules.base_module import Module
from typing import Dict, Any, List
import json


class TableModule(Module):
    """Module for displaying tabular data"""

    def __init__(self):
        super().__init__('table', 'Table')
        self.content_data = self.get_default_content()

    def get_default_content(self) -> Dict[str, Any]:
        return {
            'title': 'Table Title',
            'headers': ['Column 1', 'Column 2', 'Column 3'],
            'rows': [
                ['Row 1 Col 1', 'Row 1 Col 2', 'Row 1 Col 3'],
                ['Row 2 Col 1', 'Row 2 Col 2', 'Row 2 Col 3']
            ],
            'hover_effect': True,
            'compact': False
        }

    def render_to_html(self) -> str:
        """Generate HTML for table module"""
        title_html = ''
        if self.content_data.get('title'):
            title_html = f'<h3>{self.content_data["title"]}</h3>'

        # Build table HTML
        table_classes = ['custom-table']
        if self.content_data.get('hover_effect'):
            table_classes.append('hover-effect')
        if self.content_data.get('compact'):
            table_classes.append('compact')

        table_html = f'<table class="{" ".join(table_classes)}">'

        # Headers
        if self.content_data.get('headers'):
            table_html += '<thead><tr>'
            for header in self.content_data['headers']:
                table_html += f'<th>{header}</th>'
            table_html += '</tr></thead>'

        # Body
        table_html += '<tbody>'
        for row in self.content_data.get('rows', []):
            table_html += '<tr>'
            for cell in row:
                table_html += f'<td>{cell}</td>'
            table_html += '</tr>'
        table_html += '</tbody></table>'

        return f'''
        <div class="table-module">
            {title_html}
            <div class="table-container">
                {table_html}
            </div>
        </div>'''

    def get_property_fields(self) -> Dict[str, str]:
        return {
            'title': 'text',
            'headers': 'list_editor',
            'rows': 'table_editor',
            'hover_effect': 'checkbox',
            'compact': 'checkbox'
        }

    def update_content(self, key: str, value: Any):
        """Override to handle special table data updates"""
        if key == 'headers' and isinstance(value, str):
            # Convert comma-separated string to list
            self.content_data[key] = [h.strip() for h in value.split(',')]
        elif key == 'rows' and isinstance(value, str):
            # Parse JSON string for rows
            try:
                self.content_data[key] = json.loads(value)
            except:
                # Fallback to simple parsing
                self.content_data[key] = [[cell.strip() for cell in row.split(',')]
                                          for row in value.split('\n') if row.strip()]
        else:
            super().update_content(key, value)
