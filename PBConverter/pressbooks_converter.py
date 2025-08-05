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
import logging
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


def extract_output_dir_from_url(url: str) -> str:
    """Extract output directory name from URL path"""
    try:
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        
        if path:
            # Take the last part of the path
            parts = path.split('/')
            last_part = parts[-1]
            
            # Clean the directory name to be filesystem-safe
            clean_name = re.sub(r'[^\w\-_]', '_', last_part)
            
            # Return the cleaned name if it's valid, otherwise use default
            if clean_name and clean_name != '_':
                return clean_name
        
        # Fallback to domain name if no path
        domain = parsed.netloc.replace('www.', '')
        clean_domain = re.sub(r'[^\w\-_]', '_', domain)
        return clean_domain if clean_domain else DEFAULT_OUTPUT_DIR
        
    except Exception:
        return DEFAULT_OUTPUT_DIR


class UnifiedPressbooksConverter:
    """Unified converter that handles both site conversion and HTML cleanup"""
    
    def __init__(self, base_url: str, output_dir: str = "static_site", cleanup_enabled: bool = True):
        self.base_url = base_url.rstrip('/')
        self.output_dir = output_dir
        self.cleanup_enabled = cleanup_enabled
        self.pages: List[Dict[str, Any]] = []
        self.assets: Dict[str, str] = {}
        self.css_files: List[str] = []
        self.book_downloads: Dict[str, str] = {}  # Track downloaded book files
        self.logger = setup_logging()
        
        # Configuration from config.py with runtime override support
        self.request_timeout = REQUEST_TIMEOUT
        self.request_delay = REQUEST_DELAY
        
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
            response = requests.get(url, headers=DEFAULT_HEADERS, timeout=self.request_timeout)
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
            
            response = requests.get(url, headers=DEFAULT_HEADERS, timeout=self.request_timeout)
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
        # Process book downloads FIRST if this is the main page (before any link processing)
        if page_url.rstrip('/') == self.base_url.rstrip('/'):
            self.logger.info(f"Processing book downloads for main page: {page_url}")
            self._process_book_downloads(soup, page_url)
        
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
            
            # Skip book download links that have already been processed
            if self._is_book_download_link(href) or href.startswith('books/'):
                continue
            
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
    
    def _process_book_downloads(self, soup: BeautifulSoup, page_url: str) -> None:
        """Process and download book files from 'Download this book' section"""
        self.logger.info(f"Looking for book download links on page: {page_url}")
        
        # First, let's scan all links on the page to see what we have
        all_links = soup.find_all('a', href=True)
        self.logger.info(f"Found {len(all_links)} total links on the page")
        
        # Log a sample of links for debugging (only if debug enabled)
        if self.logger.isEnabledFor(logging.DEBUG):
            sample_links = all_links[:5]  # First 5 links
            for i, link in enumerate(sample_links):
                href = link.get('href', '')
                text = link.get_text().strip()[:30]  # First 30 chars
                self.logger.debug(f"Sample link {i}: href='{href}' text='{text}'")
        
        download_patterns = [
            # Common download section selectors
            '.book-header__cover__downloads',
            '.download-dropdown',
            '.book-downloads',
            '.export-files',
            'div[class*="download"]',
            'div[class*="export"]',
            # Pressbooks-specific dropdown patterns
            'li.dropdown-item',
            'li[class*="dropdown-item"]',
            '.dropdown-item',
            # Pressbooks-specific URL patterns
            'a[href*="/open/download"]',
            'a[href*="type=epub"]',
            'a[href*="type=pdf"]',
            'a[href*="type=xml"]',
            'a[href*="type=mobi"]',
            # Fallback: look for any dropdown or link containing download keywords
            'a[href*="download"]',
            'a[href*="export"]',
            'a[href*="files"]'
        ]
        
        download_links = []
        found_urls = set()  # Track found URLs to prevent duplicates
        
        # Try different selectors to find download links
        for pattern in download_patterns:
            try:
                elements = soup.select(pattern)
                self.logger.debug(f"Pattern '{pattern}' found {len(elements)} elements")
                if elements:
                    for element in elements:
                        # Find all links within the element
                        links = element.find_all('a', href=True) if element.name != 'a' else [element]
                        self.logger.debug(f"Found {len(links)} links in element")
                        for link in links:
                            href = link.get('href')
                            text = link.get_text().strip()
                            if href and href not in found_urls and self._is_book_download_link(href):
                                self.logger.info(f"✓ Found book download link: {href}")
                                download_links.append({
                                    'url': href,
                                    'text': text,
                                    'element': link
                                })
                                found_urls.add(href)
                            else:
                                if href and href not in found_urls:
                                    self.logger.debug(f"✗ Link rejected: {href}")
            except Exception as e:
                self.logger.debug(f"Pattern {pattern} failed: {e}")
                continue
        
        # If no specific download sections found, scan the entire page for book download links
        if not download_links:
            self.logger.info("No download links found with patterns, scanning entire page...")
            download_links = self._scan_for_book_downloads(soup)
        
        if download_links:
            self.logger.info(f"Found {len(download_links)} book download links")
            # Download the files and update links
            for link_info in download_links:
                self._download_book_file(link_info, page_url, soup)
        else:
            self.logger.warning("No book download links found on this page")
    
    def _is_book_download_link(self, href: str) -> bool:
        """Check if a link is a book download link"""
        href_lower = href.lower()
        
        # Check for Pressbooks-specific download URL pattern
        if '/open/download' in href_lower and 'type=' in href_lower:
            self.logger.debug(f"✓ Pressbooks download pattern matched: {href}")
            return True
        
        # Check for common book file extensions
        book_extensions = ['.epub', '.pdf', '.mobi', '.xml']
        for ext in book_extensions:
            if href_lower.endswith(ext):
                self.logger.debug(f"✓ File extension matched ({ext}): {href}")
                return True
        
        # Check for download-related patterns in URL
        download_patterns = [
            'download',
            'export',
            'files',
            'formats'
        ]
        
        for pattern in download_patterns:
            if pattern in href_lower:
                self.logger.debug(f"✓ Download pattern matched ({pattern}): {href}")
                return True
        
        # Log why the link was rejected
        self.logger.debug(f"✗ Link rejected - no patterns matched: {href}")
        return False
    
    def _scan_for_book_downloads(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Scan entire page for potential book download links"""
        download_links = []
        
        self.logger.info("Scanning all links on page for book downloads...")
        
        # Look for links with book file extensions or Pressbooks download patterns
        all_links = soup.find_all('a', href=True)
        checked_count = 0
        
        for link in all_links:
            href = link.get('href')
            if href:
                checked_count += 1
                if self._is_book_download_link(href):
                    # For Pressbooks /open/download links, they're likely downloads
                    if '/open/download' in href.lower():
                        self.logger.info(f"✓ Found Pressbooks download link: {href}")
                        download_links.append({
                            'url': href,
                            'text': link.get_text().strip(),
                            'element': link
                        })
                    else:
                        # Additional checks to ensure it's likely a book download
                        text = link.get_text().strip().lower()
                        if any(word in text for word in ['download', 'epub', 'pdf', 'mobi', 'xml', 'export']):
                            self.logger.info(f"✓ Found download link by text: {href} (text: {text})")
                            download_links.append({
                                'url': href,
                                'text': link.get_text().strip(),
                                'element': link
                            })
                        else:
                            self.logger.debug(f"✗ Link has download pattern but no download text: {href} (text: {text})")
        
        self.logger.info(f"Scanned {checked_count} links, found {len(download_links)} download links")
        return download_links
    
    def _download_book_file(self, link_info: Dict[str, Any], page_url: str, soup: BeautifulSoup) -> None:
        """Download a book file and update the link"""
        try:
            url = link_info['url']
            element = link_info['element']
            
            self.logger.info(f"Attempting to download book file: {url}")
            
            # Make URL absolute
            if not url.startswith(('http://', 'https://')):
                url = urljoin(page_url, url)
                self.logger.debug(f"Made URL absolute: {url}")
            
            # Determine file type
            file_ext = self._get_file_extension(url)
            if not file_ext:
                self.logger.warning(f"Could not determine file extension for: {url}")
                return
            
            self.logger.debug(f"File extension determined: {file_ext}")
            
            # Download the file
            self.logger.debug(f"Downloading from: {url}")
            response = requests.get(url, headers=DEFAULT_HEADERS, timeout=self.request_timeout)
            response.raise_for_status()
            
            content_length = len(response.content)
            self.logger.debug(f"Downloaded {content_length} bytes")
            
            # Create filename
            filename = self._generate_book_filename(url, file_ext)
            self.logger.debug(f"Generated filename: {filename}")
            
            # Save file
            book_dir = os.path.join(self.output_dir, 'books')
            os.makedirs(book_dir, exist_ok=True)
            file_path = os.path.join(book_dir, filename)
            
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            self.logger.debug(f"Saved file to: {file_path}")
            
            # Update the link in the HTML
            relative_path = f"books/{filename}"
            element['href'] = relative_path
            
            # Store the download info
            self.book_downloads[url] = relative_path
            
            # Make sure the download section is visible
            self._ensure_download_section_visible(element, soup)
            
            self.logger.info(f"✓ Successfully downloaded book file: {filename} ({file_ext.upper()}) - {content_length} bytes")
            
        except Exception as e:
            self.logger.error(f"✗ Error downloading book file {link_info['url']}: {e}")
            import traceback
            self.logger.debug(f"Full traceback: {traceback.format_exc()}")
    
    def _get_file_extension(self, url: str) -> str:
        """Get file extension from URL"""
        # Parse URL to get the path and query parameters
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        self.logger.debug(f"Extracting extension from URL: {url}")
        self.logger.debug(f"Parsed path: {path}")
        self.logger.debug(f"Parsed query: {parsed.query}")
        
        # Check for Pressbooks download URL pattern with type parameter
        if '/open/download' in path and parsed.query:
            # Parse query parameters
            from urllib.parse import parse_qs
            query_params = parse_qs(parsed.query)
            self.logger.debug(f"Query parameters: {query_params}")
            if 'type' in query_params:
                file_type = query_params['type'][0].lower()
                self.logger.debug(f"Found type parameter: {file_type}")
                if file_type in ['epub', 'pdf', 'mobi', 'xml']:
                    result = f'.{file_type}'
                    self.logger.debug(f"Returning extension: {result}")
                    return result
                elif file_type == 'print_pdf':
                    result = '.pdf'
                    self.logger.debug(f"Returning extension for print_pdf: {result}")
                    return result
        
        # Check for common book formats in path
        for ext in ['.epub', '.pdf', '.mobi', '.xml']:
            if path.endswith(ext):
                self.logger.debug(f"Found extension in path: {ext}")
                return ext
        
        self.logger.debug("No extension found")
        return ''
    
    def _generate_book_filename(self, url: str, ext: str) -> str:
        """Generate a filename for the book download"""
        # Try to extract meaningful name from URL
        parsed = urlparse(url)
        path_parts = parsed.path.split('/')
        
        # For Pressbooks URLs, use the book identifier from the path
        if '/open/download' in parsed.path:
            # Extract book name from earlier in the path
            # e.g., /functionalfoods/open/download -> functionalfoods
            for i, part in enumerate(path_parts):
                if part and part not in ['open', 'download'] and not part.isdigit():
                    # Clean the filename
                    base_name = re.sub(r'[^\w\-_\.]', '_', part)
                    
                    # Handle print_pdf type by adding suffix
                    if '?type=print_pdf' in url:
                        return f"{base_name}_print{ext}"
                    else:
                        return f"{base_name}{ext}"
        
        # Look for a meaningful filename in reverse order
        for part in reversed(path_parts):
            if part and not part.isdigit() and part not in ['open', 'download']:
                # Clean the filename
                base_name = re.sub(r'[^\w\-_\.]', '_', part)
                if base_name.endswith(ext):
                    return base_name
                else:
                    # Handle print_pdf type by adding suffix
                    if '?type=print_pdf' in url:
                        return f"{base_name}_print{ext}"
                    else:
                        return f"{base_name}{ext}"
        
        # Fallback to generic name
        fallback = f"book{ext}"
        if '?type=print_pdf' in url:
            fallback = f"book_print{ext}"
        return fallback
    
    def _ensure_download_section_visible(self, element: Any, soup: BeautifulSoup) -> None:
        """Ensure the download section is visible by removing hidden classes"""
        # Find the parent container that might be hidden
        current = element
        max_depth = 5  # Prevent infinite loops
        
        while current and max_depth > 0:
            if hasattr(current, 'get') and current.get('class'):
                classes = current.get('class', [])
                # Remove common hidden classes
                hidden_classes = ['hidden', 'hide', 'd-none', 'invisible']
                new_classes = [cls for cls in classes if cls not in hidden_classes]
                
                if new_classes != classes:
                    current['class'] = new_classes
                    self.logger.info(f"Removed hidden classes from download section")
                
                # Also check for style attributes that might hide the element
                style = current.get('style', '')
                if 'display:none' in style.replace(' ', '') or 'display: none' in style:
                    # Remove display:none from style
                    new_style = re.sub(r'display\s*:\s*none\s*;?', '', style)
                    if new_style != style:
                        current['style'] = new_style
                        self.logger.info(f"Removed display:none from download section")
            
            current = current.parent if hasattr(current, 'parent') else None
            max_depth -= 1
    

    
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
        
        
        # Save the processed page
        return self._save_page(soup, page['filename'])
    
    
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
            time.sleep(self.request_delay)
        return successful_conversions
    
    def _create_conversion_report(self, successful_conversions: int) -> None:
        """Create a detailed conversion report"""
        report = {
            'source_url': self.base_url,
            'conversion_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'pages_found': len(self.pages),
            'pages_converted': successful_conversions,
            'assets_downloaded': len(self.assets),
            'book_downloads': len(self.book_downloads),
            'output_directory': self.output_dir,
            'cleanup_enabled': self.cleanup_enabled,
            'pages': self.pages,
            'assets': list(self.assets.keys()),
            'book_files': list(self.book_downloads.keys())
        }
        
        with open(os.path.join(self.output_dir, 'conversion_report.json'), 'w') as f:
            json.dump(report, f, indent=2)
    
    def _log_completion_summary(self, successful_conversions: int) -> None:
        """Log completion summary"""
        self.logger.info("\nConversion complete!")
        self.logger.info(f"✓ Static site saved to: {self.output_dir}")
        self.logger.info(f"✓ Pages converted: {successful_conversions}/{len(self.pages)}")
        self.logger.info(f"✓ Assets downloaded: {len(self.assets)}")
        self.logger.info(f"✓ Book files downloaded: {len(self.book_downloads)}")
        self.logger.info(f"✓ HTML cleanup applied: {self.cleanup_enabled}")
        self.logger.info(f"✓ To view the site, run 'python -m http.server' in '{self.output_dir}' and go to http://localhost:8000")


def main():
    """Main entry point with command-line interface"""
    parser = argparse.ArgumentParser(
        description="Unified Pressbooks Converter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s convert                                    # Convert using default config
  %(prog)s convert --url https://example.com         # Convert specific URL
  %(prog)s convert --output my_site                   # Convert to custom output dir
  %(prog)s cleanup --cleanup-dir ./existing_site     # Clean up existing files
  %(prog)s convert --no-cleanup                       # Convert without cleanup
        """
    )
    
    # Operation mode - make convert optional/default
    parser.add_argument(
        "operation",
        nargs="?",
        default="convert",
        choices=["convert", "cleanup"],
        help="Operation to perform: convert (full conversion) or cleanup (cleanup existing files). Default: convert"
    )
    
    # Common arguments with config defaults
    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help=f"Source Pressbooks URL (default: {DEFAULT_URL})"
    )
    
    parser.add_argument(
        "--output",
        default=None,
        help="Output directory (default: extracted from URL path)"
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
    
    # Additional config options
    parser.add_argument(
        "--timeout",
        type=int,
        default=REQUEST_TIMEOUT,
        help=f"Request timeout in seconds (default: {REQUEST_TIMEOUT})"
    )
    
    parser.add_argument(
        "--delay",
        type=float,
        default=REQUEST_DELAY,
        help=f"Delay between requests in seconds (default: {REQUEST_DELAY})"
    )
    
    parser.add_argument(
        "--show-config",
        action="store_true",
        help="Show current configuration and exit"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    # Determine output directory
    if args.output is None:
        args.output = extract_output_dir_from_url(args.url)
    
    # Show configuration if requested
    if args.show_config:
        print("Current Configuration:")
        print(f"  Default URL: {DEFAULT_URL}")
        print(f"  Default Output Dir: {DEFAULT_OUTPUT_DIR}")
        print(f"  Request Timeout: {REQUEST_TIMEOUT}s")
        print(f"  Request Delay: {REQUEST_DELAY}s")
        print(f"  Navigation Selectors: {len(NAV_SELECTORS)} configured")
        print(f"  Elements to Remove: {len(ELEMENTS_TO_REMOVE)} configured")
        print(f"  Asset Directories: {list(ASSET_DIRS.keys())}")
        return
    
    # Create converter instance with config parameters
    converter = UnifiedPressbooksConverter(
        base_url=args.url,
        output_dir=args.output,
        cleanup_enabled=not args.no_cleanup
    )
    
    # Enable debug logging if requested
    if args.debug:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
        converter.logger.setLevel(logging.DEBUG)
    
    # Update config values if provided
    if args.timeout != REQUEST_TIMEOUT:
        converter.request_timeout = args.timeout
    if args.delay != REQUEST_DELAY:
        converter.request_delay = args.delay
    
    # Execute operation
    if args.operation == "convert":
        converter.convert()
    elif args.operation == "cleanup":
        cleanup_dir = args.cleanup_dir or args.output
        converter.cleanup_existing_files(cleanup_dir)


if __name__ == "__main__":
    main()