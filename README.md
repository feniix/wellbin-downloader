# Wellbin Medical Data Downloader

A comprehensive tool for downloading and processing medical data from the Wellbin platform. Supports both lab reports (FhirStudy) and medical imaging (DicomStudy) with PDF to Markdown conversion optimized for LLM consumption.

## Features

- **Universal Medical Data Downloader**: Download lab reports and medical imaging from Wellbin
- **Intelligent PDF Processing**: Convert medical PDFs to LLM-optimized markdown
- **Enhanced Mode**: Page chunking, table detection, and word-level extraction
- **Medical-Optimized Headers**: Automatic detection of medical report sections
- **Flexible Configuration**: Environment variables + command-line arguments
- **Structured Output**: Organized directories with proper categorization

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd wellbin

# Install with uv (recommended)
uv sync

# Or install in development mode
uv pip install -e .
```

## Quick Start

### 1. Create Configuration

```bash
# Generate .env configuration file with defaults
uv run wellbin config
```

Edit the generated `.env` file with your Wellbin credentials:

```env
WELLBIN_EMAIL=your-email@example.com
WELLBIN_PASSWORD=your-password
```

### 2. Download Medical Data

```bash
# Download lab reports (default)
uv run wellbin scrape

# Download all types of studies
uv run wellbin scrape --types all

# Download with limits
uv run wellbin scrape --limit 10 --types FhirStudy
```

### 3. Convert to Markdown

```bash
# Basic conversion
uv run wellbin convert

# Enhanced mode with advanced features
uv run wellbin convert --enhanced-mode

# Convert specific file types
uv run wellbin convert --file-type lab --enhanced-mode
```

## Commands

### `wellbin config`

Create a comprehensive `.env` configuration file with detailed comments.

```bash
uv run wellbin config
```

### `wellbin scrape`

Download medical data from Wellbin platform.

```bash
# Basic usage
uv run wellbin scrape

# With options
uv run wellbin scrape --email user@example.com --password mypass --types all --limit 5

# Available options:
#   --email, -e          Email for login
#   --password, -p       Password for login
#   --limit, -l          Limit number of studies (0 = all)
#   --types, -t          Study types: FhirStudy, DicomStudy, or "all"
#   --output, -o         Output directory
#   --headless/--no-headless  Browser mode
#   --dry-run           Show what would be downloaded
```

### `wellbin convert`

Convert medical PDFs to markdown format optimized for LLM consumption.

```bash
# Basic conversion
uv run wellbin convert

# Enhanced mode with advanced features
uv run wellbin convert --enhanced-mode

# Available options:
#   --input-dir, -i      Input directory with PDFs
#   --output-dir, -o     Output directory for markdown
#   --file-type, -t      File type filter: lab, imaging, all
#   --enhanced-mode      Enable advanced features
#   --preserve-structure Maintain directory structure
```

## Configuration

All commands support both environment variables and command-line arguments. Command-line arguments take precedence.

### Environment Variables

```env
# Authentication (Required)
WELLBIN_EMAIL=your-email@example.com
WELLBIN_PASSWORD=your-password

# Downloader Configuration
WELLBIN_OUTPUT_DIR=medical_data
WELLBIN_STUDY_LIMIT=0
WELLBIN_STUDY_TYPES=FhirStudy
WELLBIN_HEADLESS=true

# Converter Configuration
WELLBIN_INPUT_DIR=medical_data
WELLBIN_MARKDOWN_DIR=markdown_reports
WELLBIN_PRESERVE_STRUCTURE=true
WELLBIN_FILE_TYPE=all
WELLBIN_ENHANCED_MODE=false
```

## Enhanced Mode Features

When using `--enhanced-mode` for PDF conversion:

- **Page Chunks**: Each page embedded as a section in single markdown files
- **Table Detection**: Automatic table recognition with position metadata
- **Word Positions**: Word-level extraction with coordinates (hidden in footer)
- **Medical Headers**: Optimized detection of medical report sections
- **Text-Only Processing**: Images disabled for faster, focused extraction

## Output Structure

### Downloaded Files
```
medical_data/
├── lab_reports/
│   ├── 20240604-lab-0.pdf
│   ├── 20240605-lab-0.pdf
│   └── ...
└── imaging_reports/
    ├── 20240604-imaging-0.pdf
    ├── 20240605-imaging-0.pdf
    └── ...
```

### Converted Markdown
```
markdown_reports/
├── lab_reports_markdown/
│   ├── 20240604-lab-0.md
│   ├── 20240605-lab-0.md
│   └── ...
└── imaging_reports_markdown/
    ├── 20240604-imaging-0.md
    ├── 20240605-imaging-0.md
    └── ...
```

## LLM Usage Examples

After conversion, use the markdown files with LLMs:

```bash
# Read a specific report
cat markdown_reports/lab_reports_markdown/20240604-lab-0.md

# Search across all reports
grep -r "keyword" markdown_reports/

# Count total reports
find markdown_reports -name "*.md" | wc -l

# Feed to LLM for analysis
cat markdown_reports/**/*.md | llm "analyze trends in lab values"

# Extract specific lab values
grep -h "mg/dL\|g/dL" markdown_reports/**/*.md

# Find abnormal values
grep -i "alto\|bajo\|high\|low" markdown_reports/**/*.md
```

## Development

### Package Structure

```
wellbin/
├── __init__.py              # Package initialization
├── cli.py                   # Main CLI entry point
├── core/                    # Core functionality
│   ├── __init__.py
│   ├── scraper.py          # WellbinMedicalScraper class
│   ├── converter.py        # PDFToMarkdownConverter class
│   └── utils.py            # Utility functions
└── commands/               # CLI commands
    ├── __init__.py
    ├── config.py           # Configuration command
    ├── scrape.py           # Scraping command
    └── convert.py          # Conversion command
```

### Running Tests

```bash
# Install development dependencies
uv sync --dev

# Run linting
uv run flake8 wellbin/
uv run black --check wellbin/
uv run isort --check-only wellbin/

# Run type checking
uv run mypy wellbin/
```

## Migration from Old Scripts

If you were using the old standalone scripts:

```bash
# Old way
uv run python wellbin_scrape_labs.py --config-init
uv run python wellbin_scrape_labs.py --email user@example.com --types all
uv run python convert_pdfs_to_markdown.py --enhanced-mode

# New way
uv run wellbin config
uv run wellbin scrape --email user@example.com --types all
uv run wellbin convert --enhanced-mode
```

## Requirements

- Python 3.9+
- Chrome/Chromium browser (for Selenium)
- ChromeDriver (automatically managed by Selenium)

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## Support

For issues and questions:
- Create an issue on GitHub
- Check the configuration with `uv run wellbin config`
- Verify credentials and network connectivity
