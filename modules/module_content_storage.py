from typing import Dict, Any, List


# Data structure for module content storage
class ModuleContent:
    """Flexible content storage for modules"""

    def __init__(self):
        self.text_content: Dict[str, str] = {}
        self.media_content: Dict[str, Any] = {}
        self.list_content: Dict[str, List[str]] = {}
        self.table_content: Dict[str, List[List[str]]] = {}
        self.metadata: Dict[str, Any] = {}

    def set_text(self, key: str, value: str):
        self.text_content[key] = value

    def set_media(self, key: str, path: str, media_type: str = 'image'):
        self.media_content[key] = {
            'path': path,
            'type': media_type,
            'embedded': False  # Will be set to True when embedding in HTML
        }

    def set_list(self, key: str, items: List[str]):
        self.list_content[key] = items

    def set_table(self, key: str, data: List[List[str]]):
        self.table_content[key] = data

    def to_dict(self) -> Dict[str, Any]:
        return {
            'text': self.text_content,
            'media': self.media_content,
            'lists': self.list_content,
            'tables': self.table_content,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        content = cls()
        content.text_content = data.get('text', {})
        content.media_content = data.get('media', {})
        content.list_content = data.get('lists', {})
        content.table_content = data.get('tables', {})
        content.metadata = data.get('metadata', {})
        return content