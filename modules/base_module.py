# modules/base_module.py - Updated for better live preview path handling
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import uuid
import os


class Module(ABC):
    """Abstract base class for all content modules"""

    def __init__(self, module_type: str, display_name: str):
        self.id = str(uuid.uuid4())
        self.module_type = module_type
        self.display_name = display_name
        self.position = 0  # Order in the SOP
        self.content_data = {}
        self.custom_styles = {}

    @abstractmethod
    def get_default_content(self) -> Dict[str, Any]:
        """Return default content structure for this module"""
        pass

    @abstractmethod
    def render_to_html(self) -> str:
        """Convert module content to HTML string"""
        pass

    def _normalize_media_path(self, file_path: str) -> str:
        """
        Normalize file path for consistent mapping lookup
        MUST match MediaDiscoveryService._normalize_path
        """
        if not file_path:
            return ''

        # Remove quotes and extra whitespace
        cleaned_path = file_path.strip().strip('"\'')

        # Convert to Path object for normalization
        from pathlib import Path
        path_obj = Path(cleaned_path)

        # Return absolute path with consistent separator
        if path_obj.exists():
            # Convert to absolute path and ensure consistent separators
            abs_path = str(path_obj.resolve())
            # Always use forward slashes for consistency
            return abs_path.replace('\\', '/')
        else:
            # For non-existent files, still normalize the format
            return str(Path(cleaned_path)).replace('\\', '/')

    @abstractmethod
    def get_property_fields(self) -> Dict[str, str]:
        """Return fields that can be edited in properties panel"""
        pass

    def update_media_references(self, path_mapping: Dict[str, str]):
        """
        Update all media paths in this module using the provided mapping

        This is a default implementation that does nothing.
        Modules with media content should override this method.

        Args:
            path_mapping: Dictionary mapping original file paths to new paths (usually base64 data URLs or file URIs)
        """
        pass

    def get_media_references(self) -> List[str]:
        """
        Return all media file paths used by this module

        This is a default implementation that returns an empty list.
        Modules with media content should override this method.

        Returns:
            List of media file paths (empty by default)
        """
        return []

    def _find_matching_path_in_mapping(self, file_path: str, path_mapping: Dict[str, str]) -> Optional[str]:
        """
        Find a matching path in the mapping, trying multiple strategies

        Args:
            file_path: Original file path to find
            path_mapping: Available path mappings

        Returns:
            Mapped value if found, None otherwise
        """
        if not file_path or not path_mapping:
            return None

        # Strategy 1: Exact match
        if file_path in path_mapping:
            return path_mapping[file_path]

        # Strategy 2: Try with normalized slashes
        normalized_path = file_path.replace('\\', '/')
        if normalized_path in path_mapping:
            return path_mapping[normalized_path]

        # Strategy 3: Try case-insensitive match for the filename part
        file_name = os.path.basename(file_path).lower()
        for mapping_key, mapping_value in path_mapping.items():
            if os.path.basename(mapping_key).lower() == file_name:
                return mapping_value

        return None

    def update_content(self, key: str, value: Any):
        """Update specific content field"""
        self.content_data[key] = value

    def to_dict(self) -> Dict[str, Any]:
        """Serialize module to dictionary for saving"""
        return {
            'id': self.id,
            'module_type': self.module_type,
            'position': self.position,
            'content_data': self.content_data,
            'custom_styles': self.custom_styles
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Deserialize module from dictionary"""
        # Implementation would vary by subclass
        pass
