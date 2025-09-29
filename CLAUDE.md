# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Wellbin Medical Data Downloader is a comprehensive Python tool for downloading and processing medical data from the Wellbin platform. It supports both lab reports (FhirStudy) and medical imaging (DicomStudy) with PDF to Markdown conversion optimized for LLM consumption.

## Development Commands

### Environment Setup

```bash
# Install development dependencies
uv sync --dev

# Install in development mode
uv pip install -e .
```

### Code Quality and Testing
```bash
# Run linting
uv run flake8 wellbin/
uv run black --check wellbin/
uv run isort --check-only wellbin/

# Auto-format code
uv run black wellbin/
uv run isort wellbin/

# Run type checking
uv run pyright wellbin/

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=wellbin --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_utils.py

# Run tests with verbose output
uv run pytest -v

# Run only fast tests (exclude slow tests)
uv run pytest -m "not slow"

# Run integration tests with real medical data
uv run pytest -m integration
uv run pytest tests/test_integration.py
```

### Security and Quality Assurance
```bash
# Security vulnerability scanning
uv run bandit -r wellbin/

# Check for known security vulnerabilities in dependencies
uv run safety check

# Run all pre-commit hooks
uv run pre-commit run --all-files
```

### Debug Mode
```bash
# Enable verbose logging and detailed output
WELLBIN_DEBUG=true uv run wellbin scrape

# Debug mode with dry run for testing
WELLBIN_DEBUG=true uv run wellbin scrape --dry-run
```

### Application Commands
```bash
# Generate configuration file
uv run wellbin config

# Download medical data (with various options)
uv run wellbin scrape
uv run wellbin scrape --types all --limit 10
uv run wellbin scrape --dry-run

# Convert PDFs to markdown
uv run wellbin convert
uv run wellbin convert --enhanced-mode --file-type lab
```

## Architecture Overview

### Core Components

- **wellbin/cli.py**: Main CLI entry point using Click framework
- **wellbin/core/scraper.py**: `WellbinMedicalDownloader` class handles Selenium-based web scraping and PDF downloads
- **wellbin/core/converter.py**: `PDFToMarkdownConverter` class processes PDFs using pymupdf4llm with medical-optimized headers
- **wellbin/core/utils.py**: Utility functions for configuration management and credential validation

### Command Structure

- **wellbin/commands/config.py**: Configuration file generation
- **wellbin/commands/scrape.py**: Medical data downloading with comprehensive CLI options
- **wellbin/commands/convert.py**: PDF to Markdown conversion with enhanced mode support

### Configuration System

The application uses a precedence-based configuration system:
1. Command-line arguments (highest priority)
2. Environment variables (.env file)
3. Built-in defaults (lowest priority)

Key environment variables are prefixed with `WELLBIN_` (e.g., `WELLBIN_EMAIL`, `WELLBIN_STUDY_TYPES`, `WELLBIN_ENHANCED_MODE`).

## Configuration Setup Guide

### Step-by-Step Credential Configuration

**1. Generate Configuration Template:**
```bash
# Create .env file with all available options and comments
uv run wellbin config
```

**2. Alternative: Use .env.example Template:**
```bash
# Copy the example file
cp .env.example .env

# Edit with your preferred editor
nano .env  # or vim .env, code .env, etc.
```

**3. Essential Configuration (Minimum Required):**
```env
# Required: Your Wellbin platform credentials
WELLBIN_EMAIL=your-actual-email@example.com
WELLBIN_PASSWORD=your-actual-password

# Optional: Basic settings (defaults shown)
WELLBIN_OUTPUT_DIR=medical_data
WELLBIN_STUDY_TYPES=FhirStudy
WELLBIN_STUDY_LIMIT=0
```

**4. Validate Configuration:**
```bash
# Test credentials without downloading
uv run wellbin scrape --dry-run

# Enable debug mode for detailed validation
WELLBIN_DEBUG=true uv run wellbin scrape --dry-run
```

### Configuration File Templates

**Basic Lab Reports Only (.env):**
```env
WELLBIN_EMAIL=user@example.com
WELLBIN_PASSWORD=mypassword
WELLBIN_STUDY_TYPES=FhirStudy
WELLBIN_ENHANCED_MODE=false
```

**Complete Medical Data with Enhanced Processing (.env):**
```env
WELLBIN_EMAIL=user@example.com
WELLBIN_PASSWORD=mypassword
WELLBIN_STUDY_TYPES=all
WELLBIN_STUDY_LIMIT=50
WELLBIN_ENHANCED_MODE=true
WELLBIN_HEADLESS=true
WELLBIN_OUTPUT_DIR=medical_data
WELLBIN_MARKDOWN_DIR=markdown_reports
```

### Debug Mode Configuration

**Enable Debug Output:**
```bash
# Set debug mode via environment variable
export WELLBIN_DEBUG=true
uv run wellbin scrape

# Or use inline for single command
WELLBIN_DEBUG=true uv run wellbin scrape --limit 5
```

**Debug Mode Features:**
- Detailed authentication flow logging
- Study filtering and date extraction progress
- S3 URL processing and validation details
- Medical header detection results during conversion
- Browser interaction step-by-step output

### Browser Configuration Options

**Development vs Production Settings:**

**Development (Visible Browser):**
```bash
# See browser actions for debugging
uv run wellbin scrape --no-headless

# Debug mode with visible browser
WELLBIN_DEBUG=true uv run wellbin scrape --no-headless --limit 5
```

**Production (Headless Mode):**
```env
# .env file setting
WELLBIN_HEADLESS=true
```

```bash
# Or via command line
uv run wellbin scrape --headless
```

**Browser Performance Options:**
- **Headless mode**: Faster, less resource usage, no visual feedback
- **Visible mode**: Slower, more resources, allows visual debugging of authentication and navigation
- **User agent**: Automatically set to realistic Chrome user agent string
- **Window size**: Fixed at 1920x1080 for consistency

### Configuration Troubleshooting

**Common Issues:**
- **Empty .env values**: Use quotes for values with spaces: `WELLBIN_EMAIL="user@domain.com"`
- **Boolean values**: Use `true`/`false`, `1`/`0`, `yes`/`no`, or `on`/`off`
- **Path separators**: Use forward slashes on all platforms: `WELLBIN_OUTPUT_DIR=data/medical`
- **Special characters**: Escape special characters in passwords or use quotes

**Configuration Validation:**
```bash
# Check if credentials are properly set
uv run wellbin scrape --dry-run | grep -E "(Email|Password|Credentials)"

# Verify all environment variables are loaded
WELLBIN_DEBUG=true uv run wellbin scrape --dry-run | head -20
```

### Study Type Architecture

Medical data is categorized into two main types:
- **FhirStudy**: Lab reports stored in `lab_reports/` subdirectory
- **DicomStudy**: Medical imaging stored in `imaging_reports/` subdirectory

File naming follows the pattern: `YYYYMMDD-{type}-{counter}.pdf` where type is "lab" or "imaging".

### Enhanced PDF Processing

The converter supports two modes:
- **Standard**: Basic PDF to markdown conversion
- **Enhanced**: Page-by-page processing with embedded metadata, table detection, word-level positioning, and medical header optimization

## Technical Implementation Deep Dive

### Complex Date Extraction System (scraper.py:234-272)

The date extraction uses a sophisticated multi-pattern approach with fallbacks:

**Primary extraction patterns:**
- `MM/DD/YYYY` or `DD/MM/YYYY` format detection with ambiguity resolution
- `YYYY/MM/DD` ISO format parsing
- Natural language formats (`DD Mon YYYY`, `Mon DD, YYYY`)
- Study ID embedded timestamp extraction

**Fallback mechanisms:**
- Page content scanning for date-like patterns
- Study ID parsing for timestamp components
- Default fallback to `20240101` when no date found
- Container text analysis from parent DOM elements

### S3 Pre-signed URL Handling

Downloads bypass authentication using pre-signed S3 URLs:
- Direct S3 bucket access (`wellbin-uploads.s3`) without session cookies
- Automatic URL expiration handling with retry mechanisms
- Streaming downloads with chunk processing (8KB chunks)
- Response validation and error handling for failed downloads

### Study Type Filtering Logic

URL-based filtering system maps study types to medical categories:
- **FhirStudy**: `type=FhirStudy` → lab reports → `lab_reports/` directory
- **DicomStudy**: `type=DicomStudy` → imaging reports → `imaging_reports/` directory
- **"all"**: Processes both FhirStudy and DicomStudy types
- Link discovery uses CSS selectors: `//a[contains(@href, '/study/')]`

### Filename Deduplication System

Counter-based naming prevents overwrites:
- Pattern: `YYYYMMDD-{type}-{counter}.pdf`
- Deduplication key: `{study_type}_{study_date}`
- Per-type counters maintained in `date_counters` dictionary
- Sequential numbering: `20240604-lab-0.pdf`, `20240604-lab-1.pdf`

### Medical Header Detection (converter.py:40-105)

Custom PyMuPDF4LLM header recognition for medical documents:

**Main sections (H2):** PATIENT INFORMATION, LABORATORY RESULTS, CLINICAL FINDINGS
**Subsections (H3):** CHEMISTRY, HEMATOLOGY, LIPID PANEL, CBC
**Parameters (H4):** Any text ending with colon and appropriate font size

Uses font size and styling cues to determine header hierarchy for optimal markdown structure.

## Development Guidelines

### Code Style
- Follow PEP 8 guidelines enforced by Black (line length: 88)
- Use type hints throughout (strict mode with Pyright)
- Import sorting with isort using Black profile

### Error Handling
- Graceful failure with informative error messages
- Comprehensive try-catch blocks in scraper methods
- Progress indicators and status reporting throughout operations

### Testing Strategy

**Test Framework:** Uses pytest with comprehensive coverage reporting and mocking capabilities.

**Test Structure:**
- `tests/test_utils.py`: Core utilities (configuration, validation)
- `tests/test_cli.py`: CLI commands and Click integration
- `tests/test_converter.py`: PDF to markdown conversion
- `tests/test_scraper.py`: Web scraping with Selenium (mocked)

**Test Categories:**
- **Unit tests**: Individual function testing with mocking
- **Integration tests**: Component interaction testing with real medical data
- **CLI tests**: Command-line interface testing with Click's TestRunner
- **Real-world validation**: Tests using actual medical PDFs and converted markdown

**Running Tests:**
```bash
# Run all tests with coverage
uv run pytest --cov=wellbin --cov-report=term-missing

# Run specific test categories
uv run pytest -m "unit"          # Unit tests only
uv run pytest -m "integration"   # Integration tests only
uv run pytest -m "not slow"      # Exclude slow tests

# Debug test failures
uv run pytest -v -s tests/test_utils.py::TestValidateCredentials

# Run real medical data tests (requires medical_data_source/ directory)
uv run pytest tests/test_integration.py -v
```

**Integration Test Features:**
- Uses anonymized Spanish medical reports for realistic testing (lab + imaging)
- Tests medical header detection with authentic document patterns
- Validates filename pattern compliance (YYYYMMDD-type-N.pdf format)
- Checks markdown conversion quality and structure
- Includes fixtures based on real medical data with privacy protection

**Test Fixtures:**
- `tests/fixtures/medical_data/` contains anonymized medical reports
- Lab reports: normal values (recent) and elevated values (older)
- Imaging reports: MRI with findings (recent) and normal CT (older)
- All fixtures maintain authentic Spanish medical terminology
- Safe for public repositories and CI systems

**Test Configuration:**
- Minimum 30% code coverage required (currently achieving 60%+)
- Automatic HTML coverage reports in `htmlcov/`
- Strict marker and configuration validation
- Comprehensive fixture setup in `tests/conftest.py`

**Manual Testing Strategies:**
- Test CLI commands locally with `--dry-run` flag for scraping
- Use debug mode with `WELLBIN_DEBUG=true` environment variable
- Validate configuration before operations using credential validation

## Medical Data Processing Pipeline

1. **Authentication**: Login to Wellbin platform using Selenium WebDriver
2. **Discovery**: Navigate to explorer page and filter studies by type
3. **Date Extraction**: Extract study dates from page content and metadata
4. **Download**: Retrieve PDF files from S3 pre-signed URLs
5. **Organization**: Sort files into structured directories by study type
6. **Conversion**: Process PDFs to LLM-optimized markdown with medical headers

## Error Handling Patterns

### Common Failure Points and Recovery Strategies

**Authentication Failures:**
- Check credentials with `validate_credentials()` function before operations
- Look for "Login failed" messages in output
- Verify `.env` file contains correct `WELLBIN_EMAIL` and `WELLBIN_PASSWORD`
- Test with `--dry-run` flag first

**ChromeDriver/Selenium Issues:**
- Browser crashes: Check Chrome/Chromium installation
- WebDriver exceptions: Selenium automatically manages ChromeDriver versions
- Headless mode problems: Use `--no-headless` flag for debugging
- Timeout errors: Increase implicit wait times in `setup_driver()`

**Network and Download Issues:**
- S3 URL failures: Pre-signed URLs may expire, retry the scraping process
- Connection timeouts: Built-in delays (0.5s between studies, 0.2s between downloads)
- Partial downloads: Check file sizes and retry failed downloads
- Rate limiting: Respect the platform's request limits

**PDF Processing Issues:**
- Memory errors with large files: Process files individually or reduce `--limit`
- PyMuPDF4LLM failures: Check PDF file integrity and permissions
- Enhanced mode crashes: Fall back to standard mode conversion

### Progress Indicators and Status Reporting

The application provides comprehensive status reporting:
- Study discovery progress with counts and filtering results
- Download progress with file sizes and success/failure indicators
- Conversion progress with page counts and feature detection
- Final summaries with file organization details

### Log Analysis for Debugging

**Error logs contain:**
- Selenium WebDriver exceptions and browser state
- Network request failures and response codes
- PDF processing errors with file paths
- Authentication flow details and redirect tracking

**Debug mode output includes:**
- Detailed study filtering logic
- Date extraction attempts and fallbacks
- S3 URL processing and validation
- Medical header detection results

## Performance and Limitations

### Memory Usage Patterns

**Large PDF Processing:**
- Medical PDF files can consume significant RAM during conversion
- Enhanced mode increases memory usage due to word-level extraction and metadata
- PyMuPDF4LLM loads entire documents into memory for processing
- Recommendation: Use `--limit` parameter for testing with large datasets

**Resource Management:**
- Chrome/Chromium browser instances consume ~100-200MB RAM each
- Selenium WebDriver maintains browser state throughout scraping session
- PDF conversion processes files sequentially to manage memory usage
- Temporary file cleanup handled automatically by Python garbage collection

### Built-in Rate Limiting

**Scraping Delays:**
- 0.5 seconds between study page processing (`time.sleep(0.5)` in `scraper.py:738`)
- 0.2 seconds between individual PDF downloads (`time.sleep(0.2)` in `scraper.py:765`)
- 1-3 second delays during authentication and page navigation
- Respectful of Wellbin platform resources to avoid overwhelming servers

**Browser Performance:**
- Headless mode (`--headless`) reduces resource consumption significantly
- Visible browser mode (`--no-headless`) useful for debugging but slower
- WebDriver implicit wait set to 10 seconds, explicit waits up to 15 seconds
- Browser cleanup handled in `finally` block to prevent resource leaks

### Concurrency Limitations

**Single-threaded Design:**
- Sequential processing of studies and downloads (no parallel execution)
- One browser session per scraping operation
- PDF conversion processes files one at a time
- Design prevents overwhelming target servers and ensures data integrity

**Selenium WebDriver Constraints:**
- Single Chrome instance per downloader session
- Browser state maintained throughout operation for authentication
- No concurrent browser sessions to avoid authentication conflicts
- Resource cleanup requires proper session termination

### Platform Rate Limiting Considerations

**Wellbin Platform Limits:**
- S3 pre-signed URLs have expiration times (retry needed if expired)
- Authentication sessions may timeout during long operations
- Respect platform's terms of service and usage policies
- Monitor for HTTP 429 (Too Many Requests) responses

**Scaling Recommendations:**
- Use reasonable `--limit` values for large datasets (e.g., 50-100 studies)
- Process data in batches rather than attempting full downloads
- Consider implementing exponential backoff for retry logic
- Monitor system resources during large operations

## Project Files Documentation

### Pre-commit Configuration (.pre-commit-config.yaml)

**Purpose:** Automated code quality enforcement using Git pre-commit hooks.

**Local Hooks (using uv):**
- **black**: Code formatting with `uv run black`
- **isort**: Import sorting with `uv run isort --profile black`
- **flake8**: Linting with `uv run flake8` (excludes `.venv/`)

**External Hooks:**
- **trailing-whitespace**: Remove trailing whitespace
- **end-of-file-fixer**: Ensure files end with newline
- **check-yaml**: Validate YAML syntax
- **check-added-large-files**: Prevent large file commits
- **check-merge-conflict**: Detect merge conflict markers

**Setup and Usage:**
```bash
# Install pre-commit (already in dev dependencies)
uv sync --dev

# Install Git hooks
uv run pre-commit install

# Run hooks on all files manually
uv run pre-commit run --all-files

# Hooks run automatically on git commit
git commit -m "your message"  # Triggers automatic checks
```

## Comprehensive Troubleshooting Guide

### ChromeDriver and Selenium Issues

**Installation Problems:**
```bash
# Check Chrome/Chromium installation
google-chrome --version  # or chromium --version

# Selenium automatically manages ChromeDriver, but verify installation
uv run python -c "from selenium import webdriver; print('Selenium installed correctly')"
```

**Common ChromeDriver Errors:**
- **"ChromeDriver not found"**: Selenium 4.15+ auto-manages drivers, ensure Chrome is installed
- **Version mismatch**: Update Chrome browser to latest version
- **Permission errors**: Run with appropriate permissions, avoid running as root
- **Display issues on headless systems**: Use `DISPLAY=:99` or ensure Xvfb is available

**Browser Session Problems:**
```bash
# Test browser creation manually
uv run python -c "
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
options = Options()
options.add_argument('--headless')
driver = webdriver.Chrome(options=options)
print('Browser created successfully')
driver.quit()
"
```

### Authentication and Credential Issues

**Credential Validation Failures:**
- **Default values detected**: Ensure `.env` doesn't contain `your-email@example.com`
- **Special characters in password**: Wrap password in quotes: `WELLBIN_PASSWORD="pass@word!"`
- **Environment variables not loaded**: Check `.env` file location (must be in working directory)
- **Case sensitivity**: Verify exact email address (case matters for some systems)

**Authentication Flow Problems:**
```bash
# Debug authentication step-by-step
WELLBIN_DEBUG=true uv run wellbin scrape --no-headless --dry-run

# Check login form detection
uv run wellbin scrape --no-headless --limit 1  # Watch browser manually
```

**Session Management:**
- **Session timeouts**: Reduce `--limit` for long operations
- **Multiple login attempts**: Clear browser data, restart scraping process
- **Redirect loops**: Check if account requires 2FA or additional verification

### Network and Connection Issues

**Download Failures:**
```bash
# Test network connectivity to Wellbin
curl -I https://wellbin.co

# Check S3 access (if you have a sample URL)
curl -I "https://wellbin-uploads.s3.amazonaws.com/"
```

**Connection Timeouts:**
- **Slow networks**: Increase timeout values in `scraper.py` if needed
- **Intermittent failures**: Enable debug mode to see retry attempts
- **Proxy issues**: Configure browser proxy settings if behind corporate firewall
- **DNS resolution**: Verify access to `wellbin.co` and AWS S3 endpoints

**S3 URL Expiration:**
- **Pre-signed URL expired**: Retry the entire scraping process
- **Invalid S3 URLs**: Check if study page structure changed
- **403 Forbidden errors**: Verify Wellbin session is still active

### Memory and Performance Issues

**Large PDF Processing:**
```bash
# Monitor memory usage during conversion
top -p $(pgrep -f "wellbin convert")

# Process files individually for memory-constrained systems
uv run wellbin convert --file-type lab  # Process only lab reports first
uv run wellbin convert --file-type imaging  # Then imaging reports
```

**Memory Exhaustion:**
- **Enhanced mode memory issues**: Disable enhanced mode: `WELLBIN_ENHANCED_MODE=false`
- **Large datasets**: Use `--limit 10` for testing, batch process larger datasets
- **Browser memory leaks**: Restart scraping process periodically for large operations
- **PDF conversion crashes**: Process PDFs in smaller batches

**Browser Resource Issues:**
```bash
# Clean up any stuck browser processes
pkill -f chrome
pkill -f chromium

# Monitor browser resource usage
ps aux | grep -E "(chrome|chromium)"
```

### File System and Permission Issues

**Directory Creation Failures:**
```bash
# Check write permissions
ls -la $(dirname "$PWD/medical_data")

# Create directories manually if needed
mkdir -p medical_data/lab_reports medical_data/imaging_reports
```

**File Access Problems:**
- **Permission denied**: Ensure write access to output directories
- **Disk space**: Check available space: `df -h`
- **Path length limits**: Use shorter directory names on Windows
- **Special characters**: Avoid special characters in file paths

### Recovery Strategies

**Partial Download Recovery:**
1. **Check existing files**: `ls -la medical_data/*/`
2. **Resume with smaller limit**: `uv run wellbin scrape --limit 5`
3. **Skip completed studies**: Manually remove successfully downloaded PDFs from consideration

**Browser Session Recovery:**
```bash
# Kill all browser processes
pkill -f chrome

# Clear temporary files
rm -rf /tmp/.org.chromium.* 2>/dev/null || true

# Restart scraping with clean session
uv run wellbin scrape --limit 5
```

**Configuration Reset:**
```bash
# Backup current config
cp .env .env.backup

# Regenerate clean configuration
uv run wellbin config

# Restore credentials from backup
```

### Debugging Command Reference

**Essential Debugging Commands:**
```bash
# Full debug mode with visible browser
WELLBIN_DEBUG=true uv run wellbin scrape --no-headless --limit 1

# Network and authentication debugging
WELLBIN_DEBUG=true uv run wellbin scrape --dry-run

# PDF conversion debugging
WELLBIN_DEBUG=true uv run wellbin convert --file-type lab

# System resource monitoring
htop  # or top
df -h  # disk space
free -h  # memory usage
```

## Security Considerations

- Credentials handled through environment variables, never hardcoded
- Browser automation uses appropriate user agents and delays
- File downloads validate response status and handle streaming properly
- No sensitive data logged or exposed in debug output

## Git Commit Guidelines

- Never include references to Claude or AI assistance in commit messages
- Focus on technical changes and functional improvements
- Use conventional commit format when possible
- Keep commit messages concise and descriptive of the actual changes made
