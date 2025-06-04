# modules/media_module.py - FIXED with separate card title and media header
from modules.base_module import Module
from typing import Dict, Any, List
import os
from utils.text_formatter import TextFormatter  # NEW IMPORT


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
            'title': '',  # NEW: Card title (h3 at top of card) - separate from media header
            'header': 'Media Title',  # Media container header (dark bar above image)
            'max_width': '800px',
            'max_height': '',  # Optional max height
            'clickable': True,  # Enable modal view
            'content_before': '',  # Text content before media
            'content_after': ''  # Text content after media
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

    def _is_base64_data(self, data_string: str) -> bool:
        """
        Check if a string appears to be base64 data rather than a file path

        Args:
            data_string: String to check

        Returns:
            True if it appears to be base64 data
        """
        if not data_string or not isinstance(data_string, str):
            return False

        # Check for data URL format (most reliable indicator)
        if data_string.startswith('data:'):
            return True

        # If it has obvious file path characteristics, it's NOT base64
        if any(char in data_string for char in ['/', '\\', '.png', '.jpg', '.jpeg', '.gif', '.mp4', '.webm']):
            return False

        # Check if it looks like pure base64 (no path separators, very long, base64 characters)
        if (len(data_string) > 100 and  # Base64 data is typically much longer
                not any(char in data_string for char in r'\/.:') and  # No path separators or extensions
                data_string.replace('=', '').replace('+', '').replace('/', '').isalnum() and
                len(data_string) % 4 == 0):  # Base64 length is typically multiple of 4
            return True

        return False

    def get_media_references(self) -> List[str]:
        """Return all media file paths used by this module"""
        media_refs = []

        source = self.content_data.get('source', '')
        print(f"MediaModule source from content_data: '{source}' (type: {type(source)})")

        if source and source.strip():
            cleaned_source = source.strip()

            # Check if this is base64 data instead of a file path
            if self._is_base64_data(cleaned_source):
                print(f"⚠️ MediaModule: Source appears to be base64 data, not a file path: '{cleaned_source[:20]}...'")
                return []  # Don't treat base64 data as a file reference

            # Skip if already a URI/URL
            if cleaned_source.startswith(('file://', 'http')):
                print(f"⚠️ MediaModule: Source is already a URI/URL, skipping: '{cleaned_source[:50]}...'")
                return []

            print(f"Adding MediaModule source: '{cleaned_source}'")
            media_refs.append(cleaned_source)

        print(f"MediaModule returning {len(media_refs)} references: {media_refs}")
        return media_refs

    def update_media_references(self, path_mapping: Dict[str, str]):
        """Update all media paths using the provided mapping"""
        source = self.content_data.get('source', '')
        print(f"🔧 Original source: '{source}'")

        if source and source.strip():
            # Skip if source is already base64 data
            if self._is_base64_data(source):
                print(f"🔧 Source is already base64 data, skipping update")
                return

            # Skip if already a URI/URL
            if source.startswith(('file://', 'data:', 'http')):
                print(f"🔧 Source is already a URI/URL, skipping update")
                return

            # Find matching path using multiple strategies
            new_path = self._find_matching_path_in_mapping(source, path_mapping)

            if new_path:
                old_source = self.content_data['source']
                self.content_data['source'] = new_path
                print(f"🔧 Updated source from '{old_source}' to '{new_path[:50]}...'")
            else:
                print(f"🔧 Could not find mapping for source: '{source}'")
                print(f"🔧 Available mapping keys: {list(path_mapping.keys())}")

    def render_to_html(self) -> str:
        """Generate HTML for media module with separate card title and media header"""
        # Normalize the source path
        source_path = self._normalize_file_path(self.content_data['source'])

        # Card title (h3 at top of content) - NEW
        card_title_html = ''
        if self.content_data.get('title'):
            card_title_html = f'<h3>{self.content_data["title"]}</h3>\n'

        # Content before media - USING TextFormatter NOW
        content_before_html = ''
        if self.content_data.get('content_before'):
            formatted_content = TextFormatter.format_text_content(self.content_data['content_before'])
            content_before_html = f'''
            <div class="media-content-before">
                {formatted_content}
            </div>'''

        # Media container header (dark bar above image)
        media_header_html = ''
        if self.content_data.get('header'):
            # Add proper CSS class for image vs video
            media_class = 'video' if self.content_data['media_type'] == 'video' else 'image'
            media_header_html = f'''
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

        # Content after media - USING TextFormatter NOW
        content_after_html = ''
        if self.content_data.get('content_after'):
            formatted_content = TextFormatter.format_text_content(self.content_data['content_after'])
            content_after_html = f'''
            <div class="media-content-after">
                {formatted_content}
            </div>'''

        # Handle max-width and max-height
        style_attrs = f"--media-max-width: {self.content_data['max_width']}"
        if self.content_data.get('max_height'):
            style_attrs += f"; --media-max-height: {self.content_data['max_height']}"

        # Combine all elements with card title at the top
        html_parts = []

        # Add card title first if it exists
        if card_title_html:
            html_parts.append(card_title_html.strip())

        if content_before_html:
            html_parts.append(content_before_html)

        html_parts.append(f'''
        <div class="media-container" style="{style_attrs}">
            {media_header_html}
            <div class="media-content">
                {media_html}
            </div>
            {caption_html}
        </div>''')

        if content_after_html:
            html_parts.append(content_after_html)

        return '\n'.join(html_parts)

    def get_property_fields(self) -> Dict[str, str]:
        return {
            'title': 'text',  # NEW: Card title field
            'media_type': 'dropdown:image,video',
            'source': 'file_or_url',
            'alt_text': 'text',
            'caption': 'textarea',
            'header': 'text',  # Media container header
            'content_before': 'textarea:formatted',  # Enable formatting toolbar
            'content_after': 'textarea:formatted',  # Enable formatting toolbar
            'max_width': 'text',
            'max_height': 'text',
            'clickable': 'checkbox'
        }

    def update_content(self, key: str, value: Any):
        """Update specific content field with path normalization and base64 validation"""
        if key == 'source':
            # Validate that we're not storing base64 data as a file path
            if value and self._is_base64_data(str(value)):
                print(f"⚠️ Warning: Attempting to set source to base64 data: '{str(value)[:20]}...'")
                print(f"⚠️ This may indicate a bug in the media handling code.")
                # For now, allow it but log it for debugging

            # Normalize file paths when they're updated (but not base64 data)
            if value and not self._is_base64_data(str(value)):
                self.content_data[key] = self._normalize_file_path(value)
            else:
                self.content_data[key] = value
        else:
            self.content_data[key] = value
