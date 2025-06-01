# utils/project_manager.py
import json
from pathlib import Path
from typing import Dict, Any, List
from modules.module_factory import ModuleFactory
from modules.base_module import Module
from modules.complex_module import TabModule


class ProjectManager:
    """Handle saving and loading SOP projects with TabModule support"""

    def __init__(self):
        self.project_extension = ".sopx"
        self.version = "1.1"  # Updated for TabModule support

    def save_project(self, file_path: Path, project_data: Dict[str, Any]):
        """Save project to file"""
        try:
            # Ensure file has correct extension
            if not str(file_path).endswith(self.project_extension):
                file_path = file_path.with_suffix(self.project_extension)

            # Save project
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, indent=2)

            return True

        except Exception as e:
            print(f"Error saving project: {e}")
            return False

    def load_project(self, file_path: str) -> Dict[str, Any]:
        """Load project from file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)

            # Validate version compatibility
            project_version = project_data.get('version', '1.0')
            if project_version not in ['1.0', '1.1']:
                print(f"Warning: Project version {project_version} may not be fully compatible.")

            return project_data

        except Exception as e:
            print(f"Error loading project: {e}")
            raise

    def serialize_module(self, module: Module) -> Dict[str, Any]:
        """Convert module to dictionary for saving"""
        return module.to_dict()

    def deserialize_module(self, module_data: Dict[str, Any]) -> Module:
        """Convert dictionary back to module instance with proper TabModule handling"""
        # Create module instance
        module_type = module_data['module_type']

        if module_type == 'tabs':
            # Special handling for TabModule
            module = self._deserialize_tab_module(module_data)
        else:
            # Standard module deserialization
            module = ModuleFactory.create_module(module_type)

            # Restore properties
            module.id = module_data['id']
            module.position = module_data['position']
            module.content_data = module_data['content_data']
            module.custom_styles = module_data.get('custom_styles', {})

        return module

    def _deserialize_tab_module(self, module_data: Dict[str, Any]) -> TabModule:
        """Deserialize a TabModule with its nested modules"""
        # Create the TabModule instance
        tab_module = ModuleFactory.create_module('tabs')

        # Restore basic properties
        tab_module.id = module_data['id']
        tab_module.position = module_data['position']
        tab_module.content_data = module_data['content_data']
        tab_module.custom_styles = module_data.get('custom_styles', {})
        tab_module.tab_ids = module_data.get('tab_ids', {})

        # Ensure tab_ids exist for all tabs
        for tab in tab_module.content_data['tabs']:
            if tab not in tab_module.tab_ids:
                import uuid
                tab_module.tab_ids[tab] = str(uuid.uuid4())

        # Deserialize sub-modules if they exist
        sub_modules_data = module_data.get('sub_modules', {})
        for tab_name, modules_data in sub_modules_data.items():
            tab_module.sub_modules[tab_name] = []
            for sub_module_data in modules_data:
                # Recursively deserialize nested modules
                sub_module = self.deserialize_module(sub_module_data)
                tab_module.sub_modules[tab_name].append(sub_module)

        return tab_module

    def create_backup(self, file_path: Path):
        """Create backup of existing project"""
        if file_path.exists():
            backup_path = file_path.with_suffix(f'.backup{self.project_extension}')
            try:
                import shutil
                shutil.copy2(file_path, backup_path)
                return backup_path
            except Exception as e:
                print(f"Error creating backup: {e}")
                return None

    def validate_project_data(self, project_data: Dict[str, Any]) -> bool:
        """Validate project data structure"""
        required_keys = ['version', 'modules']

        # Check required keys
        for key in required_keys:
            if key not in project_data:
                print(f"Missing required key: {key}")
                return False

        # Validate modules
        if not isinstance(project_data['modules'], list):
            print("Modules must be a list")
            return False

        for module in project_data['modules']:
            if not self._validate_module_data(module):
                return False

        return True

    def _validate_module_data(self, module_data: Dict[str, Any]) -> bool:
        """Validate individual module data"""
        required_keys = ['id', 'module_type', 'position', 'content_data']

        for key in required_keys:
            if key not in module_data:
                print(f"Module missing required key: {key}")
                return False

        # Additional validation for TabModule
        if module_data['module_type'] == 'tabs':
            # Validate TabModule structure
            if 'sub_modules' in module_data:
                sub_modules = module_data['sub_modules']
                if not isinstance(sub_modules, dict):
                    print("TabModule sub_modules must be a dictionary")
                    return False

                # Validate each tab's modules
                for tab_name, tab_modules in sub_modules.items():
                    if not isinstance(tab_modules, list):
                        print(f"Tab '{tab_name}' modules must be a list")
                        return False

                    for tab_module in tab_modules:
                        if not self._validate_module_data(tab_module):
                            return False

        return True

    def export_project_summary(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of the project structure"""
        summary = {
            'version': project_data.get('version'),
            'total_modules': len(project_data.get('modules', [])),
            'module_types': {},
            'tab_modules': []
        }

        for module_data in project_data.get('modules', []):
            module_type = module_data.get('module_type', 'unknown')
            summary['module_types'][module_type] = summary['module_types'].get(module_type, 0) + 1

            # Special handling for TabModule
            if module_type == 'tabs':
                tab_info = {
                    'id': module_data.get('id'),
                    'tabs': module_data.get('content_data', {}).get('tabs', []),
                    'nested_modules': {}
                }

                sub_modules = module_data.get('sub_modules', {})
                for tab_name, tab_modules in sub_modules.items():
                    tab_info['nested_modules'][tab_name] = len(tab_modules)

                summary['tab_modules'].append(tab_info)

        return summary
