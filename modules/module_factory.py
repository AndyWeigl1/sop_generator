# modules/module_factory.py
from typing import Dict, Type, Any
from modules.base_module import Module


class ModuleFactory:
    """Factory for creating module instances"""

    _module_registry: Dict[str, Type[Module]] = {}

    @classmethod
    def register_module(cls, module_type: str, module_class: Type[Module]):
        """Register a module type"""
        cls._module_registry[module_type] = module_class

    @classmethod
    def create_module(cls, module_type: str) -> Module:
        """Create a module instance by type"""
        if module_type not in cls._module_registry:
            raise ValueError(f"Unknown module type: {module_type}")
        return cls._module_registry[module_type]()

    @classmethod
    def get_available_modules(cls) -> Dict[str, Type[Module]]:
        """Get all registered module types"""
        return cls._module_registry.copy()