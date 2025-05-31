# utils/theme_manager.py
from pathlib import Path
from typing import Dict, List, Optional
import json


class ThemeManager:
    """Manage themes for SOP Builder"""

    def __init__(self):
        self.themes_dir = Path("assets/themes")
        self.themes_dir.mkdir(parents=True, exist_ok=True)
        self.current_theme = "kodiak"
        self.theme_metadata = self._load_theme_metadata()

    def _load_theme_metadata(self) -> Dict:
        """Load theme metadata from themes.json"""
        metadata_file = self.themes_dir / "themes.json"

        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                return json.load(f)
        else:
            # Create default metadata
            default_metadata = {
                "kodiak": {
                    "name": "Kodiak",
                    "description": "Professional theme with Kodiak branding",
                    "author": "Kodiak Cakes",
                    "version": "1.0",
                    "assets": [
                        "Gin_Round.otf",
                        "background.jpg",
                        "bear_red.png",
                        "bear_paw.png",
                        "Mountains.png",
                        "Kodiak.png"
                    ],
                    "colors": {
                        "primary": "#B22234",
                        "secondary": "#4A3828",
                        "background": "#D4B69A"
                    }
                },
                "default": {
                    "name": "Default",
                    "description": "Clean, minimal theme",
                    "author": "System",
                    "version": "1.0",
                    "assets": [],
                    "colors": {
                        "primary": "#2c3e50",
                        "secondary": "#3498db",
                        "background": "#ecf0f1"
                    }
                }
            }

            # Save default metadata
            with open(metadata_file, 'w') as f:
                json.dump(default_metadata, f, indent=2)

            return default_metadata

    def get_available_themes(self) -> List[Dict]:
        """Get list of available themes with metadata"""
        themes = []

        for css_file in self.themes_dir.glob("*.css"):
            theme_id = css_file.stem

            # Get metadata if available
            metadata = self.theme_metadata.get(theme_id, {
                "name": theme_id.title(),
                "description": f"{theme_id} theme",
                "author": "Unknown",
                "version": "1.0",
                "assets": [],
                "colors": {}
            })

            themes.append({
                "id": theme_id,
                "file": str(css_file),
                **metadata
            })

        return themes

    def get_theme_info(self, theme_id: str) -> Optional[Dict]:
        """Get information about a specific theme"""
        themes = self.get_available_themes()
        for theme in themes:
            if theme["id"] == theme_id:
                return theme
        return None

    def create_default_theme(self):
        """Create a default theme CSS file"""
        default_css = '''/* Default SOP Theme */
:root {
    --primary-color: #2c3e50;
    --secondary-color: #3498db;
    --background-color: #ecf0f1;
    --text-color: #2c3e50;
    --border-color: #bdc3c7;
    --warning-color: #e74c3c;
    --success-color: #27ae60;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    line-height: 1.6;
    margin: 0;
    padding: 0;
    background-color: var(--background-color);
    color: var(--text-color);
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
    background-color: white;
    min-height: 100vh;
}

/* Header Styles */
.header {
    background-color: var(--primary-color);
    color: white;
    padding: 2rem;
    margin: -2rem -2rem 2rem -2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.header h1 {
    margin: 0;
    font-size: 2.5rem;
}

.logo-container {
    width: 150px;
    height: 150px;
}

.logo-container img {
    width: 100%;
    height: 100%;
    object-fit: contain;
}

/* Section Title Styles */
.section-title {
    margin: 3rem 0 2rem 0;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid var(--primary-color);
}

.section-title h2 {
    color: var(--primary-color);
    margin: 0;
}

/* Step Card Styles */
.step-card {
    background: white;
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 2rem;
    margin: 1.5rem 0;
    position: relative;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.step-number {
    position: absolute;
    top: -15px;
    left: -15px;
    width: 40px;
    height: 40px;
    background: var(--secondary-color);
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    font-size: 1.2rem;
}

/* Media Container Styles */
.media-container {
    margin: 2rem 0;
    border: 1px solid var(--border-color);
    border-radius: 8px;
    overflow: hidden;
    max-width: var(--media-max-width, 800px);
    margin-left: auto;
    margin-right: auto;
}

.media-header {
    background: var(--primary-color);
    color: white;
    padding: 0.75rem 1rem;
    font-weight: bold;
}

.media-content {
    background: #f8f9fa;
    padding: 1rem;
    text-align: center;
}

.media-content img {
    max-width: 100%;
    height: auto;
    cursor: pointer;
}

.media-caption {
    padding: 0.75rem 1rem;
    background: #f8f9fa;
    border-top: 1px solid var(--border-color);
    font-size: 0.9rem;
    color: #666;
}

/* Table Styles */
.custom-table {
    width: 100%;
    border-collapse: collapse;
    margin: 1rem 0;
}

.custom-table th,
.custom-table td {
    padding: 0.75rem;
    text-align: left;
    border: 1px solid var(--border-color);
}

.custom-table th {
    background: var(--primary-color);
    color: white;
    font-weight: bold;
}

.custom-table tr:hover {
    background: #f8f9fa;
}

/* Disclaimer Box */
.disclaimer-box {
    background: #fff3cd;
    border: 1px solid #ffeaa7;
    border-left: 4px solid var(--warning-color);
    padding: 1.5rem;
    margin: 2rem 0;
    border-radius: 4px;
}

/* Issue Card */
.issue-card {
    background: white;
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 1.5rem;
    margin: 1.5rem 0;
}

.issue-card h4 {
    color: var(--warning-color);
    margin: 0 0 1rem 0;
}

.solution {
    background: #f8f9fa;
    padding: 1rem;
    margin-top: 1rem;
    border-left: 3px solid var(--secondary-color);
}

/* Footer */
.footer {
    background: var(--primary-color);
    color: white;
    padding: 2rem;
    margin: 2rem -2rem -2rem -2rem;
    text-align: center;
}

/* Media Grid */
.media-grid {
    display: grid;
    gap: 1rem;
    margin: 2rem 0;
}

.media-grid.side-by-side {
    grid-template-columns: 1fr 1fr;
}

.media-grid.grid-3 {
    grid-template-columns: repeat(3, 1fr);
}

.media-grid.grid-4 {
    grid-template-columns: repeat(4, 1fr);
}

@media (max-width: 768px) {
    .media-grid {
        grid-template-columns: 1fr !important;
    }
}

/* Tabs */
.tabs {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1rem;
    border-bottom: 2px solid var(--border-color);
}

.tab {
    padding: 0.75rem 1.5rem;
    background: #f8f9fa;
    border: 1px solid var(--border-color);
    border-bottom: none;
    cursor: pointer;
    transition: all 0.3s ease;
}

.tab.active {
    background: white;
    border-color: var(--primary-color);
    color: var(--primary-color);
    font-weight: bold;
}

.section-content {
    display: none;
    padding: 1rem 0;
}

.section-content.active {
    display: block;
}

/* Modal for image viewing */
.modal {
    display: none;
    position: fixed;
    z-index: 1000;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0,0,0,0.8);
}

.modal-content {
    position: relative;
    margin: 5% auto;
    max-width: 90%;
    max-height: 90vh;
}

.modal-content img {
    width: 100%;
    height: auto;
    max-height: 85vh;
    object-fit: contain;
}'''

        default_theme_path = self.themes_dir / "default.css"
        with open(default_theme_path, 'w', encoding='utf-8') as f:
            f.write(default_css)

        return default_theme_path

    def validate_theme_assets(self, theme_id: str) -> Dict[str, bool]:
        """Check if all required assets for a theme exist"""
        theme_info = self.get_theme_info(theme_id)
        if not theme_info:
            return {}

        assets_status = {}
        assets_dir = Path("assets")

        for asset in theme_info.get("assets", []):
            asset_path = assets_dir / asset
            assets_status[asset] = asset_path.exists()

        return assets_status
