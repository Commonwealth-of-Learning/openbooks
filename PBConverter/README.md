# Unified Pressbooks Converter

A comprehensive tool for converting Pressbooks sites to static HTML and cleaning up existing HTML files.

## Features

- **Full Site Conversion**: Convert entire Pressbooks sites to static HTML
- **Asset Management**: Download and organize all assets (images, CSS, JS, PDFs, etc.)
- **Book Download Support**: Automatically detect and download book files (EPUB, PDF, XML, MOBI)
- **HTML Cleanup**: Remove admin elements, widgets, and unwanted content
- **Responsive Images**: Handle srcset attributes for responsive images
- **Document Support**: Handle PDF, EPUB, and XML documents
- **Navigation Generation**: Create enhanced navigation pages
- **Smart Output Naming**: Automatically extract output directory from URL
- **Logging**: Comprehensive logging for debugging and monitoring

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. The tool requires the following Python packages:
   - requests
   - beautifulsoup4
   - lxml

## Usage

### Convert a Pressbooks Site

Convert a complete Pressbooks site to static HTML using default configuration:

```bash
python pressbooks_converter.py                    # Uses defaults from config.py
python pressbooks_converter.py convert            # Same as above, explicit convert
```

Convert with automatic output directory extraction:

```bash
python pressbooks_converter.py --url https://openbooks.col.org/functionalfoods/
# Output will be saved to "functionalfoods" directory
```

Convert with custom parameters:

```bash
python pressbooks_converter.py convert --url https://example.pressbooks.com --output my_site
```

### Convert with Cleanup Disabled

If you want to convert without applying HTML cleanup:

```bash
python pressbooks_converter.py convert --url https://example.pressbooks.com --output my_site --no-cleanup
```

### Clean Up Existing HTML Files

Clean up existing HTML files in a directory:

```bash
python pressbooks_converter.py cleanup --cleanup-dir ./existing_site
```

### Show Current Configuration

Display the current configuration from config.py:

```bash
python pressbooks_converter.py --show-config
```

## Command Line Options

### Common Options

- `--url URL`: Source Pressbooks URL (uses config.py default if not specified)
- `--output OUTPUT`: Output directory (default: auto-extracted from URL path)
- `--no-cleanup`: Disable HTML cleanup during conversion
- `--cleanup-dir CLEANUP_DIR`: Directory to clean up (for cleanup operation)
- `--timeout SECONDS`: Request timeout in seconds (default from config.py)
- `--delay SECONDS`: Delay between requests in seconds (default from config.py)
- `--show-config`: Show current configuration from config.py and exit

### Operations

- `convert`: Full conversion of a Pressbooks site (default operation)
- `cleanup`: Clean up existing HTML files

## Configuration

The tool uses configuration files for easy customization:

- `config.py`: Contains all configuration settings
- `utils.py`: Common utility functions

### Key Configuration Options

- **DEFAULT_URL**: Default Pressbooks URL (used when --url is not specified)
- **DEFAULT_OUTPUT_DIR**: Fallback output directory (used when URL extraction fails)
- **REQUEST_TIMEOUT**: Default request timeout in seconds (overridden by --timeout)
- **REQUEST_DELAY**: Default delay between requests in seconds (overridden by --delay)
- **NAV_SELECTORS**: CSS selectors for finding navigation links
- **ELEMENTS_TO_REMOVE**: Elements to remove during cleanup
- **ASSET_DIRS**: Directory structure for different asset types

### Using Configuration Defaults

The tool is designed to work with minimal command-line arguments by using sensible defaults from `config.py`:

```bash
# Uses all defaults from config.py
python pressbooks_converter.py

# Override specific settings while using other defaults
python pressbooks_converter.py --output my_custom_site
python pressbooks_converter.py --url https://different-site.com
```

## HTML Cleanup Features

The cleanup process removes:

- UserWay accessibility widgets
- Pressbooks admin elements
- Search forms
- Site navigation blocks
- Admin-related CSS classes
- WordPress admin links

It also:

- Replaces platform links with local references
- Maintains content structure
- Preserves functionality

## Book Download Features

The converter automatically detects and downloads book files from the "Download this book" section:

### Supported Formats
- **EPUB**: Electronic publication format
- **PDF**: Portable document format
- **XML**: Various XML formats
- **MOBI**: Mobipocket format (for Kindle)

### Download Process
1. **Detection**: Scans the main page for download sections using multiple CSS selectors
2. **Download**: Downloads found book files to the `books/` directory
3. **Link Update**: Updates HTML links to point to local downloaded files
4. **Visibility**: Automatically unhides hidden download dropdowns by removing CSS classes like `hidden`, `d-none`, etc.

### Download Section Detection
The converter looks for download sections using these patterns:
- `.book-header__cover__downloads` (specific Pressbooks class)
- `.download-dropdown`, `.book-downloads`, `.export-files`
- **Pressbooks-specific URLs**: `/open/download?type=epub`, `/open/download?type=pdf`, etc.
- Links containing keywords like "download", "export", "files"
- Any links pointing to book file extensions

### Pressbooks Download URL Pattern
The converter specifically handles Pressbooks download URLs:
- **Pattern**: `https://site.com/bookname/open/download?type=FORMAT`
- **Examples**: 
  - `https://openbooks.col.org/functionalfoods/open/download?type=epub`
  - `https://openbooks.col.org/functionalfoods/open/download?type=pdf`
  - `https://openbooks.col.org/functionalfoods/open/download?type=xml`

### Local File Organization
Downloaded book files are saved with meaningful names extracted from the URL:
```
books/
├── functionalfoods.epub    # EPUB version (from /functionalfoods/open/download?type=epub)
├── functionalfoods.pdf     # PDF version (from /functionalfoods/open/download?type=pdf)
├── functionalfoods.xml     # XML version (from /functionalfoods/open/download?type=xml)
└── functionalfoods.mobi    # MOBI version (if available)
```

### File Naming Convention
- **Pressbooks URLs**: Extracts book name from URL path (e.g., `functionalfoods` from `/functionalfoods/open/download`)
- **Direct file links**: Uses original filename or generates clean name
- **Filesystem safe**: Removes special characters and replaces with underscores
- **Format preserved**: Maintains original file extension

## Smart Output Directory Naming

When `--output` is not specified, the converter automatically extracts the output directory name from the URL:

### Examples
- `https://openbooks.col.org/functionalfoods/` → `functionalfoods`
- `https://example.com/books/psychology-2e/` → `psychology_2e`
- `https://site.com/advanced-mathematics/` → `advanced_mathematics`
- `https://pressbooks.com/` → `pressbooks_com` (fallback to domain)

### Features
- **Automatic Extraction**: Uses the last segment of the URL path
- **Filesystem Safe**: Removes special characters and replaces with underscores
- **Fallback Support**: Uses domain name if no path exists
- **Override Available**: Can still specify custom output with `--output`

### Usage Examples
```bash
# Auto-extract output directory
python pressbooks_converter.py --url https://openbooks.col.org/functionalfoods/
# Creates "functionalfoods" directory

# Override with custom directory
python pressbooks_converter.py --url https://openbooks.col.org/functionalfoods/ --output my_custom_name
# Creates "my_custom_name" directory
```

## Output Structure

The converter creates the following directory structure:

```
output_directory/
├── index.html                 # Main page
├── navigation.html            # Generated navigation
├── sitemap.json              # Site map
├── conversion_report.json    # Detailed conversion report
├── assets/
│   ├── css/                  # Stylesheets
│   ├── js/                   # JavaScript files
│   ├── images/               # Images
│   ├── pdf/                  # PDF documents
│   ├── epub/                 # EPUB documents
│   └── xml/                  # XML documents
├── books/                    # Downloaded book files
│   ├── book.epub             # EPUB book file
│   ├── book.pdf              # PDF book file
│   └── book.xml              # XML book file
├── chapter_*.html            # Chapter pages
├── front-matter_*.html       # Front matter pages
└── back-matter_*.html        # Back matter pages
```

## Advanced Usage

### Programmatic Usage

```python
from pressbooks_converter import UnifiedPressbooksConverter

# Create converter
converter = UnifiedPressbooksConverter(
    base_url="https://example.pressbooks.com",
    output_dir="my_site",
    cleanup_enabled=True
)

# Convert the site
converter.convert()

# Or just clean up existing files
converter.cleanup_existing_files("./existing_site")
```

### Custom Configuration

You can modify `config.py` to customize:

- Request timeouts and delays
- Asset directory structure
- Navigation styles
- Elements to remove during cleanup

## Error Handling

The tool includes comprehensive error handling:

- Network timeouts and retries
- File system errors
- Malformed HTML handling
- Asset download failures

All errors are logged with appropriate detail levels.

## Logging

The tool provides detailed logging:

- Page discovery and conversion progress
- Asset download status
- Cleanup operations
- Error messages and warnings

## Examples

### Basic Conversion (Using Config Defaults)
```bash
python pressbooks_converter.py                    # Uses DEFAULT_URL and DEFAULT_OUTPUT_DIR
python pressbooks_converter.py convert            # Same as above, explicit convert
```

### Conversion with Custom URL (Auto Output Directory)
```bash
python pressbooks_converter.py --url https://openbooks.col.org/functionalfoods/
# Output automatically saved to "functionalfoods" directory
```

### Conversion with Custom URL and Directory
```bash
python pressbooks_converter.py --url https://example.com --output custom_site
```

### Book Download Examples
```bash
# Convert site with book downloads (EPUB, PDF, XML automatically detected)
python pressbooks_converter.py --url https://openbooks.col.org/functionalfoods/
# Downloads available book files to books/ directory and makes download links visible
# Files saved as: functionalfoods.epub, functionalfoods.pdf, functionalfoods.xml
```

### Pressbooks Download URL Examples
```bash
# The converter automatically detects and downloads from these URL patterns:
# https://openbooks.col.org/functionalfoods/open/download?type=epub
# https://openbooks.col.org/functionalfoods/open/download?type=pdf
# https://openbooks.col.org/functionalfoods/open/download?type=xml
# https://openbooks.col.org/functionalfoods/open/download?type=mobi
```

### Conversion with Custom Settings
```bash
python pressbooks_converter.py --url https://example.com --output custom_site --timeout 60 --delay 1.0
```

### Cleanup Only
```bash
python pressbooks_converter.py cleanup --cleanup-dir ./my_html_files
```

### Conversion Without Cleanup
```bash
python pressbooks_converter.py --url https://example.com --no-cleanup
```

### Show Configuration
```bash
python pressbooks_converter.py --show-config
```

## File Organization

- `pressbooks_converter.py`: Main unified converter
- `config.py`: Configuration settings
- `utils.py`: Utility functions
- `requirements.txt`: Python dependencies

## Legacy Support

For backward compatibility, the original files are still available:
- `pb_converter.py`: Original converter (refactored)
- `html_cleanup.py`: Original cleanup tool (refactored)

## Contributing

1. Modify configuration in `config.py`
2. Add utility functions to `utils.py`
3. Extend the `UnifiedPressbooksConverter` class
4. Test with various Pressbooks sites

## License

This tool is designed for educational and archival purposes. Ensure you have proper permissions before converting copyrighted content.

## Troubleshooting

### Common Issues

1. **Network Errors**: Check internet connection and URL accessibility
2. **Permission Errors**: Ensure write permissions for output directory
3. **Memory Issues**: Large sites may require increased memory allocation
4. **Malformed HTML**: Some sites may have invalid HTML that affects parsing
5. **Book Downloads Not Found**: 
   - Check if the Pressbooks site has "Download this book" section enabled
   - Verify the site uses the standard Pressbooks download URL pattern
   - Look for download links in the converter logs
6. **Download Links Not Working**: 
   - Ensure the book has been exported in the desired formats
   - Check if the site requires authentication to download books

### Debug Mode

Enable debug logging by modifying the logging level in `utils.py`:

```python
def setup_logging(level: str = "DEBUG") -> logging.Logger:
```

This will provide detailed information about the conversion process.

### Book Download Debugging

To debug book download issues, look for these log messages:

```
INFO - Looking for book download links...
DEBUG - Found X elements with pattern: a[href*="/open/download"]
DEBUG - Found book download link: https://site.com/book/open/download?type=epub
INFO - Found X book download links
INFO - Downloaded book file: bookname.epub (EPUB)
```

If you see "No book download links found on this page", the site may not have downloads enabled or may use a different URL pattern.