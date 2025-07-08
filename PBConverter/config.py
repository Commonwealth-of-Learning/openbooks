"""
Configuration settings for the Pressbooks converter
"""

# Default URLs and paths
DEFAULT_URL = "https://openbooks.col.org/functionalfoods/"
DEFAULT_OUTPUT_DIR = "functionalfoods"

# HTTP headers
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# Navigation selectors for page discovery
NAV_SELECTORS = [
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

# Elements to remove during cleaning
ELEMENTS_TO_REMOVE = [
    '#wp-admin-bar-root-default',
    '.edit-link',
    '.screen-reader-text',
    '[href*="wp-admin"]',
    '[href*="wp-login"]',
    '.pressbooks-admin-bar'
]

# File extensions for different asset types
IMAGE_EXTENSIONS = ['png', 'jpg', 'jpeg', 'gif', 'svg', 'ico']
DOCUMENT_EXTENSIONS = ['pdf', 'epub', 'xml']
SCRIPT_EXTENSIONS = ['js']
STYLE_EXTENSIONS = ['css']

# Favicon link rel attributes
FAVICON_RELS = ['icon', 'shortcut icon', 'apple-touch-icon', 'mask-icon']

# Directory structure
ASSET_DIRS = {
    'css': 'assets/css',
    'js': 'assets/js',
    'images': 'assets/images',
    'pdf': 'assets/pdf',
    'epub': 'assets/epub',
    'xml': 'assets/xml',
    'misc': 'assets/misc'
}

# Navigation styles
NAVIGATION_STYLES = (
    '.site-navigation{display:block;margin:1em 0;padding:0.5em;'
    'background:#f0f0f0;font-family:sans-serif;font-size:0.9em;}'
    '.site-navigation a{margin-right:1em;text-decoration:none;}'
)

# Request timeout and delay settings
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 0.5