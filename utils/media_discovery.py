# utils/media_discovery.py
"""
Media Discovery Service

Scans modules and discovers all media file references, provides file information
and size estimation for base64 embedding decisions.
"""

import os
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass
from modules.base_module import Module
from modules.complex_module import TabModule


@dataclass
class MediaInfo:
    """Information about a media file"""
    file_path: str
    file_size: int
    mime_type: str
    exists: bool
    is_valid: bool
    error_message: Optional[str] = None
    base64_size_estimate: int = 0  # Estimated size after base64 encoding


class MediaDiscoveryService:
    """Service to discover and analyze media files used in SOP modules"""

    # Supported media types for embedding
    SUPPORTED_IMAGE_TYPES = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp'}
    SUPPORTED_VIDEO_TYPES = {'.mp4', '.webm', '.avi', '.mov'}
    SUPPORTED_FONT_TYPES = {'.otf', '.ttf', '.woff', '.woff2'}
    SUPPORTED_AUDIO_TYPES = {'.mp3', '.wav', '.ogg'}

    # Size thresholds (in bytes)
    SINGLE_FILE_WARNING_SIZE = 10 * 1024 * 1024  # 10MB
    SINGLE_FILE_LIMIT_SIZE = 50 * 1024 * 1024  # 50MB
    TOTAL_SIZE_WARNING = 100 * 1024 * 1024  # 100MB
    TOTAL_SIZE_LIMIT = 500 * 1024 * 1024  # 500MB

    def __init__(self):
        self.discovered_media: Dict[str, MediaInfo] = {}

    def discover_all_media(self, modules: List[Module]) -> Dict[str, MediaInfo]:
        """
        Scan all modules and discover media file references

        Args:
            modules: List of modules to scan

        Returns:
            Dictionary mapping file paths to MediaInfo objects
        """
        self.discovered_media.clear()
        media_paths = set()

        # Discover media from all modules
        for module in modules:
            module_media = self._discover_module_media(module)
            media_paths.update(module_media)

        # Get detailed info for each discovered media file
        for media_path in media_paths:
            if media_path and media_path.strip():  # Skip empty paths
                self.discovered_media[media_path] = self.get_media_info(media_path)

        return self.discovered_media

    def _discover_module_media(self, module: Module) -> Set[str]:
        """
        Discover media files from a specific module

        Args:
            module: Module to scan

        Returns:
            Set of media file paths found in the module
        """
        media_paths = set()

        # Handle different module types
        if module.module_type == 'media':
            source = module.content_data.get('source', '')
            if source:
                media_paths.add(self._normalize_path(source))

        elif module.module_type == 'media_grid':
            items = module.content_data.get('items', [])
            for item in items:
                if isinstance(item, dict):
                    source = item.get('source', '')
                    if source:
                        media_paths.add(self._normalize_path(source))

        elif module.module_type == 'issue_card':
            # Issue media
            issue_source = module.content_data.get('issue_media_source', '')
            if issue_source:
                media_paths.add(self._normalize_path(issue_source))

            # Solution single media
            solution_source = module.content_data.get('solution_single_media_source', '')
            if solution_source:
                media_paths.add(self._normalize_path(solution_source))

            # Solution media items (grid)
            solution_items = module.content_data.get('solution_media_items', [])
            for item in solution_items:
                if isinstance(item, dict):
                    source = item.get('source', '')
                    if source:
                        media_paths.add(self._normalize_path(source))

        elif module.module_type == 'header':
            logo_path = module.content_data.get('logo_path', '')
            if logo_path:
                media_paths.add(self._normalize_path(logo_path))

        elif module.module_type == 'footer':
            bg_image = module.content_data.get('background_image', '')
            if bg_image:
                media_paths.add(self._normalize_path(bg_image))

        # Handle TabModule with nested modules
        if isinstance(module, TabModule):
            for tab_name, tab_modules in module.sub_modules.items():
                for nested_module in tab_modules:
                    nested_media = self._discover_module_media(nested_module)
                    media_paths.update(nested_media)

        return media_paths

    def _normalize_path(self, file_path: str) -> str:
        """
        Normalize file path for consistent handling

        Args:
            file_path: Raw file path from module

        Returns:
            Normalized file path
        """
        if not file_path:
            return ''

        # Remove quotes and extra whitespace
        cleaned_path = file_path.strip().strip('"\'')

        # Convert to Path object for normalization
        path_obj = Path(cleaned_path)

        # Return absolute path if it exists, otherwise return as-is
        if path_obj.exists():
            return str(path_obj.resolve())
        else:
            return cleaned_path

    def get_media_info(self, file_path: str) -> MediaInfo:
        """
        Get detailed information about a media file

        Args:
            file_path: Path to the media file

        Returns:
            MediaInfo object with file details
        """
        # Initialize with basic info
        media_info = MediaInfo(
            file_path=file_path,
            file_size=0,
            mime_type='',
            exists=False,
            is_valid=False
        )

        try:
            path_obj = Path(file_path)

            # Check if file exists
            if not path_obj.exists():
                media_info.error_message = f"File not found: {file_path}"
                return media_info

            media_info.exists = True

            # Get file size
            media_info.file_size = path_obj.stat().st_size

            # Estimate base64 size (base64 encoding increases size by ~33%)
            media_info.base64_size_estimate = int(media_info.file_size * 1.37)

            # Determine MIME type
            media_info.mime_type = self._get_mime_type(path_obj)

            # Validate file type and size
            media_info.is_valid, error_msg = self._validate_file(path_obj, media_info.file_size)
            if error_msg:
                media_info.error_message = error_msg

        except Exception as e:
            media_info.error_message = f"Error analyzing file {file_path}: {str(e)}"

        return media_info

    def _get_mime_type(self, file_path: Path) -> str:
        """
        Determine MIME type for a file

        Args:
            file_path: Path object for the file

        Returns:
            MIME type string
        """
        import mimetypes

        suffix = file_path.suffix.lower()

        # Common mappings for embedding
        mime_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.svg': 'image/svg+xml',
            '.bmp': 'image/bmp',
            '.mp4': 'video/mp4',
            '.webm': 'video/webm',
            '.avi': 'video/x-msvideo',
            '.mov': 'video/quicktime',
            '.otf': 'font/otf',
            '.ttf': 'font/ttf',
            '.woff': 'font/woff',
            '.woff2': 'font/woff2',
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.ogg': 'audio/ogg'
        }

        if suffix in mime_map:
            return mime_map[suffix]

        # Fallback to mimetypes module
        mime_type, _ = mimetypes.guess_type(str(file_path))
        return mime_type or 'application/octet-stream'

    def _validate_file(self, file_path: Path, file_size: int) -> Tuple[bool, Optional[str]]:
        """
        Validate if file is suitable for embedding

        Args:
            file_path: Path to the file
            file_size: Size of the file in bytes

        Returns:
            Tuple of (is_valid, error_message)
        """
        suffix = file_path.suffix.lower()

        # Check if file type is supported
        if suffix not in (self.SUPPORTED_IMAGE_TYPES |
                          self.SUPPORTED_VIDEO_TYPES |
                          self.SUPPORTED_FONT_TYPES |
                          self.SUPPORTED_AUDIO_TYPES):
            return False, f"Unsupported file type: {suffix}"

        # Check file size limits
        if file_size > self.SINGLE_FILE_LIMIT_SIZE:
            size_mb = file_size / (1024 * 1024)
            return False, f"File too large for embedding: {size_mb:.1f}MB (limit: {self.SINGLE_FILE_LIMIT_SIZE / (1024 * 1024):.0f}MB)"

        # Check if file is readable
        try:
            with open(file_path, 'rb') as f:
                f.read(1)  # Try to read first byte
        except Exception as e:
            return False, f"Cannot read file: {str(e)}"

        return True, None

    def estimate_embedded_size(self, media_dict: Optional[Dict[str, MediaInfo]] = None) -> Dict[str, Any]:
        """
        Calculate size estimations for embedding

        Args:
            media_dict: Optional specific media dict, uses discovered_media if None

        Returns:
            Dictionary with size statistics
        """
        if media_dict is None:
            media_dict = self.discovered_media

        total_original_size = 0
        total_embedded_size = 0
        valid_files = 0
        invalid_files = 0
        large_files = []

        for file_path, media_info in media_dict.items():
            if media_info.is_valid and media_info.exists:
                total_original_size += media_info.file_size
                total_embedded_size += media_info.base64_size_estimate
                valid_files += 1

                # Track large files
                if media_info.file_size > self.SINGLE_FILE_WARNING_SIZE:
                    large_files.append({
                        'path': file_path,
                        'size': media_info.file_size,
                        'size_mb': media_info.file_size / (1024 * 1024)
                    })
            else:
                invalid_files += 1

        return {
            'total_files': len(media_dict),
            'valid_files': valid_files,
            'invalid_files': invalid_files,
            'total_original_size': total_original_size,
            'total_embedded_size': total_embedded_size,
            'total_original_size_mb': total_original_size / (1024 * 1024),
            'total_embedded_size_mb': total_embedded_size / (1024 * 1024),
            'size_increase': total_embedded_size - total_original_size,
            'size_increase_percent': ((
                                                  total_embedded_size - total_original_size) / total_original_size * 100) if total_original_size > 0 else 0,
            'large_files': large_files,
            'exceeds_warning_threshold': total_embedded_size > self.TOTAL_SIZE_WARNING,
            'exceeds_size_limit': total_embedded_size > self.TOTAL_SIZE_LIMIT
        }

    def get_embeddable_files(self) -> Dict[str, MediaInfo]:
        """
        Get only the files that can be safely embedded

        Returns:
            Dictionary of files suitable for embedding
        """
        return {
            path: info for path, info in self.discovered_media.items()
            if info.is_valid and info.exists
        }

    def get_problematic_files(self) -> Dict[str, MediaInfo]:
        """
        Get files that cannot be embedded

        Returns:
            Dictionary of problematic files with error details
        """
        return {
            path: info for path, info in self.discovered_media.items()
            if not info.is_valid or not info.exists
        }