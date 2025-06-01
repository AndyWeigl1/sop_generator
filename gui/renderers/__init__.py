# gui/renderers/__init__.py
"""
GUI Renderers Package

This package contains specialized renderers for different aspects of the canvas functionality:
- module_widget_manager: Handles creation and management of individual module widgets
- tab_widget_manager: Handles tab module visual representation and management

These renderers help separate concerns and keep the main canvas_panel.py focused on coordination
rather than implementation details.
"""

from .module_widget_manager import ModuleWidgetManager
from .tab_widget_manager import TabWidgetManager

__all__ = ['ModuleWidgetManager', 'TabWidgetManager']
