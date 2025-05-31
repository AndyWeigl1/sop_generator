# !/usr/bin/env python3
"""
Setup script for SOP Builder themes
This script helps set up the theme directory structure
"""

import shutil
from pathlib import Path
import sys
from utils.theme_manager import ThemeManager


def setup_themes():
    """Set up the themes directory and ensure kodiak.css is in place"""

    # Create directory structure
    assets_dir = Path("assets")
    themes_dir = assets_dir / "themes"

    # Create directories
    assets_dir.mkdir(exist_ok=True)
    themes_dir.mkdir(exist_ok=True)

    print("📁 Creating theme directory structure...")
    print(f"   ✅ Created: {themes_dir}")

    # Check if kodiak.css already exists
    kodiak_css_path = themes_dir / "kodiak.css"

    if kodiak_css_path.exists():
        print(f"   ✅ Theme file already exists: {kodiak_css_path}")
    else:
        print(f"   ⚠️  Kodiak theme not found at: {kodiak_css_path}")
        print("   📝 Please copy your kodiak.css file to this location")

    # Create default theme
    tm = ThemeManager()
    default_path = tm.create_default_theme()
    print(f"   ✅ Created default theme: {default_path}")

    # Create theme metadata
    metadata_file = themes_dir / "themes.json"
    if not metadata_file.exists():
        tm._load_theme_metadata()  # This creates the default metadata
        print(f"   ✅ Created theme metadata: {metadata_file}")

    # Check for Kodiak assets
    print("\n📦 Checking for Kodiak theme assets...")
    kodiak_assets = [
        "Gin_Round.otf",
        "background.jpg",
        "bear_red.png",
        "bear_paw.png",
        "Mountains.png",
        "Kodiak.png"
    ]

    missing_assets = []
    for asset in kodiak_assets:
        asset_path = assets_dir / asset
        if asset_path.exists():
            print(f"   ✅ Found: {asset}")
        else:
            missing_assets.append(asset)
            print(f"   ❌ Missing: {asset}")

    if missing_assets:
        print(f"\n⚠️  Missing {len(missing_assets)} assets for Kodiak theme")
        print("   Please copy these files to the assets/ directory")
    else:
        print("\n✅ All Kodiak theme assets found!")

    # Instructions
    print("\n" + "=" * 50)
    print("SETUP COMPLETE!")
    print("=" * 50)
    print("\nTo use the Kodiak theme:")
    print("1. Ensure kodiak.css is in: assets/themes/kodiak.css")
    print("2. Copy all theme assets to: assets/")
    print("3. Run the SOP Builder and select 'Kodiak' theme when exporting")
    print("\nTheme directory structure:")
    print("📁 assets/")
    print("  📁 themes/")
    print("    📄 kodiak.css")
    print("    📄 default.css")
    print("    📄 themes.json")
    print("  📄 Gin_Round.otf")
    print("  📄 background.jpg")
    print("  📄 bear_red.png")
    print("  📄 bear_paw.png")
    print("  📄 Mountains.png")
    print("  📄 Kodiak.png")


if __name__ == "__main__":
    setup_themes()