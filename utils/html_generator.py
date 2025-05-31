# utils/html_generator.py
from typing import List
from modules.base_module import Module
import base64
from pathlib import Path


class HTMLGenerator:
    """Generate HTML from arranged modules"""

    def __init__(self):
        self.base_template = self._load_base_template()

    def _load_base_template(self) -> str:
        """Load the base HTML template"""
        # This is a simplified version - you can expand this to load from file
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        {styles}
    </style>
</head>
<body>
    <div class="container">
        {content}
    </div>
    <script>
        {scripts}
    </script>
</body>
</html>'''

    def generate_html(self, modules: List[Module], title: str = "Standard Operating Procedure") -> str:
        """Generate complete HTML from modules"""
        # Collect all module HTML
        content_html = ""
        for module in sorted(modules, key=lambda m: m.position):
            content_html += f'\n        {module.render_to_html()}'

        # Generate CSS
        styles = self._generate_styles()

        # Generate JavaScript
        scripts = self._generate_scripts()

        # Combine everything
        html = self.base_template.format(
            title=title,
            styles=styles,
            content=content_html,
            scripts=scripts
        )

        return html

    def _generate_styles(self) -> str:
        """Generate CSS styles for the SOP"""
        # Based on the Lineage example, here's a subset of essential styles
        return '''
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

        .disclaimer-box.disclaimer-warning {
            background: #fff3cd;
            border-color: #ffeaa7;
            border-left-color: var(--warning-color);
        }

        .disclaimer-box.disclaimer-info {
            background: #d1ecf1;
            border-color: #bee5eb;
            border-left-color: var(--secondary-color);
        }

        .disclaimer-box.disclaimer-success {
            background: #d4edda;
            border-color: #c3e6cb;
            border-left-color: var(--success-color);
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

        /* Text Module */
        .text-module {
            margin: 1.5rem 0;
        }

        .text-content p {
            margin: 0.5rem 0;
        }

        .text-emphasized {
            font-style: italic;
            color: #555;
        }

        .text-code {
            font-family: 'Courier New', monospace;
            background: #f8f9fa;
            padding: 0.25rem 0.5rem;
            border-radius: 3px;
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

    def _generate_scripts(self) -> str:
        """Generate JavaScript for interactive elements"""
        return '''
        // Tab functionality
        document.addEventListener('DOMContentLoaded', function() {
            const tabs = document.querySelectorAll('.tab');
            const sections = document.querySelectorAll('.section-content');

            tabs.forEach((tab, index) => {
                tab.addEventListener('click', () => {
                    tabs.forEach(t => t.classList.remove('active'));
                    sections.forEach(s => s.classList.remove('active'));

                    tab.classList.add('active');
                    sections[index].classList.add('active');
                });
            });
        });

        // Image modal functionality
        function openImageModal(img) {
            const modal = document.createElement('div');
            modal.className = 'modal';
            modal.innerHTML = `
                <div class="modal-content">
                    <img src="${img.src}" alt="${img.alt}">
                </div>
            `;

            modal.onclick = function() {
                modal.remove();
            };

            document.body.appendChild(modal);
            modal.style.display = 'block';
        }

        // Add click handlers to images
        document.querySelectorAll('.media-content img').forEach(img => {
            if (img.onclick === null) {
                img.onclick = function() { openImageModal(this); };
            }
        });'''

    def embed_asset(self, file_path: str) -> str:
        """Convert file to base64 data URL"""
        try:
            path = Path(file_path)
            if not path.exists():
                return file_path  # Return as-is if file doesn't exist

            # Determine MIME type
            mime_types = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.svg': 'image/svg+xml',
                '.mp4': 'video/mp4',
                '.webm': 'video/webm'
            }

            mime_type = mime_types.get(path.suffix.lower(), 'application/octet-stream')

            # Read and encode file
            with open(path, 'rb') as f:
                data = base64.b64encode(f.read()).decode('utf-8')

            return f"data:{mime_type};base64,{data}"

        except Exception as e:
            print(f"Error embedding asset {file_path}: {e}")
            return file_path