# modules/media_module.py
from modules.base_module import Module
from typing import Dict, Any, List
import os


class MediaModule(Module):
    """Module for images and videos with captions"""

    def __init__(self):
        super().__init__('media', 'Media Container')
        self.content_data = self.get_default_content()

    def get_default_content(self) -> Dict[str, Any]:
        return {
            'media_type': 'image',  # 'image' or 'video'
            'source': '',  # File path or URL
            'alt_text': 'Image description',
            'caption': 'Image caption text (click to view full size)',
            'header': 'Media Title',
            'max_width': '800px',
            'max_height': '',  # Optional max height
            'clickable': True  # Enable modal view
        }

    def _normalize_file_path(self, file_path: str) -> str:
        """Convert Windows file paths to web-compatible relative paths"""
        if not file_path:
            return ''

        # Remove extra quotes if present
        cleaned_path = file_path.strip('"\'')

        # If it's a Windows absolute path, try to convert to relative
        if '\\' in cleaned_path and ':' in cleaned_path:
            # Extract just the filename for now - in production you'd want to
            # copy files to Assets folder and reference them there
            filename = os.path.basename(cleaned_path)
            return f'Assets/{filename}'

        # If it's already a relative path, use as-is
        return cleaned_path

    def render_to_html(self) -> str:
        """Generate HTML for media module"""
        # Normalize the source path
        source_path = self._normalize_file_path(self.content_data['source'])

        header_html = ''
        if self.content_data.get('header'):
            # Add proper CSS class for image vs video
            media_class = 'video' if self.content_data['media_type'] == 'video' else 'image'
            header_html = f'''
            <div class="media-header {media_class}">
                {self.content_data['header']}
            </div>'''

        media_html = ''
        if self.content_data['media_type'] == 'image':
            click_handler = 'onclick="openImageModal(this)"' if self.content_data.get('clickable') else ''
            title_attr = 'title="Click to view full size"' if self.content_data.get('clickable') else ''

            media_html = f'''
            <img src="{source_path}" 
                 alt="{self.content_data.get('alt_text', '')}"
                 style="width: 100%; height: auto; object-fit: contain;"
                 {click_handler}
                 {title_attr}>'''
        else:  # video
            media_html = f'''
            <iframe src="{source_path}"
                    title="{self.content_data.get('alt_text', '')}"
                    style="width: 100%; height: 400px; border: none;"
                    allowfullscreen>
            </iframe>'''

        caption_html = ''
        if self.content_data.get('caption'):
            # Add the click instruction for clickable images
            click_instruction = ''
            if self.content_data.get('clickable') and self.content_data['media_type'] == 'image':
                click_instruction = f'''
                <span style="color: var(--kodiak-red); font-size: 0.9em;">(Click image to view full size)</span>'''

            caption_html = f'''
            <div class="media-caption">
                {self.content_data['caption']}
                {click_instruction}
            </div>'''

        # Handle max-width and max-height
        style_attrs = f"--media-max-width: {self.content_data['max_width']}"
        if self.content_data.get('max_height'):
            style_attrs += f"; --media-max-height: {self.content_data['max_height']}"

        return f'''
        <div class="media-container" style="{style_attrs}">
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
            'max_height': 'text',  # Add max_height field
            'clickable': 'checkbox'
        }

    def update_content(self, key: str, value: Any):
        """Update specific content field with path normalization"""
        if key == 'source':
            # Normalize file paths when they're updated
            self.content_data[key] = self._normalize_file_path(value)
        else:
            self.content_data[key] = value
