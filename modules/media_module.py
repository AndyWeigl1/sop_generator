# modules/media_module.py
from modules.base_module import Module
from typing import Dict, Any, List


class MediaModule(Module):
    """Module for images and videos with captions"""

    def __init__(self):
        super().__init__('media', 'Media Container')
        self.content_data = self.get_default_content()

    def get_default_content(self) -> Dict[str, Any]:
        return {
            'media_type': 'image',  # 'image' or 'video'
            'source': '',  # File path or URL
            'alt_text': '',
            'caption': '',
            'header': '',
            'max_width': '800px',
            'clickable': True  # Enable modal view
        }

    def render_to_html(self) -> str:
        """Generate HTML for media module"""
        header_html = ''
        if self.content_data.get('header'):
            icon = '🎥' if self.content_data['media_type'] == 'video' else ''
            header_html = f'''
            <div class="media-header {self.content_data['media_type']}">
                {self.content_data['header']}
            </div>'''

        media_html = ''
        if self.content_data['media_type'] == 'image':
            click_handler = 'onclick="openImageModal(this)"' if self.content_data.get('clickable') else ''
            media_html = f'''
            <img src="{self.content_data['source']}" 
                 alt="{self.content_data.get('alt_text', '')}"
                 style="width: 100%; height: auto; object-fit: contain;"
                 {click_handler}>'''
        else:  # video
            media_html = f'''
            <iframe src="{self.content_data['source']}"
                    title="{self.content_data.get('alt_text', '')}"
                    style="width: 100%; height: 400px; border: none;"
                    allowfullscreen>
            </iframe>'''

        caption_html = ''
        if self.content_data.get('caption'):
            caption_html = f'''
            <div class="media-caption">
                {self.content_data['caption']}
            </div>'''

        return f'''
        <div class="media-container" style="--media-max-width: {self.content_data['max_width']}">
            {header_html}
            <div class="media-content">
                {media_html}
            </div>
            {caption_html}
        </div>'''

    def get_property_fields(self) -> Dict[str, str]:
        return {
            'media_type': 'dropdown:image,video',
            'source': 'file_or_url',
            'alt_text': 'text',
            'caption': 'textarea',
            'header': 'text',
            'max_width': 'text',
            'clickable': 'checkbox'
        }