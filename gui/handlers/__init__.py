# gui/handlers/__init__.py
"""
GUI Handlers Package

This package contains specialized handlers for different aspects of the canvas functionality:
- canvas_drag_drop_handler: Handles drag and drop for existing modules on the canvas
- library_drag_drop_handler: Handles drag and drop from the module library (future)

These handlers help separate concerns and keep the main canvas_panel.py focused on coordination
rather than implementation details.
"""

from .canvas_drag_drop_handler import CanvasDragDropHandler

__all__ = ['CanvasDragDropHandler']