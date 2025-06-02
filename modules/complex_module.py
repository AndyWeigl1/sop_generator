# modules/complex_module.py
from modules.base_module import Module
from typing import Dict, Any, List, Optional
import uuid


class TabModule(Module):
    """Module for tabbed content sections with full nested module support"""

    def __init__(self):
        super().__init__('tabs', 'Tab Section')
        self.content_data = self.get_default_content()
        self.sub_modules: Dict[str, List[Module]] = {}  # Tab name -> modules
        self.tab_ids: Dict[str, str] = {}  # Tab name -> unique ID for persistence

    def get_default_content(self) -> Dict[str, Any]:
        return {
            'tabs': ['Instructions', 'Common Issues'],  # Default tab names
            'active_tab': 0
        }

    def add_tab(self, tab_name: str) -> str:
        """Add a new tab and return its ID"""
        if tab_name not in self.content_data['tabs']:
            self.content_data['tabs'].append(tab_name)
            tab_id = str(uuid.uuid4())
            self.tab_ids[tab_name] = tab_id
            self.sub_modules[tab_name] = []
            return tab_id
        return self.tab_ids.get(tab_name, '')

    def remove_tab(self, tab_name: str):
        """Remove a tab and all its modules"""
        if tab_name in self.content_data['tabs'] and len(self.content_data['tabs']) > 1:
            self.content_data['tabs'].remove(tab_name)
            if tab_name in self.sub_modules:
                del self.sub_modules[tab_name]
            if tab_name in self.tab_ids:
                del self.tab_ids[tab_name]
            # Reset active tab if needed
            if self.content_data['active_tab'] >= len(self.content_data['tabs']):
                self.content_data['active_tab'] = 0

    def rename_tab(self, old_name: str, new_name: str):
        """Rename a tab"""
        if old_name in self.content_data['tabs'] and new_name not in self.content_data['tabs']:
            idx = self.content_data['tabs'].index(old_name)
            self.content_data['tabs'][idx] = new_name
            # Move sub-modules
            if old_name in self.sub_modules:
                self.sub_modules[new_name] = self.sub_modules.pop(old_name)
            # Move tab ID
            if old_name in self.tab_ids:
                self.tab_ids[new_name] = self.tab_ids.pop(old_name)

    def add_module_to_tab(self, tab_name: str, module: Module) -> bool:
        """Add a module to a specific tab"""
        if tab_name not in self.content_data['tabs']:
            return False

        if tab_name not in self.sub_modules:
            self.sub_modules[tab_name] = []

        # Set module position within the tab
        module.position = len(self.sub_modules[tab_name])
        self.sub_modules[tab_name].append(module)
        return True

    def remove_module_from_tab(self, tab_name: str, module_id: str) -> Optional[Module]:
        """Remove a module from a tab and return it"""
        if tab_name in self.sub_modules:
            for i, module in enumerate(self.sub_modules[tab_name]):
                if module.id == module_id:
                    removed_module = self.sub_modules[tab_name].pop(i)
                    # Update positions
                    for j, m in enumerate(self.sub_modules[tab_name]):
                        m.position = j
                    return removed_module
        return None

    def get_all_nested_modules(self) -> List[Module]:
        """Get all modules from all tabs"""
        all_modules = []
        for tab_modules in self.sub_modules.values():
            all_modules.extend(tab_modules)
        return all_modules

    def find_module_tab(self, module_id: str) -> Optional[str]:
        """Find which tab contains a specific module"""
        for tab_name, modules in self.sub_modules.items():
            for module in modules:
                if module.id == module_id:
                    return tab_name
        return None

    def reorder_module_in_tab(self, tab_name: str, module_id: str, new_position: int):
        """Reorder a module within its tab"""
        if tab_name in self.sub_modules:
            modules = self.sub_modules[tab_name]
            # Find the module
            module_index = None
            for i, module in enumerate(modules):
                if module.id == module_id:
                    module_index = i
                    break

            if module_index is not None and 0 <= new_position < len(modules):
                module = modules.pop(module_index)
                modules.insert(new_position, module)
                # Update all positions
                for i, m in enumerate(modules):
                    m.position = i

    def render_to_html(self) -> str:
        """Generate HTML for tabbed content - simplified version for use with HTML generator"""
        # Ensure sub_modules exist for all tabs
        for tab in self.content_data['tabs']:
            if tab not in self.sub_modules:
                self.sub_modules[tab] = []

        # Generate tab buttons
        tab_buttons = ''
        for i, tab in enumerate(self.content_data['tabs']):
            active_class = 'active' if i == self.content_data['active_tab'] else ''
            tab_buttons += f'<button class="tab {active_class}">{tab}</button>\n'

        # Start building the HTML
        html = f'''
    <div class="tabs">
        {tab_buttons}
    </div>'''

        # Generate ALL section-content divs for ALL tabs
        for i, tab in enumerate(self.content_data['tabs']):
            active_class = 'active' if i == self.content_data['active_tab'] else ''

            # Get content for this tab - simple version without cards
            content = ''
            if tab in self.sub_modules:
                sorted_modules = sorted(self.sub_modules[tab], key=lambda m: m.position)
                for module in sorted_modules:
                    content += module.render_to_html()

            # If no content, show placeholder
            if not content:
                content = '<p style="color: gray; text-align: center;">No content in this tab yet.</p>'

            # Add the section-content div
            html += f'''
    <div class="section-content {active_class}">
        {content}
    </div>'''

        return html

    def get_property_fields(self) -> Dict[str, str]:
        return {
            'tabs': 'tab_list_editor',  # Custom editor for tab management
            'active_tab': 'number'
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serialize module to dictionary including sub-modules"""
        base_dict = super().to_dict()

        # Serialize sub-modules
        sub_modules_data = {}
        for tab_name, modules in self.sub_modules.items():
            sub_modules_data[tab_name] = [m.to_dict() for m in modules]

        base_dict['sub_modules'] = sub_modules_data
        base_dict['tab_ids'] = self.tab_ids
        return base_dict

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Deserialize module from dictionary including sub-modules"""
        # Note: This method is not used in the current implementation
        # as deserialization is handled by ProjectManager
        module = cls()
        module.id = data['id']
        module.position = data['position']
        module.content_data = data['content_data']
        module.custom_styles = data.get('custom_styles', {})
        module.tab_ids = data.get('tab_ids', {})

        # Ensure tab_ids exist for all tabs
        for tab in module.content_data['tabs']:
            if tab not in module.tab_ids:
                module.tab_ids[tab] = str(uuid.uuid4())

        return module

    def get_module_count_by_tab(self) -> Dict[str, int]:
        """Get the number of modules in each tab"""
        counts = {}
        for tab_name in self.content_data['tabs']:
            counts[tab_name] = len(self.sub_modules.get(tab_name, []))
        return counts

    def move_module_between_tabs(self, module_id: str, from_tab: str, to_tab: str) -> bool:
        """Move a module from one tab to another within this TabModule"""
        removed_module = self.remove_module_from_tab(from_tab, module_id)
        if removed_module and self.add_module_to_tab(to_tab, removed_module):
            return True
        return False

    def get_media_references(self) -> List[str]:
        """
        Return all media file paths used by this module and its nested modules

        TabModule itself has no media, but its nested modules might
        """
        media_refs = []

        # Collect media references from all nested modules
        for tab_name, nested_modules in self.sub_modules.items():
            for nested_module in nested_modules:
                if hasattr(nested_module, 'get_media_references'):
                    nested_refs = nested_module.get_media_references()
                    media_refs.extend(nested_refs)

        return media_refs

    def update_media_references(self, path_mapping: Dict[str, str]):
        """
        Update all media paths in nested modules using the provided mapping

        TabModule itself has no media, but its nested modules might
        """
        # Update media references in all nested modules
        for tab_name, nested_modules in self.sub_modules.items():
            for nested_module in nested_modules:
                if hasattr(nested_module, 'update_media_references'):
                    nested_module.update_media_references(path_mapping)

    def validate_tab_structure(self) -> bool:
        """Validate the internal consistency of the tab structure"""
        # Check that all tabs in content_data have corresponding entries
        for tab_name in self.content_data['tabs']:
            if tab_name not in self.sub_modules:
                self.sub_modules[tab_name] = []
            if tab_name not in self.tab_ids:
                self.tab_ids[tab_name] = str(uuid.uuid4())

        # Check that sub_modules and tab_ids don't have extra entries
        valid_tabs = set(self.content_data['tabs'])

        # Remove orphaned sub_modules
        orphaned_sub_modules = set(self.sub_modules.keys()) - valid_tabs
        for orphan in orphaned_sub_modules:
            del self.sub_modules[orphan]

        # Remove orphaned tab_ids
        orphaned_tab_ids = set(self.tab_ids.keys()) - valid_tabs
        for orphan in orphaned_tab_ids:
            del self.tab_ids[orphan]

        return True
