# modules/issue_card_module.py
from modules.base_module import Module
from typing import Dict, Any


class IssueCardModule(Module):
    """Module for displaying issues/problems with solutions"""

    def __init__(self):
        super().__init__('issue_card', 'Issue Card')
        self.content_data = self.get_default_content()

    def get_default_content(self) -> Dict[str, Any]:
        return {
            'issue_title': 'Common Issue Title',
            'issue_description': 'Description of the issue or problem...',
            'solution_title': 'Solution:',
            'solution_content': 'Steps to resolve the issue...',
            'include_media': False,
            'media_source': '',
            'media_caption': '',
            'show_icon': True
        }

    def render_to_html(self) -> str:
        """Generate HTML for issue card"""
        # Media section if included
        media_html = ''
        if self.content_data.get('include_media') and self.content_data.get('media_source'):
            media_html = f'''
            <div class="media-container" style="--media-max-width: 545px">
                <div class="media-header">Related Screenshot</div>
                <div class="media-content">
                    <img src="{self.content_data['media_source']}" 
                         alt="{self.content_data.get('media_caption', '')}"
                         onclick="openImageModal(this)">
                </div>
                <div class="media-caption">
                    {self.content_data.get('media_caption', '')}
                </div>
            </div>'''

        # Parse solution content for list items
        solution_content = self.content_data['solution_content']
        if '\n' in solution_content and all(line.strip().startswith(('1.', '2.', '3.', '-', '*'))
                                           for line in solution_content.split('\n') if line.strip()):
            # Convert to ordered list
            lines = solution_content.split('\n')
            solution_html = '<ol>'
            for line in lines:
                if line.strip():
                    # Remove list markers
                    clean_line = line.strip().lstrip('0123456789.-* ')
                    solution_html += f'<li>{clean_line}</li>'
            solution_html += '</ol>'
        else:
            solution_html = f'<p>{solution_content}</p>'

        icon_html = ''
        if self.content_data.get('show_icon'):
            icon_html = '⚠️'

        return f'''
        <div class="issue-card">
            <h4>{icon_html} {self.content_data['issue_title']}</h4>
            <p>{self.content_data['issue_description']}</p>
            {media_html}
            <div class="solution">
                <strong>{self.content_data['solution_title']}</strong>
                {solution_html}
            </div>
        </div>'''

    def get_property_fields(self) -> Dict[str, str]:
        return {
            'issue_title': 'text',
            'issue_description': 'textarea',
            'solution_title': 'text',
            'solution_content': 'textarea',
            'include_media': 'checkbox',
            'media_source': 'file',
            'media_caption': 'text',
            'show_icon': 'checkbox'
        }
