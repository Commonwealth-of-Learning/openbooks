"""
Utility functions for the Pressbooks converter
"""

import os
import re
import logging
from urllib.parse import urlparse
from typing import Optional, List, Dict, Any

def setup_logging(level: str = "INFO") -> logging.Logger:
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def create_directory_structure(output_dir: str, asset_dirs: Dict[str, str]) -> None:
    """Create the output directory structure"""
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(f"{output_dir}/wp-content", exist_ok=True)
    os.makedirs(f"{output_dir}/wp-includes", exist_ok=True)
    
    for dir_path in asset_dirs.values():
        os.makedirs(f"{output_dir}/{dir_path}", exist_ok=True)

def url_to_filename(url: str, base_url: str) -> str:
    """Convert URL to local filename preserving structure"""
    parsed = urlparse(url)
    path = parsed.path.strip('/')
    
    base_path = urlparse(base_url).path.strip('/')
    if path.startswith(base_path):
        path = path[len(base_path):].strip('/')
    
    if not path:
        return 'index.html'
    
    filename = path.replace('/', '_') + '.html'
    return re.sub(r'[^\w\-_\.]', '_', filename)

def get_asset_type(url: str) -> str:
    """Determine asset type from URL"""
    lower_url = url.lower()
    
    if lower_url.endswith('.pdf'):
        return 'pdf'
    elif lower_url.endswith('.epub'):
        return 'epub'
    elif lower_url.endswith('.xml'):
        return 'xml'
    elif lower_url.endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico')):
        return 'images'
    elif lower_url.endswith('.css') or 'fonts.googleapis.com' in url:
        return 'css'
    elif lower_url.endswith('.js'):
        return 'js'
    else:
        return 'misc'

def get_asset_path(url: str, asset_count: int, asset_dirs: Dict[str, str]) -> str:
    """Generate asset path based on URL and type"""
    asset_type = get_asset_type(url)
    parsed_url = urlparse(url)
    asset_path = parsed_url.path.lstrip('/')
    
    if asset_type in ['pdf', 'epub', 'xml']:
        filename = os.path.basename(asset_path)
        return f"{asset_dirs[asset_type]}/{filename}"
    elif 'fonts.googleapis.com' in url:
        filename = f"google_fonts_{asset_count}.css"
        return f"{asset_dirs['css']}/{filename}"
    elif not asset_path:
        filename = f"asset_{asset_count}"
        ext = get_file_extension(url)
        if ext:
            filename += f".{ext}"
        return f"{asset_dirs['misc']}/{filename}"
    else:
        return asset_path

def get_file_extension(url: str) -> Optional[str]:
    """Extract file extension from URL"""
    if '.' in url:
        ext = url.split('.')[-1].split('?')[0]
        if ext in ['css', 'js', 'png', 'jpg', 'jpeg', 'gif', 'svg', 'ico', 'pdf', 'epub', 'xml']:
            return ext
    return None

def is_internal_link(href: str, base_url: str) -> bool:
    """Check if a link is internal to the site"""
    return (base_url in href or 
            (href.startswith('/') and not href.startswith('//')))

def clean_admin_classes(element) -> None:
    """Clean admin-related classes from an element"""
    if element.get('class'):
        classes = element['class']
        cleaned_classes = [cls for cls in classes if not any(
            admin_term in cls.lower() for admin_term in ['admin', 'edit', 'wp-admin']
        )]
        if cleaned_classes:
            element['class'] = cleaned_classes
        else:
            del element['class']

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to be filesystem-safe"""
    return re.sub(r'[^\w\-_\.]', '_', filename)