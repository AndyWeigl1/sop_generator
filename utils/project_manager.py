# utils/project_manager.py
import json
from pathlib import Path
from typing import Dict, Any, List
from modules.module_factory import ModuleFactory
from modules.base_module import Module


class ProjectManager:
    """Handle saving and loading SOP projects"""

    def __init__(self):
        self.project_extension = ".sopx"
        self.version = "1.0"

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

            # Validate version
            if project_data.get('version') != self.version:
                print(f"Warning: Project version mismatch. Expected {self.version}, got {project_data.get('version')}")

            return project_data

        except Exception as e:
            print(f"Error loading project: {e}")
            raise

    def serialize_module(self, module: Module) -> Dict[str, Any]:
        """Convert module to dictionary for saving"""
        return module.to_dict()

    def deserialize_module(self, module_data: Dict[str, Any]) -> Module:
        """Convert dictionary back to module instance"""
        # Create module instance
        module_type = module_data['module_type']
        module = ModuleFactory.create_module(module_type)

        # Restore properties
        module.id = module_data['id']
        module.position = module_data['position']
        module.content_data = module_data['content_data']
        module.custom_styles = module_data.get('custom_styles', {})

        return module

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

        return True