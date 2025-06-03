# utils/module_content_updater.py - FIXED
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
            path_mapping: Dictionary mapping original paths to base64 data URLs or file URIs

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
            path_mapping: Path to data URL/file URI mapping
        """
        # Debug: Log the module and its media references before update
        if hasattr(module, 'get_media_references'):
            original_refs = module.get_media_references()
            if original_refs:
                print(f"📝 Updating {module.module_type} module:")
                for ref in original_refs:
                    # Skip if already a file URI or data URL
                    if ref.startswith(('file://', 'data:', 'http')):
                        print(f"   ⚠️ SKIPPING: '{ref[:50]}...' is already a URI/URL")
                        continue

                    # Check direct mapping first (exact match)
                    if ref in path_mapping:
                        print(f"   ✅ DIRECT MATCH: '{ref}' found in mapping")
                    else:
                        print(f"   ❌ NO MATCH: '{ref}' not found in mapping")
                        print(f"   Available keys: {list(path_mapping.keys())[:3]}...")

        # Update the module's own media references
        if hasattr(module, 'update_media_references'):
            module.update_media_references(path_mapping)

        # Handle TabModule nested content
        if isinstance(module, TabModule):
            self._update_tab_module_media(module, path_mapping)

    def _is_base64_data(self, data_string: str) -> bool:
        """
        Check if a string appears to be base64 data rather than a file path

        Args:
            data_string: String to check

        Returns:
            True if it appears to be base64 data
        """
        if not data_string or not isinstance(data_string, str):
            return False

        # Check for data URL format
        if data_string.startswith('data:'):
            return True

        # Check for short strings with base64 characters
        if len(data_string) < 20 and any(c in data_string for c in '=+/'):
            # Additional check: base64 strings are typically longer than 4 characters
            # and "2Q==" is definitely base64 (it decodes to "h")
            return True

        # Check if it looks like pure base64 (no file path characteristics)
        if (len(data_string) > 10 and
                not any(char in data_string for char in r'\/.:') and  # No path separators or extensions
                data_string.replace('=', '').replace('+', '').replace('/', '').isalnum()):
            return True

        return False

    def _normalize_path_for_lookup(self, file_path: str) -> str:
        """
        Normalize file path for mapping lookup - simplified for live preview
        """
        if not file_path:
            return ''

        # Don't normalize URIs that are already converted
        if file_path.startswith(('file://', 'data:', 'http')):
            return file_path

        # For live preview, use exact path matching to avoid issues
        return file_path.strip().strip('"\'')

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
        Enhanced with debugging to track down strange references

        Args:
            modules: List of modules to scan

        Returns:
            Set of unique media file paths (excluding base64 data)
        """
        all_media = set()

        for module in modules:
            print(f"🔍 Scanning {module.module_type} module (ID: {module.id[:8]})")
            module_media = self._get_module_media_references(module)

            # Debug each media reference found
            for media_ref in module_media:
                print(f"   Found media ref: '{media_ref}' (type: {type(media_ref)})")

                # Check for suspicious references
                if self._is_base64_data(media_ref):
                    print(f"   ⚠️ SKIPPING: This looks like base64 data, not a file path!")
                    print(f"   ⚠️ Module content_data: {module.content_data}")
                    continue  # Skip base64 data

            all_media.update(module_media)

        # Filter out any base64 data that might have slipped through
        filtered_media = {ref for ref in all_media if not self._is_base64_data(ref)}

        print(f"📊 Total unique media references found: {len(filtered_media)}")
        for ref in filtered_media:
            print(f"   - '{ref}'")

        return filtered_media

    def _get_module_media_references(self, module: Module) -> Set[str]:
        """
        Get all media references from a single module
        Enhanced with debugging and better filtering
        """
        media_refs = set()

        # Get media references from the module if it supports the method
        if hasattr(module, 'get_media_references'):
            try:
                module_refs = module.get_media_references()
                print(f"   Module returned {len(module_refs)} references")

                for ref in module_refs:
                    if ref and ref.strip():
                        cleaned_ref = ref.strip()

                        # Skip if it's already a URI or data URL
                        if cleaned_ref.startswith(('file://', 'data:', 'http')):
                            print(f"   Skipping URI/URL: '{cleaned_ref[:50]}...'")
                            continue

                        print(f"   Adding reference: '{cleaned_ref}'")
                        media_refs.add(cleaned_ref)
                    else:
                        print(f"   Skipping empty/None reference: {repr(ref)}")

            except Exception as e:
                print(f"   ❌ Error getting media references: {e}")

        # Handle TabModule nested content
        if isinstance(module, TabModule):
            for tab_name, nested_modules in module.sub_modules.items():
                print(f"   Scanning tab '{tab_name}' with {len(nested_modules)} nested modules")
                for nested_module in nested_modules:
                    nested_refs = self._get_module_media_references(nested_module)
                    media_refs.update(nested_refs)

        return media_refs

    def validate_media_updates(self, modules: List[Module],
                               path_mapping: Dict[str, str]) -> Dict[str, List[str]]:
        """
        Validate that all media references in modules have corresponding mappings
        Enhanced with better debugging information and base64 filtering

        Args:
            modules: Modules to validate
            path_mapping: Available path mappings

        Returns:
            Dictionary with 'missing' and 'found' lists plus debugging info
        """
        all_media = self.get_all_media_references(modules)

        missing_mappings = []
        found_mappings = []
        debug_info = []

        for media_path in all_media:
            # Skip base64 data
            if self._is_base64_data(media_path):
                continue

            normalized_path = self._normalize_path_for_lookup(media_path)

            if normalized_path in path_mapping:
                found_mappings.append(media_path)
            else:
                missing_mappings.append(media_path)
                # Add debug info for missing mappings
                debug_info.append({
                    'original': media_path,
                    'normalized': normalized_path,
                    'reason': 'not_found_in_mapping'
                })

        return {
            'missing': missing_mappings,
            'found': found_mappings,
            'total_references': len(all_media),
            'debug_info': debug_info  # New debug information
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
        # self.original_modules.clear()
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
