# utils/base64_embedder.py
"""
Base64 Embedding Service

Handles conversion of media files to base64 data URLs for embedding in HTML files.
Provides batch processing capabilities with progress tracking and error handling.
"""

import base64
import mimetypes
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Callable, Any
import time


class Base64EmbedderService:
    """Service for converting media files to base64 data URLs"""

    def __init__(self):
        self.conversion_cache: Dict[str, str] = {}
        self.error_log: List[Dict[str, str]] = []

    def embed_file_to_base64(self, file_path: str, use_cache: bool = True) -> str:
        """
        Convert a single file to base64 data URL

        Args:
            file_path: Path to the file to convert
            use_cache: Whether to use cached results for repeated conversions

        Returns:
            Base64 data URL string, or empty string if conversion fails

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file type is not supported
            IOError: If file cannot be read
        """
        # Normalize the path
        normalized_path = str(Path(file_path).resolve())

        # Check cache first
        if use_cache and normalized_path in self.conversion_cache:
            return self.conversion_cache[normalized_path]

        try:
            # Validate file exists
            path_obj = Path(file_path)
            if not path_obj.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            # Get MIME type
            mime_type = self._get_mime_type(path_obj)
            if not mime_type:
                raise ValueError(f"Unsupported file type: {path_obj.suffix}")

            # Read and encode file
            with open(path_obj, 'rb') as file:
                file_data = file.read()

            # Encode to base64
            base64_data = base64.b64encode(file_data).decode('utf-8')

            # Create data URL
            data_url = f"data:{mime_type};base64,{base64_data}"

            # Cache the result
            if use_cache:
                self.conversion_cache[normalized_path] = data_url

            return data_url

        except Exception as e:
            error_info = {
                'file_path': file_path,
                'error': str(e),
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            self.error_log.append(error_info)
            print(f"Error embedding file {file_path}: {e}")
            return ""

    def embed_multiple_files(self, file_paths: List[str],
                             progress_callback: Optional[Callable[[int, int, str], None]] = None,
                             use_cache: bool = True) -> Dict[str, str]:
        """
        Convert multiple files to base64 data URLs with progress tracking

        Args:
            file_paths: List of file paths to convert
            progress_callback: Optional callback function(current, total, current_file)
            use_cache: Whether to use cached results

        Returns:
            Dictionary mapping original file paths to data URLs
            Files that fail conversion will have empty string values
        """
        results = {}
        total_files = len(file_paths)

        for i, file_path in enumerate(file_paths):
            # Update progress
            if progress_callback:
                progress_callback(i + 1, total_files, file_path)

            # Convert file
            try:
                data_url = self.embed_file_to_base64(file_path, use_cache)
                results[file_path] = data_url
            except Exception as e:
                print(f"Failed to embed {file_path}: {e}")
                results[file_path] = ""

        return results

    def validate_file_for_embedding(self, file_path: str) -> Tuple[bool, str]:
        """
        Check if a file can and should be embedded

        Args:
            file_path: Path to the file to check

        Returns:
            Tuple of (can_embed, reason)
            If can_embed is False, reason contains the explanation
        """
        try:
            path_obj = Path(file_path)

            # Check if file exists
            if not path_obj.exists():
                return False, f"File not found: {file_path}"

            # Check file size (50MB limit)
            file_size = path_obj.stat().st_size
            max_size = 50 * 1024 * 1024  # 50MB
            if file_size > max_size:
                size_mb = file_size / (1024 * 1024)
                return False, f"File too large: {size_mb:.1f}MB (limit: 50MB)"

            # Check if we can determine MIME type
            mime_type = self._get_mime_type(path_obj)
            if not mime_type:
                return False, f"Unsupported file type: {path_obj.suffix}"

            # Check if file is readable
            try:
                with open(path_obj, 'rb') as f:
                    f.read(1)  # Try to read first byte
            except Exception as e:
                return False, f"Cannot read file: {str(e)}"

            return True, "File is suitable for embedding"

        except Exception as e:
            return False, f"Error validating file: {str(e)}"

    def _get_mime_type(self, file_path: Path) -> Optional[str]:
        """
        Determine MIME type for a file based on extension

        Args:
            file_path: Path object for the file

        Returns:
            MIME type string or None if unsupported
        """
        suffix = file_path.suffix.lower()

        # Comprehensive MIME type mapping for embedding
        mime_map = {
            # Images
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.svg': 'image/svg+xml',
            '.bmp': 'image/bmp',
            '.ico': 'image/x-icon',
            '.tiff': 'image/tiff',
            '.tif': 'image/tiff',

            # Videos
            '.mp4': 'video/mp4',
            '.webm': 'video/webm',
            '.avi': 'video/x-msvideo',
            '.mov': 'video/quicktime',
            '.wmv': 'video/x-ms-wmv',
            '.flv': 'video/x-flv',
            '.mkv': 'video/x-matroska',

            # Audio
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.ogg': 'audio/ogg',
            '.aac': 'audio/aac',
            '.flac': 'audio/flac',

            # Fonts
            '.otf': 'font/otf',
            '.ttf': 'font/ttf',
            '.woff': 'font/woff',
            '.woff2': 'font/woff2',
            '.eot': 'application/vnd.ms-fontobject',

            # Documents (less common for embedding but supported)
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',

            # Archives
            '.zip': 'application/zip',
            '.rar': 'application/x-rar-compressed',
            '.7z': 'application/x-7z-compressed'
        }

        if suffix in mime_map:
            return mime_map[suffix]

        # Fallback to Python's mimetypes module
        mime_type, _ = mimetypes.guess_type(str(file_path))
        return mime_type

    def estimate_conversion_time(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        Estimate time required for batch conversion

        Args:
            file_paths: List of files to convert

        Returns:
            Dictionary with time estimates and file statistics
        """
        total_size = 0
        file_count = len(file_paths)
        large_files = 0

        for file_path in file_paths:
            try:
                path_obj = Path(file_path)
                if path_obj.exists():
                    size = path_obj.stat().st_size
                    total_size += size

                    # Count large files (>10MB)
                    if size > 10 * 1024 * 1024:
                        large_files += 1

            except Exception:
                continue

        # Rough estimation: ~5MB/second for base64 conversion
        # This varies greatly by system, but gives a ballpark
        estimated_seconds = total_size / (5 * 1024 * 1024)

        return {
            'total_files': file_count,
            'total_size_mb': total_size / (1024 * 1024),
            'large_files': large_files,
            'estimated_seconds': max(1, int(estimated_seconds)),
            'estimated_minutes': max(0.1, estimated_seconds / 60)
        }

    def clear_cache(self):
        """Clear the conversion cache"""
        self.conversion_cache.clear()

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the conversion cache

        Returns:
            Dictionary with cache statistics
        """
        cache_size = len(self.conversion_cache)
        total_data_size = sum(len(data) for data in self.conversion_cache.values())

        return {
            'cached_files': cache_size,
            'cache_data_size_mb': total_data_size / (1024 * 1024),
            'average_data_url_size_kb': (total_data_size / cache_size / 1024) if cache_size > 0 else 0
        }

    def get_error_log(self) -> List[Dict[str, str]]:
        """
        Get log of conversion errors

        Returns:
            List of error dictionaries
        """
        return self.error_log.copy()

    def clear_error_log(self):
        """Clear the error log"""
        self.error_log.clear()

    def create_data_url(self, data: bytes, mime_type: str) -> str:
        """
        Create a data URL from raw bytes and MIME type

        Args:
            data: Raw file data
            mime_type: MIME type of the data

        Returns:
            Data URL string
        """
        base64_data = base64.b64encode(data).decode('utf-8')
        return f"data:{mime_type};base64,{base64_data}"

    def extract_data_from_url(self, data_url: str) -> Tuple[bytes, str]:
        """
        Extract raw data and MIME type from a data URL

        Args:
            data_url: Data URL string

        Returns:
            Tuple of (raw_data, mime_type)

        Raises:
            ValueError: If data URL format is invalid
        """
        if not data_url.startswith('data:'):
            raise ValueError("Invalid data URL format")

        try:
            # Split the data URL
            header, data = data_url.split(',', 1)

            # Extract MIME type
            mime_part = header[5:]  # Remove 'data:'
            if ';base64' in mime_part:
                mime_type = mime_part.replace(';base64', '')
            else:
                raise ValueError("Only base64 encoded data URLs are supported")

            # Decode base64 data
            raw_data = base64.b64decode(data)

            return raw_data, mime_type

        except Exception as e:
            raise ValueError(f"Error parsing data URL: {str(e)}")

    def optimize_for_web(self, file_path: str, max_width: Optional[int] = None,
                         quality: Optional[int] = None) -> str:
        """
        Optimize an image for web embedding (future enhancement)

        Args:
            file_path: Path to image file
            max_width: Maximum width for resizing
            quality: JPEG quality (1-100)

        Returns:
            Base64 data URL of optimized image

        Note: This is a placeholder for future image optimization features
        """
        # For now, just embed as-is
        # Future: Add PIL/Pillow integration for image optimization
        return self.embed_file_to_base64(file_path)