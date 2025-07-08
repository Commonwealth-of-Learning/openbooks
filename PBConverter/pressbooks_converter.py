#!/usr/bin/env python3
"""
Unified Pressbooks Converter
Combines site conversion and HTML cleanup in a single, cohesive tool
"""

import requests
from bs4 import BeautifulSoup
import os
import re
import json
from urllib.parse import urljoin, urlparse
import time
import argparse
from typing import Optional, List, Dict, Any

from config import (
    DEFAULT_URL, DEFAULT_OUTPUT_DIR, DEFAULT_HEADERS, NAV_SELECTORS,
    ELEMENTS_TO_REMOVE, FAVICON_RELS, ASSET_DIRS, NAVIGATION_STYLES,
    REQUEST_TIMEOUT, REQUEST_DELAY, DOCUMENT_EXTENSIONS
)
from utils import (
    setup_logging, create_directory_structure, url_to_filename,
    get_asset_type, get_asset_path, is_internal_link, clean_admin_classes
)


class UnifiedPressbooksConverter:
    """Unified converter that handles both site conversion and HTML cleanup"""
    
    def __init__(self, base_url: str, output_dir: str = "static_site", cleanup_enabled: bool = True):
        self.base_url = base_url.rstrip('/')
        self.output_dir = output_dir
        self.cleanup_enabled = cleanup_enabled
        self.pages: List[Dict[str, Any]] = []
        self.assets: Dict[str, str] = {}
        self.css_files: List[str] = []
        self.logger = setup_logging()
        
        # HTML cleanup patterns
        self.userway_pattern = (
            r'<script>\(function\(d\)\{var s = d\.createElement\("script"\);'
            r's\.setAttribute\("data-account", "tHALxNKsJo"\);'
            r's\.setAttribute\("src", "https://cdn\.userway\.org/widget\.js"\);'
            r'\(d\.body \|\| d\.head\)\.appendChild\(s\);\}\)\(document\)'
            r'</script><noscript>Please ensure Javascript is enabled for purposes of '
            r'<a href="https://userway.org">website accessibility</a></noscript>'
        )
        
        # Create output directory structure
        create_directory_structure(output_dir, ASSET_DIRS)
    
    def get_page_content(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a page"""
        try:
            response = requests.get(url, headers=DEFAULT_HEADERS, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            self.logger.error(f"Error fetching {url}: {e}")
            return None
    
    def discover_pages(self) -> None:
        """Discover all pages by examining the site structure"""
        self.logger.info("Discovering pages...")
        
        soup = self.get_page_content(self.base_url)
        if not soup:
            return
        
        # Add main page first
        self._add_main_page()
        
        # Look for chapter links in the navigation or content
        found_links = self._find_page_links(soup)
        
        self.logger.info(f"Found {len(self.pages)} pages")
        for page in self.pages:
            self.logger.info(f"  - {page['type']}: {page['title']}")
    
    def _add_main_page(self) -> None:
        """Add the main page to the pages list"""
        self.pages.append({
            'title': 'Table of Contents',
            'url': self.base_url,
            'filename': 'index.html',
            'type': 'main'
        })
    
    def _find_page_links(self, soup: BeautifulSoup) -> set:
        """Find all page links using configured selectors"""
        found_links = set()
        
        for selector in NAV_SELECTORS:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href and href not in found_links:
                    full_url = urljoin(self.base_url, href)
                    if self.base_url in full_url:
                        found_links.add(href)
                        self._add_page_from_link(link, full_url, href)
        
        return found_links
    
    def _add_page_from_link(self, link, full_url: str, href: str) -> None:
        """Add a page from a discovered link"""
        page_type = self._determine_page_type(href)
        title = link.get_text().strip() or f"Page {len(self.pages)}"
        
        self.pages.append({
            'title': title,
            'url': full_url,
            'filename': url_to_filename(full_url, self.base_url),
            'type': page_type,
            'href': href
        })
    
    def _determine_page_type(self, href: str) -> str:
        """Determine the type of page based on its href"""
        if 'front-matter' in href:
            return 'front-matter'
        elif 'back-matter' in href:
            return 'back-matter'
        elif 'appendix' in href.lower():
            return 'appendix'
        elif 'home' in href.lower() or href == '/':
            return 'main'
        else:
            return 'chapter'
    
    def download_asset(self, url: str, asset_type: Optional[str] = None) -> Optional[str]:
        """Download and save asset maintaining directory structure"""
        try:
            if url in self.assets:
                return self.assets[url]
            
            response = requests.get(url, headers=DEFAULT_HEADERS, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            asset_path = get_asset_path(url, len(self.assets), ASSET_DIRS)
            local_path = os.path.join(self.output_dir, asset_path)
            local_dir = os.path.dirname(local_path)
            
            os.makedirs(local_dir, exist_ok=True)
            
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            self.assets[url] = asset_path
            return asset_path
            
        except Exception as e:
            self.logger.error(f"Error downloading asset {url}: {e}")
            return None
    
    def process_assets(self, soup: BeautifulSoup, page_url: str) -> None:
        """Process and download all assets while maintaining paths"""
        self._process_images(soup, page_url)
        self._process_stylesheets(soup, page_url)
        self._process_favicons(soup, page_url)
        self._process_scripts(soup, page_url)
        self._process_document_links(soup, page_url)
    
    def _process_images(self, soup: BeautifulSoup, page_url: str) -> None:
        """Process image assets including src and srcset"""
        for img in soup.find_all('img'):
            # Handle the main 'src' attribute
            src = img.get('src')
            if src:
                asset_url = urljoin(page_url, src)
                local_path = self.download_asset(asset_url, 'images')
                if local_path:
                    img['src'] = local_path
            
            # Handle the 'srcset' attribute for responsive images
            srcset = img.get('srcset')
            if srcset:
                new_srcset = self._process_srcset(srcset, page_url)
                if new_srcset:
                    img['srcset'] = new_srcset
                elif 'srcset' in img.attrs:
                    del img['srcset']
    
    def _process_srcset(self, srcset: str, page_url: str) -> str:
        """Process srcset attribute for responsive images"""
        new_srcset_parts = []
        
        for part in srcset.split(','):
            part = part.strip()
            if not part:
                continue

            # Split the part into url and descriptor (e.g., 'image.png 1024w')
            url_descriptor_pair = part.split()
            image_url_part = url_descriptor_pair[0]
            descriptor = ' '.join(url_descriptor_pair[1:])

            # Build the full absolute URL for the asset
            asset_url = urljoin(page_url, image_url_part)
            
            # Download the asset and get its new local path
            local_path = self.download_asset(asset_url, 'images')
            
            if local_path:
                # Reconstruct the part with the new local path and original descriptor
                new_srcset_parts.append(f"{local_path} {descriptor}")
        
        return ', '.join(new_srcset_parts) if new_srcset_parts else ''
    
    def _process_stylesheets(self, soup: BeautifulSoup, page_url: str) -> None:
        """Process CSS stylesheet links"""
        for link in soup.find_all('link', rel='stylesheet'):
            href = link.get('href')
            if href:
                asset_url = urljoin(page_url, href)
                local_path = self.download_asset(asset_url, 'css')
                if local_path:
                    link['href'] = local_path
    
    def _process_favicons(self, soup: BeautifulSoup, page_url: str) -> None:
        """Process favicon and icon links"""
        for link in soup.find_all('link', rel=lambda r: r and any(val in r for val in FAVICON_RELS)):
            href = link.get('href')
            if href:
                asset_url = urljoin(page_url, href)
                local_path = self.download_asset(asset_url, 'images')
                if local_path:
                    link['href'] = local_path
    
    def _process_scripts(self, soup: BeautifulSoup, page_url: str) -> None:
        """Process JavaScript files"""
        for script in soup.find_all('script', src=True):
            src = script.get('src')
            if src:
                asset_url = urljoin(page_url, src)
                local_path = self.download_asset(asset_url, 'js')
                if local_path:
                    script['src'] = local_path
    
    def _process_document_links(self, soup: BeautifulSoup, page_url: str) -> None:
        """Process PDF, EPUB, XML document links"""
        # Handle document links in <a> tags
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.lower().endswith(tuple(DOCUMENT_EXTENSIONS)):
                asset_url = urljoin(page_url, href)
                local_path = self.download_asset(asset_url)
                if local_path:
                    a['href'] = local_path

        # Handle documents in <embed> tags
        for embed in soup.find_all('embed', src=True):
            src = embed['src']
            if src.lower().endswith(tuple(DOCUMENT_EXTENSIONS)):
                asset_url = urljoin(page_url, src)
                local_path = self.download_asset(asset_url)
                if local_path:
                    embed['src'] = local_path

        # Handle documents in <iframe> tags
        for iframe in soup.find_all('iframe', src=True):
            src = iframe['src']
            if src.lower().endswith(tuple(DOCUMENT_EXTENSIONS)):
                asset_url = urljoin(page_url, src)
                local_path = self.download_asset(asset_url)
                if local_path:
                    iframe['src'] = local_path
    
    def clean_pressbooks_elements(self, soup: BeautifulSoup) -> None:
        """Remove Pressbooks admin elements while preserving content structure"""
        # Remove elements by CSS selector
        for selector in ELEMENTS_TO_REMOVE:
            for element in soup.select(selector):
                element.decompose()
        
        # Remove elements by class pattern
        for element in soup.find_all(class_=re.compile(r'pressbooks|pb-|wp-admin')):
            element.decompose()
            
        # Remove admin links
        for element in soup.find_all('a', href=re.compile(r'wp-admin|edit')):
            element.decompose()
        
        # Clean admin classes from remaining elements
        for element in soup.find_all(True):
            clean_admin_classes(element)
    
    def apply_html_cleanup(self, soup: BeautifulSoup) -> None:
        """Apply HTML cleanup operations"""
        if not self.cleanup_enabled:
            return
        
        # Convert soup to string for regex operations
        content = str(soup)
        
        # Remove UserWay widget
        content = self._remove_userway_widget(content)
        
        # Parse back to soup for DOM operations
        soup = BeautifulSoup(content, 'lxml')
        
        # Apply other cleanup operations
        self._replace_platform_links(soup)
        self._remove_search_form(soup)
        self._remove_navigation_block(soup)
        
        return soup
    
    def _remove_userway_widget(self, content: str) -> str:
        """Remove UserWay accessibility widget"""
        if re.search(self.userway_pattern, content):
            self.logger.info("  - Found and removed UserWay accessibility widget.")
            content = re.sub(self.userway_pattern, '', content)
        return content
    
    def _replace_platform_links(self, soup: BeautifulSoup) -> None:
        """Replace platform links with local index.html"""
        # Find and replace general platform links
        platform_link = soup.find('a', href=re.compile(r'https://opentextbooks\.col(vee)?\.org/?'))
        if platform_link:
            original_href = platform_link['href']
            platform_link['href'] = '../index.html'
            self.logger.info(f'  - Replaced link "{original_href}" with "../index.html".')
        
        # Find and replace specific openbooks link
        openbooks_link = soup.find('a', attrs={'aria-label': 'Openbooks.col.org'}, href='https://openbooks.col.org/')
        if openbooks_link:
            original_href = openbooks_link['href']
            openbooks_link['href'] = '../index.html'
            self.logger.info(f'  - Replaced link "{original_href}" with "../index.html".')
    
    def _remove_search_form(self, soup: BeautifulSoup) -> None:
        """Remove search form elements"""
        search_input = soup.find('input', class_='search-field')
        if search_input:
            search_label = search_input.find_parent('label')
            search_button = search_label.find_next_sibling('button', class_='search-submit') if search_label else None
            
            if search_label and search_button:
                search_label.decompose()
                search_button.decompose()
                self.logger.info("  - Found and removed search form (label and button).")
            elif search_label:
                search_label.decompose()
                self.logger.info("  - Found and removed search form label.")
    
    def _remove_navigation_block(self, soup: BeautifulSoup) -> None:
        """Remove site navigation block"""
        nav_block = soup.find('nav', class_='site-navigation')
        if nav_block:
            nav_block.decompose()
            self.logger.info('  - Removed <nav class="site-navigation"> navigation block.')
    
    def fix_internal_links(self, soup: BeautifulSoup) -> None:
        """Fix internal links to point to local files"""
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            if self.base_url in href:
                target_filename = url_to_filename(href, self.base_url)
                link['href'] = target_filename
            elif href.startswith('/') and not href.startswith('//'):
                full_url = urljoin(self.base_url, href)
                if any(page['url'] == full_url for page in self.pages):
                    target_filename = url_to_filename(full_url, self.base_url)
                    link['href'] = target_filename
            
            # Handle document links that haven't been processed yet
            if self._is_unprocessed_document_link(href):
                full_url = urljoin(self.base_url, href)
                if full_url in self.assets:
                    link['href'] = self.assets[full_url]
    
    def _is_unprocessed_document_link(self, href: str) -> bool:
        """Check if href is an unprocessed document link"""
        return (href.lower().endswith(tuple(DOCUMENT_EXTENSIONS)) and 
                not any(href.startswith(f"assets/{ext}/") for ext in ['pdf', 'epub', 'xml']))
    
    def create_navigation_menu(self) -> str:
        """Return a very small navigation block for each page."""
        nav_html = (
            '<nav class="site-navigation">'
            '<a href="index.html">Home</a> | '
            '<a href="navigation.html">All Pages</a>'
            '</nav>'
        )
        return nav_html

    def add_navigation_styles(self, soup: BeautifulSoup) -> None:
        """Insert minimal CSS required for the navigation markup."""
        if soup.head:
            style_tag = soup.new_tag('style')
            style_tag.string = NAVIGATION_STYLES
            soup.head.append(style_tag)
    
    def convert_page(self, page: Dict[str, Any]) -> bool:
        """Convert individual page while preserving original structure"""
        self.logger.info(f"Converting: {page['title']} ({page['type']})")
        
        soup = self.get_page_content(page['url'])
        if not soup:
            return False
        
        # Process the page content
        self.process_assets(soup, page['url'])
        self.clean_pressbooks_elements(soup)
        
        # Apply HTML cleanup if enabled
        if self.cleanup_enabled:
            soup = self.apply_html_cleanup(soup)
        
        self.fix_internal_links(soup)
        
        # Add navigation
        self._add_navigation_to_page(soup)
        
        # Save the processed page
        return self._save_page(soup, page['filename'])
    
    def _add_navigation_to_page(self, soup: BeautifulSoup) -> None:
        """Add navigation menu to the page"""
        if soup.body:
            nav_soup = BeautifulSoup(self.create_navigation_menu(), 'html.parser')
            soup.body.insert(0, nav_soup)
        
        self.add_navigation_styles(soup)
    
    def _save_page(self, soup: BeautifulSoup, filename: str) -> bool:
        """Save the processed page to file"""
        try:
            final_html = str(soup)
            if self.base_url:
                final_html = final_html.replace(self.base_url, '')

            output_path = os.path.join(self.output_dir, filename)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(final_html)
            
            return True
        except Exception as e:
            self.logger.error(f"Error saving page {filename}: {e}")
            return False
    
    def create_enhanced_navigation(self) -> None:
        """Create enhanced navigation page"""
        nav_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Site Navigation</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .page-type {{ margin: 20px 0; }}
        .page-type h2 {{ color: #333; border-bottom: 2px solid #007cba; }}
        .page-list {{ list-style: none; padding: 0; }}
        .page-list li {{ margin: 10px 0; }}
        .page-list a {{ text-decoration: none; color: #007cba; }}
        .page-list a:hover {{ text-decoration: underline; }}
        .stats {{ background: #f0f0f0; padding: 15px; margin: 20px 0; }}
    </style>
</head>
<body>
    <h1>Site Navigation</h1>
    <div class="stats">
        <strong>{len(self.pages)}</strong> pages converted from <a href="{self.base_url}">{self.base_url}</a>
    </div>
"""
        
        # Group pages by type
        page_types = {}
        for page in self.pages:
            page_type = page['type']
            if page_type not in page_types:
                page_types[page_type] = []
            page_types[page_type].append(page)
        
        # Generate navigation for each type
        for page_type, pages in page_types.items():
            nav_html += f"""
    <div class="page-type">
        <h2>{page_type.title()} Pages</h2>
        <ul class="page-list">
"""
            for page in pages:
                nav_html += f'            <li><a href="{page["filename"]}">{page["title"]}</a></li>\n'
            nav_html += "        </ul>\n    </div>\n"
        
        nav_html += """
</body>
</html>"""
        
        with open(os.path.join(self.output_dir, 'navigation.html'), 'w', encoding='utf-8') as f:
            f.write(nav_html)
    
    def create_sitemap(self) -> None:
        """Create sitemap JSON file"""
        sitemap = {
            'pages': self.pages,
            'conversion_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'source_url': self.base_url,
            'total_pages': len(self.pages),
            'total_assets': len(self.assets)
        }
        with open(os.path.join(self.output_dir, 'sitemap.json'), 'w') as f:
            json.dump(sitemap, f, indent=2)
    
    def cleanup_existing_files(self, directory: str = None) -> None:
        """Clean up existing HTML files in a directory"""
        target_dir = directory or self.output_dir
        
        if not os.path.isdir(target_dir):
            self.logger.error(f"Error: Directory '{target_dir}' not found.")
            return
        
        self.logger.info(f"Starting cleanup in directory: {target_dir}")
        
        files_processed = 0
        files_successful = 0
        
        for root, _, files in os.walk(target_dir):
            for file in files:
                if file.endswith('.html'):
                    file_path = os.path.join(root, file)
                    files_processed += 1
                    if self._cleanup_html_file(file_path):
                        files_successful += 1
        
        self.logger.info(f"Cleanup complete! Processed {files_successful}/{files_processed} files successfully.")
    
    def _cleanup_html_file(self, file_path: str) -> bool:
        """Clean up a single HTML file"""
        self.logger.info(f"Cleaning up: {file_path}...")
        try:
            content = self._read_file(file_path)
            if content is None:
                return False
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(content, 'lxml')
            
            # Apply cleanup
            cleaned_soup = self.apply_html_cleanup(soup)
            
            # Write back to file
            return self._write_file(file_path, str(cleaned_soup))
            
        except Exception as e:
            self.logger.error(f"Could not clean file {file_path}. Error: {e}")
            return False
    
    def _read_file(self, file_path: str) -> Optional[str]:
        """Read content from HTML file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"Error reading file {file_path}: {e}")
            return None
    
    def _write_file(self, file_path: str, content: str) -> bool:
        """Write content to HTML file"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.logger.info(f"Finished: {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error writing file {file_path}: {e}")
            return False
    
    def convert(self) -> None:
        """Main conversion process"""
        self.logger.info(f"Converting Pressbooks site: {self.base_url}")
        self.logger.info(f"Output directory: {self.output_dir}")
        self.logger.info(f"HTML cleanup enabled: {self.cleanup_enabled}")
        
        self.discover_pages()
        
        if not self.pages:
            self.logger.error("No pages found! Check the URL and site structure.")
            return
        
        successful_conversions = self._convert_all_pages()
        
        self.create_enhanced_navigation()
        self.create_sitemap()
        self._create_conversion_report(successful_conversions)
        
        self._log_completion_summary(successful_conversions)
    
    def _convert_all_pages(self) -> int:
        """Convert all discovered pages"""
        successful_conversions = 0
        for page in self.pages:
            if self.convert_page(page):
                successful_conversions += 1
            time.sleep(REQUEST_DELAY)
        return successful_conversions
    
    def _create_conversion_report(self, successful_conversions: int) -> None:
        """Create a detailed conversion report"""
        report = {
            'source_url': self.base_url,
            'conversion_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'pages_found': len(self.pages),
            'pages_converted': successful_conversions,
            'assets_downloaded': len(self.assets),
            'output_directory': self.output_dir,
            'cleanup_enabled': self.cleanup_enabled,
            'pages': self.pages,
            'assets': list(self.assets.keys())
        }
        
        with open(os.path.join(self.output_dir, 'conversion_report.json'), 'w') as f:
            json.dump(report, f, indent=2)
    
    def _log_completion_summary(self, successful_conversions: int) -> None:
        """Log completion summary"""
        self.logger.info("\nConversion complete!")
        self.logger.info(f"✓ Static site saved to: {self.output_dir}")
        self.logger.info(f"✓ Pages converted: {successful_conversions}/{len(self.pages)}")
        self.logger.info(f"✓ Assets downloaded: {len(self.assets)}")
        self.logger.info(f"✓ HTML cleanup applied: {self.cleanup_enabled}")
        self.logger.info(f"✓ To view the site, run 'python -m http.server' in '{self.output_dir}' and go to http://localhost:8000")


def main():
    """Main entry point with command-line interface"""
    parser = argparse.ArgumentParser(description="Unified Pressbooks Converter")
    
    # Operation mode
    parser.add_argument(
        "operation",
        choices=["convert", "cleanup"],
        help="Operation to perform: convert (full conversion) or cleanup (cleanup existing files)"
    )
    
    # Common arguments
    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help="Source Pressbooks URL (required for convert operation)"
    )
    
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT_DIR,
        help="Output directory"
    )
    
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Disable HTML cleanup during conversion"
    )
    
    parser.add_argument(
        "--cleanup-dir",
        help="Directory to clean up (for cleanup operation, defaults to output dir)"
    )
    
    args = parser.parse_args()
    
    # Create converter instance
    converter = UnifiedPressbooksConverter(
        base_url=args.url,
        output_dir=args.output,
        cleanup_enabled=not args.no_cleanup
    )
    
    # Execute operation
    if args.operation == "convert":
        converter.convert()
    elif args.operation == "cleanup":
        cleanup_dir = args.cleanup_dir or args.output
        converter.cleanup_existing_files(cleanup_dir)


if __name__ == "__main__":
    main()