from modules.base_module import Module
from typing import Dict, Any, List

# modules/complex_modules.py
class TabModule(Module):
    """Module for tabbed content sections"""

    def __init__(self):
        super().__init__('tabs', 'Tab Section')
        self.content_data = self.get_default_content()
        self.sub_modules: Dict[str, List[Module]] = {}  # Tab name -> modules

    def get_default_content(self) -> Dict[str, Any]:
        return {
            'tabs': ['Tab 1', 'Tab 2'],  # Tab names
            'active_tab': 0
        }

    def add_tab(self, tab_name: str):
        """Add a new tab"""
        self.content_data['tabs'].append(tab_name)
        self.sub_modules[tab_name] = []

    def add_module_to_tab(self, tab_name: str, module: Module):
        """Add a module to a specific tab"""
        if tab_name not in self.sub_modules:
            self.sub_modules[tab_name] = []
        self.sub_modules[tab_name].append(module)

    def render_to_html(self) -> str:
        """Generate HTML for tabbed content"""
        # Generate tab buttons
        tab_buttons = ''
        for i, tab in enumerate(self.content_data['tabs']):
            active_class = 'active' if i == self.content_data['active_tab'] else ''
            tab_buttons += f'<button class="tab {active_class}">{tab}</button>\n'

        # Generate tab content
        tab_contents = ''
        for i, tab in enumerate(self.content_data['tabs']):
            active_class = 'active' if i == self.content_data['active_tab'] else ''
            content = ''

            # Render sub-modules for this tab
            if tab in self.sub_modules:
                for module in self.sub_modules[tab]:
                    content += module.render_to_html()

            tab_contents += f'''
            <div class="section-content {active_class}">
                {content}
            </div>'''

        return f'''
        <div class="tabs">
            {tab_buttons}
        </div>
        {tab_contents}'''

    def get_property_fields(self) -> Dict[str, str]:
        return {
            'tabs': 'list_editor',
            'active_tab': 'number'
        }