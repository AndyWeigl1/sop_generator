from modules.base_module import Module
from typing import Dict, Any, List

# modules/step_card_module.py
class StepCardModule(Module):
    """Module for numbered step cards"""

    def __init__(self):
        super().__init__('step_card', 'Step Card')
        self.content_data = self.get_default_content()

    def get_default_content(self) -> Dict[str, Any]:
        return {
            'step_number': '1',
            'title': 'Step Title',
            'content': 'Step description and instructions...',
            'content_type': 'text'  # Can be 'text', 'list', 'mixed'
        }

    def render_to_html(self) -> str:
        content_html = self._render_content()

        return f'''
        <div class="step-card">
            <div class="step-number">{self.content_data['step_number']}</div>
            <h3>{self.content_data['title']}</h3>
            {content_html}
        </div>'''

    def _render_content(self) -> str:
        """Render content based on content_type"""
        content = self.content_data['content']
        if self.content_data['content_type'] == 'text':
            return f'<p>{content}</p>'
        elif self.content_data['content_type'] == 'list':
            # Parse list items (assuming newline separated)
            items = content.split('\n')
            list_html = '<ul>'
            for item in items:
                if item.strip():
                    list_html += f'<li>{item.strip()}</li>'
            list_html += '</ul>'
            return list_html
        return content

    def get_property_fields(self) -> Dict[str, str]:
        return {
            'step_number': 'text',
            'title': 'text',
            'content': 'textarea',
            'content_type': 'dropdown:text,list,mixed'
        }