# modules/issue_card_module.py
from modules.base_module import Module
from typing import Dict, Any, List
import re
import os


class IssueCardModule(Module):
    """Enhanced module for displaying issues/problems with solutions, supporting media and formatted text"""

    def __init__(self):
        super().__init__('issue_card', 'Issue Card')
        self.content_data = self.get_default_content()

    def get_default_content(self) -> Dict[str, Any]:
        return {
            'issue_title': 'Common Issue Title',
            'issue_description_before': 'Description of the issue or problem that occurs...',
            'issue_include_media': False,
            'issue_media_type': 'image',  # 'image' or 'video'
            'issue_media_source': '',
            'issue_media_caption': 'Description of the issue shown in the image',
            'issue_media_alt_text': 'Screenshot showing the issue',
            'issue_media_max_width': '545px',
            'issue_description_after': '',  # Optional text after media
            'solution_title': 'Solution:',
            'solution_content': 'Steps to resolve the issue:\n\n1. First step to fix the problem\n2. Second step if needed',
            'solution_include_media': False,
            'solution_media_type': 'single',  # 'single' or 'grid'
            'solution_single_media_source': '',
            'solution_single_media_caption': 'Example showing the solution',
            'solution_single_media_alt_text': 'Screenshot of the resolved state',
            'solution_media_items': [  # For grid layout
                {
                    'source': '',
                    'caption': 'Before: Problem state',
                    'alt_text': 'Screenshot showing the problem'
                },
                {
                    'source': '',
                    'caption': 'After: Solution applied',
                    'alt_text': 'Screenshot showing the solution'
                }
            ],
            'show_icon': True
        }

    def _normalize_file_path(self, file_path: str) -> str:
        """Convert Windows file paths to web-compatible relative paths"""
        if not file_path:
            return ''

        # Remove extra quotes if present
        cleaned_path = file_path.strip('"\'')

        # If it's a Windows absolute path, try to convert to relative
        if '\\' in cleaned_path and ':' in cleaned_path:
            filename = os.path.basename(cleaned_path)
            return f'Assets/{filename}'

        return cleaned_path

    def _format_text_content(self, text: str) -> str:
        """Format text content with bullets, numbers, and bold"""
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

    def _render_media_container(self, media_type: str, source: str, caption: str, 
                                alt_text: str, header: str, max_width: str = '545px') -> str:
        """Render a media container with proper styling"""
        if not source:
            return ''

        source = self._normalize_file_path(source)
        
        # Determine if clickable based on media type
        clickable = (media_type == 'image')
        
        media_html = ''
        if media_type == 'image':
            click_handler = 'onclick="openImageModal(this)"' if clickable else ''
            title_attr = 'title="Click to view full size"' if clickable else ''
            
            media_html = f'''
            <picture>
                <img 
                    src="{source}" 
                    alt="{alt_text}"
                    style="width: 100%; height: auto; max-height: 80vh; object-fit: contain;"
                    {click_handler}
                    {title_attr}
                >
            </picture>'''
        else:  # video
            media_html = f'''
            <iframe
                src="{source}"
                title="{alt_text}"
                allowfullscreen>
            </iframe>'''

        # Add click instruction for images
        click_instruction = ''
        if clickable:
            click_instruction = '\n<span style="color: var(--kodiak-red); font-size: 0.9em;">(Click image to view full size)</span>'

        return f'''
        <div class="media-container" style="--media-max-width: {max_width};">
            <div class="media-header">{header}</div>
            <div class="media-content">
                {media_html}
            </div>
            <div class="media-caption">
                {caption}{click_instruction}
            </div>
        </div>'''

    def _render_solution_media(self) -> str:
        """Render media in the solution section"""
        if not self.content_data.get('solution_include_media'):
            return ''

        if self.content_data.get('solution_media_type') == 'single':
            # Single media item
            source = self.content_data.get('solution_single_media_source', '')
            if source:
                return self._render_media_container(
                    'image',  # Solutions typically use images
                    source,
                    self.content_data.get('solution_single_media_caption', ''),
                    self.content_data.get('solution_single_media_alt_text', ''),
                    'Solution Example'
                )
        else:  # grid
            # Media grid for before/after or multiple examples
            media_items = self.content_data.get('solution_media_items', [])
            if not media_items or not any(item.get('source') for item in media_items):
                return ''

            grid_html = '<div class="media-grid side-by-side">'
            
            for item in media_items:
                source = item.get('source', '')
                if source:
                    source = self._normalize_file_path(source)
                    caption = item.get('caption', '')
                    alt_text = item.get('alt_text', '')
                    
                    grid_html += f'''
                    <div class="media-container" style="--media-max-width: 100%">
                        <div class="media-header">Solution Step</div>
                        <div class="media-content">
                            <img 
                                src="{source}"
                                alt="{alt_text}"
                                style="width: 100%; height: auto; object-fit: contain;"
                                onclick="openImageModal(this)"
                                title="Click to view full size"
                            >
                        </div>
                        <div class="media-caption">
                            {caption}
                            <span style="color: var(--kodiak-red); font-size: 0.9em;">(Click image to view full size)</span>
                        </div>
                    </div>'''
            
            grid_html += '</div>'
            return grid_html

        return ''

    def render_to_html(self) -> str:
        """Generate HTML for enhanced issue card"""
        # Issue title with optional icon
        icon_html = ''
        if self.content_data.get('show_icon'):
            icon_html = '⚠️ '

        title_html = f'<h4>{icon_html}{self.content_data["issue_title"]}</h4>'

        # Issue description before media
        description_before = ''
        if self.content_data.get('issue_description_before'):
            formatted_content = self._format_text_content(self.content_data['issue_description_before'])
            description_before = formatted_content

        # Issue media
        issue_media_html = ''
        if self.content_data.get('issue_include_media'):
            issue_media_html = self._render_media_container(
                self.content_data.get('issue_media_type', 'image'),
                self.content_data.get('issue_media_source', ''),
                self.content_data.get('issue_media_caption', ''),
                self.content_data.get('issue_media_alt_text', ''),
                'Related Screenshot',
                self.content_data.get('issue_media_max_width', '545px')
            )

        # Issue description after media
        description_after = ''
        if self.content_data.get('issue_description_after'):
            formatted_content = self._format_text_content(self.content_data['issue_description_after'])
            description_after = formatted_content

        # Solution section
        solution_title = self.content_data.get('solution_title', 'Solution:')
        solution_content = self._format_text_content(self.content_data.get('solution_content', ''))
        solution_media = self._render_solution_media()

        solution_html = f'''
        <div class="solution">
            <strong>{solution_title}</strong>
            {solution_content}
            {solution_media}
        </div>'''

        # Combine all parts
        return f'''
        <div class="issue-card">
            {title_html}
            {description_before}
            {issue_media_html}
            {description_after}
            {solution_html}
        </div>'''

    def get_property_fields(self) -> Dict[str, str]:
        return {
            'issue_title': 'text',
            'issue_description_before': 'textarea:formatted',
            'issue_include_media': 'checkbox',
            'issue_media_type': 'dropdown:image,video',
            'issue_media_source': 'file',
            'issue_media_caption': 'text',
            'issue_media_alt_text': 'text',
            'issue_media_max_width': 'text',
            'issue_description_after': 'textarea:formatted',
            'solution_title': 'text',
            'solution_content': 'textarea:formatted',
            'solution_include_media': 'checkbox',
            'solution_media_type': 'dropdown:single,grid',
            'solution_single_media_source': 'file',
            'solution_single_media_caption': 'text',
            'solution_single_media_alt_text': 'text',
            'solution_media_items': 'media_list_editor',
            'show_icon': 'checkbox'
        }

    def update_content(self, key: str, value: Any):
        """Update specific content field with path normalization"""
        if key in ['issue_media_source', 'solution_single_media_source']:
            # Normalize file paths when they're updated
            self.content_data[key] = self._normalize_file_path(value)
        else:
            self.content_data[key] = value
