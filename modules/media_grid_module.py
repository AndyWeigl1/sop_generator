# modules/media_grid_module.py
from modules.base_module import Module
from typing import Dict, Any, List
import os
from utils.text_formatter import TextFormatter  # NEW IMPORT


class MediaGridModule(Module):
    """Enhanced module for displaying multiple media items in a grid layout with formatting support"""

    def __init__(self):
        super().__init__('media_grid', 'Media Grid')
        self.content_data = self.get_default_content()

    def get_default_content(self) -> Dict[str, Any]:
        return {
            'header': 'Media Gallery',
            'content_before': '',  # Text content before media grid
            'layout': 'side-by-side',  # 'side-by-side', 'grid-3', 'grid-4'
            'items': [
                {
                    'type': 'image',
                    'source': '',
                    'caption': 'Image 1',
                    'alt_text': '',
                    'header': 'Media Example'
                },
                {
                    'type': 'image',
                    'source': '',
                    'caption': 'Image 2',
                    'alt_text': '',
                    'header': 'Media Example'
                }
            ],
            'gap': 'medium',  # 'small', 'medium', 'large'
            'clickable': True,
            'content_after': '',  # Text content after media grid
            'max_width': '100%'  # Max width of the entire grid
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
        """Generate HTML for enhanced media grid"""
        # Content before grid - USING TextFormatter NOW
        content_before_html = ''
        if self.content_data.get('content_before'):
            formatted_content = TextFormatter.format_text_content(self.content_data['content_before'])
            content_before_html = f'''
            <div class="media-content-before">
                {formatted_content}
            </div>'''

        # Header
        header_html = ''
        if self.content_data.get('header'):
            header_html = f'<h3>{self.content_data["header"]}</h3>'

        # Grid layout classes
        grid_class = f'media-grid {self.content_data["layout"]}'
        gap_class = f'gap-{self.content_data.get("gap", "medium")}'

        # Generate media items
        items_html = ''
        for i, item in enumerate(self.content_data.get('items', [])):
            # Normalize the file path
            source = self._normalize_file_path(item.get('source', ''))

            # Determine header text - use a generic header if not specified
            header_text = item.get('header', f'Media {i + 1}')

            # Add proper CSS class for media type
            media_class = 'video' if item['type'] == 'video' else 'image'

            if item['type'] == 'image':
                click_handler = 'onclick="openImageModal(this)"' if self.content_data.get('clickable') else ''
                title_attr = 'title="Click to view full size"' if self.content_data.get('clickable') else ''
                media_html = f'''
                <img src="{source}" 
                     alt="{item.get('alt_text', '')}"
                     style="width: 100%; height: auto; object-fit: contain;"
                     {click_handler}
                     {title_attr}>'''
            else:  # video
                media_html = f'''
                <iframe src="{source}"
                        title="{item.get('alt_text', '')}"
                        style="width: 100%; height: 300px; border: none;"
                        allowfullscreen>
                </iframe>'''

            # Caption with click instruction for images
            caption_html = ''
            if item.get('caption'):
                click_instruction = ''
                if self.content_data.get('clickable') and item['type'] == 'image':
                    click_instruction = '<span style="color: var(--kodiak-red, #e74c3c); font-size: 0.9em;">(Click image to view full size)</span>'

                caption_html = f'''<div class="media-caption">
                    {item["caption"]}
                    {click_instruction}
                </div>'''

            items_html += f'''
            <div class="media-container">
                <div class="media-header {media_class}">{header_text}</div>
                <div class="media-content">
                    {media_html}
                </div>
                {caption_html}
            </div>'''

        # Content after grid - USING TextFormatter NOW
        content_after_html = ''
        if self.content_data.get('content_after'):
            formatted_content = TextFormatter.format_text_content(self.content_data['content_after'])
            content_after_html = f'''
            <div class="media-content-after">
                {formatted_content}
            </div>'''

        # Handle max-width
        style_attrs = f"max-width: {self.content_data.get('max_width', '100%')}"

        # Combine all elements
        html_parts = []

        if header_html:
            html_parts.append(header_html)

        if content_before_html:
            html_parts.append(content_before_html)

        html_parts.append(f'''
        <div class="{grid_class} {gap_class}" style="{style_attrs}">
            {items_html}
        </div>''')

        if content_after_html:
            html_parts.append(content_after_html)

        return '\n'.join(html_parts)

    def get_property_fields(self) -> Dict[str, str]:
        return {
            'header': 'text',
            'content_before': 'textarea:formatted',  # Enable formatting toolbar
            'layout': 'dropdown:side-by-side,grid-3,grid-4',
            'items': 'media_list_editor',
            'gap': 'dropdown:small,medium,large',
            'clickable': 'checkbox',
            'content_after': 'textarea:formatted',  # Enable formatting toolbar
            'max_width': 'text'
        }

    def get_media_references(self) -> List[str]:
        """Return all media file paths used by this module"""
        media_refs = []

        items = self.content_data.get('items', [])
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    source = item.get('source', '')
                    if source and source.strip():
                        media_refs.append(source)

        return media_refs

    def update_media_references(self, path_mapping: Dict[str, str]):
        """Update all media paths using the provided mapping"""
        items = self.content_data.get('items', [])
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    source = item.get('source', '')
                    if source and source.strip():
                        # Normalize the path before lookup
                        normalized_source = self._normalize_media_path(source)
                        if normalized_source in path_mapping:
                            item['source'] = path_mapping[normalized_source]

    def update_content(self, key: str, value: Any):
        """Update specific content field with path normalization for media items"""
        if key == 'items' and isinstance(value, list):
            # Normalize file paths in media items
            normalized_items = []
            for item in value:
                if isinstance(item, dict):
                    normalized_item = item.copy()
                    if 'source' in normalized_item:
                        normalized_item['source'] = self._normalize_file_path(normalized_item['source'])
                    normalized_items.append(normalized_item)
                else:
                    normalized_items.append(item)
            self.content_data[key] = normalized_items
        else:
            self.content_data[key] = value