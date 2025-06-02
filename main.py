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
from app.sop_builder import SOPBuilderApp, ExportDialog
from modules.module_factory import ModuleFactory
from utils.theme_manager import ThemeManager

# Import all module types to register them
from modules.header_module import HeaderModule
from modules.media_module import MediaModule
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
    ModuleFactory.register_module('text', TextModule)
    ModuleFactory.register_module('table', TableModule)
    ModuleFactory.register_module('section_title', SectionTitleModule)
    ModuleFactory.register_module('disclaimer', DisclaimerModule)
    ModuleFactory.register_module('footer', FooterModule)
    ModuleFactory.register_module('media_grid', MediaGridModule)
    ModuleFactory.register_module('issue_card', IssueCardModule)
    ModuleFactory.register_module('tabs', TabModule)


def check_themes():
    """Check if themes are properly set up"""
    theme_manager = ThemeManager()
    themes = theme_manager.get_available_themes()

    if not themes:
        print("⚠️  No themes found. Running theme setup...")
        from utils.setup_themes import setup_themes
        setup_themes()
        return False

    # Check for Kodiak theme specifically
    kodiak_theme = theme_manager.get_theme_info("kodiak")
    if not kodiak_theme:
        print("⚠️  Kodiak theme not found!")
        print("   Please ensure kodiak.css is in: assets/themes/kodiak.css")
        return False

    # Validate Kodiak assets
    assets_status = theme_manager.validate_theme_assets("kodiak")
    missing = [asset for asset, exists in assets_status.items() if not exists]

    if missing:
        print(f"⚠️  Missing {len(missing)} Kodiak theme assets:")
        for asset in missing:
            print(f"   - {asset}")
        print("   The application will still run, but the theme may not display correctly.")

    return True


def main():
    """Main application entry point"""
    # Set appearance mode and color theme
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    # Check themes setup
    themes_ok = check_themes()

    # Register all modules
    register_modules()

    # Create and run the application
    app = SOPBuilderApp()

    # Show theme warning if needed
    if not themes_ok:
        from tkinter import messagebox
        messagebox.showwarning(
            "Theme Setup",
            "Themes are not fully configured.\n\n"
            "Please run 'python setup_themes.py' to set up themes properly.\n\n"
            "The application will continue with available themes."
        )

    app.run()


if __name__ == "__main__":
    main()
