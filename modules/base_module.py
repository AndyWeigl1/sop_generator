# modules/base_module.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import uuid


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

    @abstractmethod
    def get_property_fields(self) -> Dict[str, str]:
        """Return fields that can be edited in properties panel"""
        pass

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
