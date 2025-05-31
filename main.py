#!/usr/bin/env python3
"""
SOP Builder - Main Entry Point
A visual tool for creating Standard Operating Procedures
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

import customtkinter as ctk
from app.sop_builder import SOPBuilderApp
from modules.module_factory import ModuleFactory

# Import all module types to register them
from modules.header_module import HeaderModule
from modules.media_module import MediaModule
from modules.step_card_module import StepCardModule
from modules.text_module import TextModule
from modules.table_module import TableModule
from modules.section_title_module import SectionTitleModule
from modules.disclaimer_module import DisclaimerModule
from modules.footer_module import FooterModule
from modules.media_grid_module import MediaGridModule
from modules.issue_card_module import IssueCardModule
from modules.complex_module import TabModule


def register_modules():
    """Register all available module types with the factory"""
    ModuleFactory.register_module('header', HeaderModule)
    ModuleFactory.register_module('media', MediaModule)
    ModuleFactory.register_module('step_card', StepCardModule)
    ModuleFactory.register_module('text', TextModule)
    ModuleFactory.register_module('table', TableModule)
    ModuleFactory.register_module('section_title', SectionTitleModule)
    ModuleFactory.register_module('disclaimer', DisclaimerModule)
    ModuleFactory.register_module('footer', FooterModule)
    ModuleFactory.register_module('media_grid', MediaGridModule)
    ModuleFactory.register_module('issue_card', IssueCardModule)
    ModuleFactory.register_module('tabs', TabModule)


def main():
    """Main application entry point"""
    # Set appearance mode and color theme
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    # Register all modules
    register_modules()

    # Create and run the application
    app = SOPBuilderApp()
    app.run()


if __name__ == "__main__":
    main()
