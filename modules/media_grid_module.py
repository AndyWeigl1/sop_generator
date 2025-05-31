# modules/media_grid_module.py
from modules.base_module import Module
from typing import Dict, Any, List


class MediaGridModule(Module):
    """Module for displaying multiple media items in a grid layout"""

    def __init__(self):
        super().__init__('media_grid', 'Media Grid')
        self.content_data = self.get_default_content()

    def get_default_content(self) -> Dict[str, Any]:
        return {
            'layout': 'side-by-side',  # 'side-by-side', 'grid-3', 'grid-4'
            'items': [
                {
                    'type': 'image',
                    'source': '',
                    'caption': 'Image 1',
                    'alt_text': ''
                },
                {
                    'type': 'image',
                    'source': '',
                    'caption': 'Image 2',
                    'alt_text': ''
                }
            ],
            'gap': 'medium',  # 'small', 'medium', 'large'
            'clickable': True
        }

    def render_to_html(self) -> str:
        """Generate HTML for media grid"""
        grid_class = f'media-grid {self.content_data["layout"]}'
        gap_class = f'gap-{self.content_data.get("gap", "medium")}'

        items_html = ''
        for item in self.content_data.get('items', []):
            if item['type'] == 'image':
                click_handler = 'onclick="openImageModal(this)"' if self.content_data.get('clickable') else ''
                media_html = f'''
                <img src="{item['source']}" 
                     alt="{item.get('alt_text', '')}"
                     {click_handler}>'''
            else:  # video
                media_html = f'''
                <iframe src="{item['source']}"
                        title="{item.get('alt_text', '')}"
                        allowfullscreen>
                </iframe>'''

            caption_html = ''
            if item.get('caption'):
                caption_html = f'<div class="media-caption">{item["caption"]}</div>'

            items_html += f'''
            <div class="media-container">
                <div class="media-content">
                    {media_html}
                </div>
                {caption_html}
            </div>'''

        return f'''
        <div class="{grid_class} {gap_class}">
            {items_html}
        </div>'''

    def get_property_fields(self) -> Dict[str, str]:
        return {
            'layout': 'dropdown:side-by-side,grid-3,grid-4',
            'items': 'media_list_editor',
            'gap': 'dropdown:small,medium,large',
            'clickable': 'checkbox'
        }
