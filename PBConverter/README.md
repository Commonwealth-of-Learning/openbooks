# Unified Pressbooks Converter

A comprehensive tool for converting Pressbooks sites to static HTML and cleaning up existing HTML files.

## Features

- **Full Site Conversion**: Convert entire Pressbooks sites to static HTML
- **Asset Management**: Download and organize all assets (images, CSS, JS, PDFs, etc.)
- **HTML Cleanup**: Remove admin elements, widgets, and unwanted content
- **Responsive Images**: Handle srcset attributes for responsive images
- **Document Support**: Handle PDF, EPUB, and XML documents
- **Navigation Generation**: Create enhanced navigation pages
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

Convert a complete Pressbooks site to static HTML:

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

## Command Line Options

### Common Options

- `--url URL`: Source Pressbooks URL (required for convert operation)
- `--output OUTPUT`: Output directory (default: functionalfoods)
- `--no-cleanup`: Disable HTML cleanup during conversion
- `--cleanup-dir CLEANUP_DIR`: Directory to clean up (for cleanup operation)

### Operations

- `convert`: Full conversion of a Pressbooks site
- `cleanup`: Clean up existing HTML files

## Configuration

The tool uses configuration files for easy customization:

- `config.py`: Contains all configuration settings
- `utils.py`: Common utility functions

### Key Configuration Options

- **DEFAULT_URL**: Default Pressbooks URL
- **DEFAULT_OUTPUT_DIR**: Default output directory
- **NAV_SELECTORS**: CSS selectors for finding navigation links
- **ELEMENTS_TO_REMOVE**: Elements to remove during cleanup
- **ASSET_DIRS**: Directory structure for different asset types

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

### Basic Conversion
```bash
python pressbooks_converter.py convert --url https://openbooks.col.org/functionalfoods/
```

### Conversion to Custom Directory
```bash
python pressbooks_converter.py convert --url https://example.com --output custom_site
```

### Cleanup Only
```bash
python pressbooks_converter.py cleanup --cleanup-dir ./my_html_files
```

### Conversion Without Cleanup
```bash
python pressbooks_converter.py convert --url https://example.com --no-cleanup
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

### Debug Mode

Enable debug logging by modifying the logging level in `utils.py`:

```python
def setup_logging(level: str = "DEBUG") -> logging.Logger:
```

This will provide detailed information about the conversion process.