import re
from pathlib import Path
from typing import Dict, List, Tuple
from utils.base64_embedder import Base64EmbedderService


class CSSAssetEmbedder:
    """Handles embedding of assets referenced in CSS files"""

    def __init__(self):
        self.base64_embedder = Base64EmbedderService()

    def embed_css_assets(self, css_content: str, css_file_path: Path) -> str:
        """
        Find and embed all assets referenced in CSS content

        Args:
            css_content: CSS file content
            css_file_path: Path to the CSS file (for resolving relative paths)

        Returns:
            Updated CSS content with embedded assets
        """

        # Find all url() references in CSS
        url_pattern = r'url\([\'"]?([^\'")]+)[\'"]?\)'

        def replace_url(match):
            asset_path = match.group(1)

            # Skip data URLs that are already embedded
            if asset_path.startswith('data:'):
                return match.group(0)

            # Skip external URLs
            if asset_path.startswith(('http://', 'https://', '//')):
                return match.group(0)

            # Resolve relative path
            if not Path(asset_path).is_absolute():
                # Resolve relative to CSS file location
                css_dir = css_file_path.parent
                resolved_path = css_dir / asset_path
            else:
                resolved_path = Path(asset_path)

            # Try to embed the asset
            try:
                data_url = self.base64_embedder.embed_file_to_base64(str(resolved_path))
                if data_url:
                    print(f"   ✅ Embedded CSS asset: {asset_path}")
                    return f'url({data_url})'
                else:
                    print(f"   ⚠️ Failed to embed CSS asset: {asset_path}")
                    return match.group(0)
            except Exception as e:
                print(f"   ❌ Error embedding CSS asset {asset_path}: {e}")
                return match.group(0)

        # Replace all url() references
        updated_css = re.sub(url_pattern, replace_url, css_content)
        return updated_css

    def find_css_assets(self, css_content: str, css_file_path: Path) -> List[str]:
        """
        Find all asset paths referenced in CSS

        Returns:
            List of resolved asset file paths
        """
        url_pattern = r'url\([\'"]?([^\'")]+)[\'"]?\)'
        matches = re.findall(url_pattern, css_content)

        asset_paths = []
        for asset_path in matches:
            # Skip data URLs and external URLs
            if (asset_path.startswith('data:') or
                    asset_path.startswith(('http://', 'https://', '//'))):
                continue

            # Resolve relative path
            if not Path(asset_path).is_absolute():
                css_dir = css_file_path.parent
                resolved_path = css_dir / asset_path
            else:
                resolved_path = Path(asset_path)

            if resolved_path.exists():
                asset_paths.append(str(resolved_path))

        return asset_paths
