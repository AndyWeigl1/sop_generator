# utils/module_content_updater.py
"""
Module Content Updater

Handles updating module content for export, specifically managing media file paths
and their conversion to base64 data URLs. Creates temporary copies of modules
for export processing while preserving original data.
"""

import copy
from typing import Dict, List, Optional, Set
from modules.base_module import Module
from modules.complex_module import TabModule


class ModuleContentUpdater:
    """Manages module content updates for export processing"""

    def __init__(self):
        self.original_modules: List[Module] = []
        self.updated_modules: List[Module] = []
        self.path_mappings: Dict[str, str] = {}

    def create_modules_copy_for_export(self, modules: List[Module]) -> List[Module]:
        """
        Create deep copies of modules for export processing

        Args:
            modules: Original modules list

        Returns:
            Deep copied modules list safe for modification
        """
        self.original_modules = modules
        self.updated_modules = []

        for module in modules:
            copied_module = self._deep_copy_module(module)
            self.updated_modules.append(copied_module)

        return self.updated_modules

    def update_all_media_references(self, modules: List[Module],
                                    path_mapping: Dict[str, str]) -> List[Module]:
        """
        Update all media references in modules using the provided path mapping

        Args:
            modules: List of modules to update
            path_mapping: Dictionary mapping original paths to base64 data URLs

        Returns:
            Updated modules list
        """
        self.path_mappings = path_mapping

        for module in modules:
            self._update_module_media_references(module, path_mapping)

        return modules

    def _update_module_media_references(self, module: Module, path_mapping: Dict[str, str]):
        """
        Update media references for a single module and its nested content

        Args:
            module: Module to update
            path_mapping: Path to base64 URL mapping
        """
        # Update the module's own media references
        if hasattr(module, 'update_media_references'):
            module.update_media_references(path_mapping)

        # Handle TabModule nested content
        if isinstance(module, TabModule):
            self._update_tab_module_media(module, path_mapping)

    def _update_tab_module_media(self, tab_module: TabModule, path_mapping: Dict[str, str]):
        """
        Update media references in all nested modules within a TabModule

        Args:
            tab_module: TabModule containing nested modules
            path_mapping: Path to base64 URL mapping
        """
        for tab_name, nested_modules in tab_module.sub_modules.items():
            for nested_module in nested_modules:
                self._update_module_media_references(nested_module, path_mapping)

    def _deep_copy_module(self, module: Module) -> Module:
        """
        Create a deep copy of a module, handling special cases for TabModules

        Args:
            module: Module to copy

        Returns:
            Deep copied module
        """
        # Use deepcopy for the basic module structure
        copied_module = copy.deepcopy(module)

        # For TabModules, ensure nested modules are properly copied
        if isinstance(module, TabModule) and isinstance(copied_module, TabModule):
            copied_module.sub_modules = {}
            for tab_name, nested_modules in module.sub_modules.items():
                copied_module.sub_modules[tab_name] = []
                for nested_module in nested_modules:
                    copied_nested = self._deep_copy_module(nested_module)
                    copied_module.sub_modules[tab_name].append(copied_nested)

        return copied_module

    def get_all_media_references(self, modules: List[Module]) -> Set[str]:
        """
        Collect all media file references from a list of modules

        Args:
            modules: List of modules to scan

        Returns:
            Set of unique media file paths
        """
        all_media = set()

        for module in modules:
            module_media = self._get_module_media_references(module)
            all_media.update(module_media)

        return all_media

    def _get_module_media_references(self, module: Module) -> Set[str]:
        """
        Get all media references from a single module

        Args:
            module: Module to scan

        Returns:
            Set of media file paths from this module
        """
        media_refs = set()

        # Get media references from the module if it supports the method
        if hasattr(module, 'get_media_references'):
            module_refs = module.get_media_references()
            media_refs.update(ref for ref in module_refs if ref and ref.strip())

        # Handle TabModule nested content
        if isinstance(module, TabModule):
            for tab_name, nested_modules in module.sub_modules.items():
                for nested_module in nested_modules:
                    nested_refs = self._get_module_media_references(nested_module)
                    media_refs.update(nested_refs)

        return media_refs

    def validate_media_updates(self, modules: List[Module],
                               path_mapping: Dict[str, str]) -> Dict[str, List[str]]:
        """
        Validate that all media references in modules have corresponding mappings

        Args:
            modules: Modules to validate
            path_mapping: Available path mappings

        Returns:
            Dictionary with 'missing' and 'found' lists
        """
        all_media = self.get_all_media_references(modules)

        missing_mappings = []
        found_mappings = []

        for media_path in all_media:
            if media_path in path_mapping:
                found_mappings.append(media_path)
            else:
                missing_mappings.append(media_path)

        return {
            'missing': missing_mappings,
            'found': found_mappings,
            'total_references': len(all_media)
        }

    def restore_original_modules(self) -> List[Module]:
        """
        Restore the original modules if they were backed up

        Returns:
            Original modules list or empty list if no backup exists
        """
        return self.original_modules.copy() if self.original_modules else []

    def clear_backup(self):
        """Clear backed up modules to free memory"""
        self.original_modules.clear()
        self.updated_modules.clear()
        self.path_mappings.clear()

    def get_update_statistics(self) -> Dict[str, int]:
        """
        Get statistics about the update process

        Returns:
            Dictionary with update statistics
        """
        return {
            'original_modules_count': len(self.original_modules),
            'updated_modules_count': len(self.updated_modules),
            'path_mappings_count': len(self.path_mappings),
            'has_backup': len(self.original_modules) > 0
        }