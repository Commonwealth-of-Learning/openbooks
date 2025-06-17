#!/usr/bin/env python3
"""
Combined Pressbooks to Static Site Converter
Combines features from both enhanced and basic converters
Preserves original layout and structure while making it work offline
"""

import requests
from bs4 import BeautifulSoup
import os
import re
import json
from urllib.parse import urljoin, urlparse
import time

class CombinedPressbooksConverter:
    def __init__(self, base_url, output_dir="static_site"):
        self.base_url = base_url.rstrip('/')
        self.output_dir = output_dir
        self.pages = []
        self.assets = {}
        self.css_files = []
        
        # Create output directory structure
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(f"{output_dir}/wp-content", exist_ok=True)
        os.makedirs(f"{output_dir}/wp-includes", exist_ok=True)
        os.makedirs(f"{output_dir}/assets", exist_ok=True)
        os.makedirs(f"{output_dir}/css", exist_ok=True)
        os.makedirs(f"{output_dir}/images", exist_ok=True)
        
    def get_page_content(self, url):
        """Fetch and parse a page"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def discover_pages(self):
        """Discover all pages by examining the site structure"""
        print("Discovering pages...")
        
        soup = self.get_page_content(self.base_url)
        if not soup:
            return
        
        # Add main page first
        self.pages.append({
            'title': 'Table of Contents',
            'url': self.base_url,
            'filename': 'index.html',
            'type': 'main'
        })
        
        # Look for chapter links in the navigation or content
        # Pressbooks typically has navigation in specific areas
        nav_selectors = [
            '.entry-content a[href*="chapter"]',
            '.book-body a[href*="chapter"]', 
            'nav a[href*="chapter"]',
            '.page-navigation a',
            'a[href*="front-matter"]',
            'a[href*="back-matter"]',
            'main a[href*="chapter"]',
            '.book-navigation a',
            'nav a',
            '.toc a'
        ]
        
        found_links = set()
        
        for selector in nav_selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href and href not in found_links:
                    full_url = urljoin(self.base_url, href)
                    if self.base_url in full_url:
                        found_links.add(href)
                        
                        # Determine page type
                        page_type = 'chapter'
                        if 'front-matter' in href:
                            page_type = 'front-matter'
                        elif 'back-matter' in href:
                            page_type = 'back-matter'
                        elif 'appendix' in href.lower():
                            page_type = 'appendix'
                        elif 'home' in href.lower() or href == '/':
                            page_type = 'main'
                            
                        # Get clean title
                        title = link.get_text().strip()
                        if not title:
                            title = f"Page {len(self.pages)}"
                            
                        self.pages.append({
                            'title': title,
                            'url': full_url,
                            'filename': self.url_to_filename(full_url),
                            'type': page_type,
                            'href': href
                        })
        
        print(f"Found {len(self.pages)} pages")
        for page in self.pages:
            print(f"  - {page['type']}: {page['title']}")
    
    def url_to_filename(self, url):
        """Convert URL to local filename preserving structure"""
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        
        # Remove the base path part
        base_path = urlparse(self.base_url).path.strip('/')
        if path.startswith(base_path):
            path = path[len(base_path):].strip('/')
        
        if not path:
            return 'index.html'
        
        # Keep the original path structure but make it filename safe
        filename = path.replace('/', '_') + '.html'
        filename = re.sub(r'[^\w\-_\.]', '_', filename)
        return filename
    
    def download_asset(self, url, asset_type=None):
        """Download and save asset maintaining directory structure"""
        try:
            if url in self.assets:
                return self.assets[url]
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            # Maintain the original directory structure
            parsed_url = urlparse(url)
            asset_path = parsed_url.path.lstrip('/')
            
            # Handle special cases like Google Fonts
            if 'fonts.googleapis.com' in url:
                filename = f"google_fonts_{len(self.assets)}.css"
                asset_path = f"assets/css/{filename}"
            elif asset_type and not asset_path:
                filename = f"asset_{len(self.assets)}"
                if url.endswith(('.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg')):
                    ext = url.split('.')[-1]
                    filename += f".{ext}"
                asset_path = f"assets/{asset_type}/{filename}"
            elif not asset_path:
                # Generate a safe filename if no path available
                filename = f"asset_{len(self.assets)}"
                if '.' in url:
                    ext = url.split('.')[-1].split('?')[0]  # Remove query params
                    if ext in ['css', 'js', 'png', 'jpg', 'jpeg', 'gif', 'svg']:
                        filename += f".{ext}"
                asset_path = f"assets/misc/{filename}"
            
            # Create local path with better error handling
            local_path = os.path.join(self.output_dir, asset_path)
            local_dir = os.path.dirname(local_path)
            
            # Try to create directory with better error handling
            try:
                os.makedirs(local_dir, exist_ok=True)
            except PermissionError:
                # Fallback to a simpler directory structure
                safe_filename = f"asset_{len(self.assets)}"
                if url.endswith(('.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg')):
                    ext = url.split('.')[-1].split('?')[0]
                    safe_filename += f".{ext}"
                
                fallback_path = os.path.join(self.output_dir, "assets", safe_filename)
                local_path = fallback_path
                local_dir = os.path.dirname(local_path)
                os.makedirs(local_dir, exist_ok=True)
                asset_path = f"assets/{safe_filename}"
            
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            # Store relative path for replacement
            self.assets[url] = asset_path
            
            return asset_path
            
        except Exception as e:
            print(f"Error downloading asset {url}: {e}")
            # Return a placeholder path so the page doesn't break completely
            return None
    
    def process_assets(self, soup, page_url):
        """Process and download all assets while maintaining paths"""
        
        # Handle images
        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                if src.startswith('http'):
                    asset_url = src
                else:
                    asset_url = urljoin(page_url, src)
                
                local_path = self.download_asset(asset_url, 'images')
                if local_path:
                    img['src'] = local_path
        
        # Handle CSS files
        for link in soup.find_all('link', rel='stylesheet'):
            href = link.get('href')
            if href:
                if href.startswith('http'):
                    asset_url = href
                else:
                    asset_url = urljoin(page_url, href)
                
                local_path = self.download_asset(asset_url, 'css')
                if local_path:
                    link['href'] = local_path
        
        # Handle JavaScript files
        for script in soup.find_all('script', src=True):
            src = script.get('src')
            if src:
                if src.startswith('http'):
                    asset_url = src
                else:
                    asset_url = urljoin(page_url, src)
                
                local_path = self.download_asset(asset_url, 'js')
                if local_path:
                    script['src'] = local_path
    
    def clean_pressbooks_elements(self, soup):
        """Remove Pressbooks admin elements while preserving content structure"""
        
        # Elements to remove completely
        elements_to_remove = [
            '#wp-admin-bar-root-default',
            '.edit-link',
            '.screen-reader-text',
            '[href*="wp-admin"]',
            '[href*="wp-login"]',
            '.pressbooks-admin-bar'
        ]
        
        for selector in elements_to_remove:
            for element in soup.select(selector):
                element.decompose()
        
        # Remove elements by class patterns
        for element in soup.find_all(class_=re.compile(r'pressbooks|pb-|wp-admin')):
            element.decompose()
            
        # Remove admin/edit links
        for element in soup.find_all('a', href=re.compile(r'wp-admin|edit')):
            element.decompose()
        
        # Remove admin-related attributes
        for element in soup.find_all(True):
            # Remove admin classes while keeping content classes
            if element.get('class'):
                classes = element['class']
                cleaned_classes = [cls for cls in classes if not any(
                    admin_term in cls.lower() for admin_term in ['admin', 'edit', 'wp-admin']
                )]
                if cleaned_classes:
                    element['class'] = cleaned_classes
                else:
                    del element['class']
    
    def fix_internal_links(self, soup):
        """Fix internal links to point to local files"""
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Check if it's an internal link to our site
            if self.base_url in href:
                # Find the corresponding page
                target_filename = self.url_to_filename(href)
                link['href'] = target_filename
            elif href.startswith('/') and not href.startswith('//'):
                # Relative link within the domain
                full_url = urljoin(self.base_url, href)
                if any(page['url'] == full_url for page in self.pages):
                    target_filename = self.url_to_filename(full_url)
                    link['href'] = target_filename
    
    def create_navigation_menu(self):
        """Create collapsible navigation menu HTML"""
        nav_html = '''<nav class="site-navigation">
    <div class="nav-toggle">
        <button id="nav-toggle-btn" onclick="toggleNavigation()">
            <span class="nav-icon">☰</span> Navigation
        </button>
    </div>
    <div class="nav-menu" id="nav-menu">
        <ul>
'''
        for page in self.pages:
            nav_html += f'            <li><a href="{page["filename"]}">{page["title"]}</a></li>\n'
        nav_html += '''        </ul>
    </div>
</nav>

<script>
function toggleNavigation() {
    const menu = document.getElementById('nav-menu');
    const btn = document.getElementById('nav-toggle-btn');
    const icon = btn.querySelector('.nav-icon');
    
    if (menu.style.display === 'none' || menu.style.display === '') {
        menu.style.display = 'block';
        icon.textContent = '✕';
    } else {
        menu.style.display = 'none';
        icon.textContent = '☰';
    }
}

// Hide menu by default on page load
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('nav-menu').style.display = 'none';
});
</script>
'''
        return nav_html
    
    def add_navigation_styles(self, soup):
        """Add collapsible navigation styles to page"""
        head = soup.find('head')
        if head:
            style = soup.new_tag('style')
            style.string = """
            .site-navigation {
                background: #f8f9fa;
                margin-bottom: 20px;
                border-radius: 5px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                position: relative;
                z-index: 1000;
            }
            
            .nav-toggle {
                padding: 15px;
            }
            
            #nav-toggle-btn {
                background: #0066cc;
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
                font-weight: 500;
                display: flex;
                align-items: center;
                gap: 8px;
                transition: all 0.2s;
            }
            
            #nav-toggle-btn:hover {
                background: #0052a3;
                transform: translateY(-1px);
            }
            
            .nav-icon {
                font-size: 18px;
                line-height: 1;
            }
            
            .nav-menu {
                display: none;
                background: white;
                border-top: 1px solid #e9ecef;
                max-height: 400px;
                overflow-y: auto;
                position: absolute;
                top: 100%;
                left: 0;
                right: 0;
                border-radius: 0 0 5px 5px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            
            .nav-menu ul { 
                list-style: none; 
                padding: 15px; 
                margin: 0;
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 8px;
            }
            
            .nav-menu li { 
                margin: 0;
            }
            
            .nav-menu a { 
                text-decoration: none; 
                padding: 8px 12px; 
                border: 1px solid #ddd;
                border-radius: 4px;
                background: #f8f9fa;
                color: #0066cc;
                font-size: 14px;
                transition: all 0.2s;
                display: block;
                text-align: center;
            }
            
            .nav-menu a:hover { 
                background: #0066cc;
                color: white;
                transform: translateY(-1px);
                border-color: #0066cc;
            }
            
            @media (max-width: 768px) {
                .nav-menu ul {
                    grid-template-columns: 1fr;
                }
                
                .nav-menu {
                    position: static;
                    box-shadow: none;
                    border-top: 1px solid #e9ecef;
                    border-radius: 0;
                }
            }
            
            /* Ensure navigation doesn't interfere with page content */
            body {
                position: relative;
            }
            """
            head.append(style)
    
    def convert_page(self, page):
        """Convert individual page while preserving original structure"""
        print(f"Converting: {page['title']} ({page['type']})")
        
        soup = self.get_page_content(page['url'])
        if not soup:
            return False
        
        # Process assets first
        self.process_assets(soup, page['url'])
        
        # Clean admin elements
        self.clean_pressbooks_elements(soup)
        
        # Fix internal links
        self.fix_internal_links(soup)
        
        # Add navigation to page
        body = soup.find('body')
        if body:
            nav = BeautifulSoup(self.create_navigation_menu(), 'html.parser')
            body.insert(0, nav)
        
        # Add navigation styles
        self.add_navigation_styles(soup)
        
        # Save the page
        output_path = os.path.join(self.output_dir, page['filename'])
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        
        return True
    
    def create_enhanced_navigation(self):
        """Create a separate enhanced navigation page"""
        nav_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Navigation - Pressbooks Site</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
            background: #f5f5f5;
        }}
        .nav-container {{
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .nav-header {{
            text-align: center;
            margin-bottom: 40px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 40px 20px;
        }}
        .nav-header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        .nav-content {{
            padding: 40px;
        }}
        .nav-section {{
            margin-bottom: 40px;
        }}
        .nav-section h2 {{
            color: #333;
            border-left: 4px solid #667eea;
            padding-left: 15px;
            margin-bottom: 20px;
            font-size: 1.5em;
        }}
        .nav-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
        }}
        .nav-item {{
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 20px;
            transition: all 0.3s ease;
        }}
        .nav-item:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            border-color: #667eea;
        }}
        .nav-item a {{
            text-decoration: none;
            color: #0066cc;
            font-weight: 600;
            font-size: 1.1em;
            display: block;
        }}
        .nav-item a:hover {{
            color: #667eea;
        }}
        .back-to-book {{
            text-align: center;
            margin: 40px 0;
        }}
        .back-to-book a {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 15px 30px;
            text-decoration: none;
            border-radius: 25px;
            font-weight: 600;
            transition: all 0.3s ease;
            display: inline-block;
        }}
        .back-to-book a:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }}
        .stats {{
            background: #e9ecef;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
            text-align: center;
        }}
        .stats strong {{
            color: #667eea;
            font-size: 1.2em;
        }}
    </style>
</head>
<body>
    <div class="nav-container">
        <div class="nav-header">
            <h1>Site Navigation</h1>
            <p>Complete guide to all pages and sections</p>
        </div>
        
        <div class="nav-content">
            <div class="back-to-book">
                <a href="index.html">← Back to Main Site</a>
            </div>
            
            <div class="stats">
                <strong>{len(self.pages)}</strong> pages available for browsing
            </div>
"""
        
        # Group pages by type
        grouped_pages = {
            'main': [],
            'front-matter': [],
            'chapter': [],
            'appendix': [],
            'back-matter': []
        }
        
        for page in self.pages:
            page_type = page.get('type', 'chapter')
            grouped_pages[page_type].append(page)
        
        # Add sections
        section_titles = {
            'main': 'Main Pages',
            'front-matter': 'Front Matter',
            'chapter': 'Chapters',
            'appendix': 'Appendices',
            'back-matter': 'References & Back Matter'
        }
        
        for section_key, section_pages in grouped_pages.items():
            if section_pages:
                nav_html += f"""
            <div class="nav-section">
                <h2>{section_titles[section_key]}</h2>
                <div class="nav-grid">"""
                
                for page in section_pages:
                    nav_html += f"""
                    <div class="nav-item">
                        <a href="{page["filename"]}">{page["title"]}</a>
                    </div>"""
                
                nav_html += """
                </div>
            </div>"""
        
        nav_html += """
            <div class="back-to-book">
                <a href="index.html">← Back to Main Site</a>
            </div>
        </div>
    </div>
</body>
</html>"""
        
        # Save navigation page
        with open(os.path.join(self.output_dir, 'navigation.html'), 'w', encoding='utf-8') as f:
            f.write(nav_html)
    
    def create_sitemap(self):
        """Create a sitemap JSON file"""
        sitemap = {
            'pages': self.pages,
            'conversion_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'source_url': self.base_url,
            'total_pages': len(self.pages),
            'total_assets': len(self.assets)
        }
        
        with open(os.path.join(self.output_dir, 'sitemap.json'), 'w') as f:
            json.dump(sitemap, f, indent=2)
    
    def convert(self):
        """Main conversion process"""
        print(f"Converting Pressbooks site: {self.base_url}")
        print(f"Output directory: {self.output_dir}")
        
        # Discover all pages
        self.discover_pages()
        
        if not self.pages:
            print("No pages found! Check the URL and site structure.")
            return
        
        # Convert each page
        successful_conversions = 0
        for page in self.pages:
            if self.convert_page(page):
                successful_conversions += 1
            time.sleep(0.5)  # Be respectful to the server
        
        # Create enhanced navigation
        self.create_enhanced_navigation()
        
        # Create sitemap
        self.create_sitemap()
        
        # Create conversion report
        report = {
            'source_url': self.base_url,
            'conversion_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'pages_found': len(self.pages),
            'pages_converted': successful_conversions,
            'assets_downloaded': len(self.assets),
            'output_directory': self.output_dir,
            'pages': self.pages,
            'assets': list(self.assets.keys())
        }
        
        with open(os.path.join(self.output_dir, 'conversion_report.json'), 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nConversion complete!")
        print(f"✓ Static site saved to: {self.output_dir}")
        print(f"✓ Pages converted: {successful_conversions}/{len(self.pages)}")
        print(f"✓ Assets downloaded: {len(self.assets)}")
        print(f"✓ Enhanced navigation page created: navigation.html")
        print(f"✓ Sitemap created: sitemap.json")
        print(f"✓ Conversion report created: conversion_report.json")
        print(f"\nTo view the site:")
        print(f"  cd {self.output_dir}")
        print(f"  python -m http.server 8000")
        print(f"  Then open: http://localhost:8000")
        print(f"  Or open: http://localhost:8000/navigation.html for enhanced navigation")

# Usage
if __name__ == "__main__":
    # Example usage
    converter = CombinedPressbooksConverter(
        "https://openbooks.col.org/ctft/",
        "cybersecuritytrainingforteachers"
    )
    converter.convert()