# Configuration Guide

This document provides comprehensive configuration options for the Wellbin Medical Data Downloader.

## Quick Setup

1. Generate a configuration file with defaults:
   ```bash
   uv run wellbin config
   ```

2. Edit the generated `.env` file with your credentials and preferences.

## Configuration Methods

The application supports configuration through:
1. **Environment variables** (`.env` file or system environment)
2. **Command-line arguments** (take precedence over environment variables)

## Environment Variables

### Authentication (Required)

```env
# Your Wellbin platform credentials
WELLBIN_EMAIL=your-email@example.com
WELLBIN_PASSWORD=your-password
```

### Scraper Configuration

```env
# Output directory for downloaded files
WELLBIN_OUTPUT_DIR=medical_data

# Maximum number of studies to download (0 = unlimited)
WELLBIN_STUDY_LIMIT=0

# Types of studies to download: FhirStudy, DicomStudy, or "all"
WELLBIN_STUDY_TYPES=FhirStudy

# Run browser in headless mode (true/false)
WELLBIN_HEADLESS=true
```

### Converter Configuration

```env
# Input directory containing PDFs to convert
WELLBIN_INPUT_DIR=medical_data

# Output directory for converted markdown files
WELLBIN_MARKDOWN_DIR=markdown_reports

# Preserve original directory structure in output (true/false)
WELLBIN_PRESERVE_STRUCTURE=true

# File type filter: lab, imaging, or all
WELLBIN_FILE_TYPE=all

# Enable enhanced mode with advanced features (true/false)
WELLBIN_ENHANCED_MODE=false
```

## Command-Line Arguments

All environment variables can be overridden with command-line arguments:

### Scraper Arguments

```bash
uv run wellbin scrape \
  --email user@example.com \
  --password mypassword \
  --output medical_data \
  --limit 10 \
  --types all \
  --headless \
  --dry-run
```

### Converter Arguments

```bash
uv run wellbin convert \
  --input-dir medical_data \
  --output-dir markdown_reports \
  --file-type lab \
  --enhanced-mode \
  --preserve-structure
```

## Configuration Examples

### Basic Lab Reports Only
```env
WELLBIN_EMAIL=user@example.com
WELLBIN_PASSWORD=mypassword
WELLBIN_STUDY_TYPES=FhirStudy
WELLBIN_STUDY_LIMIT=0
WELLBIN_ENHANCED_MODE=false
```

### All Studies with Enhanced Processing
```env
WELLBIN_EMAIL=user@example.com
WELLBIN_PASSWORD=mypassword
WELLBIN_STUDY_TYPES=all
WELLBIN_STUDY_LIMIT=50
WELLBIN_ENHANCED_MODE=true
WELLBIN_HEADLESS=true
```

### Custom Directory Structure
```env
WELLBIN_EMAIL=user@example.com
WELLBIN_PASSWORD=mypassword
WELLBIN_OUTPUT_DIR=./downloads/medical
WELLBIN_MARKDOWN_DIR=./processed/markdown
WELLBIN_PRESERVE_STRUCTURE=false
```

## Study Types

- **FhirStudy**: Lab reports and clinical data
- **DicomStudy**: Medical imaging reports
- **all**: Both lab reports and imaging

## Enhanced Mode Features

When `WELLBIN_ENHANCED_MODE=true`:
- Page-by-page processing with metadata
- Advanced table detection and extraction
- Word-level positioning data
- Medical report section optimization
- Improved text extraction accuracy

## File Type Filters

- **lab**: Process only lab report PDFs
- **imaging**: Process only imaging report PDFs
- **all**: Process all PDF types

## Security Notes

- Store credentials in `.env` file (not tracked by git)
- Use environment variables in production
- Avoid hardcoding credentials in scripts
- Consider using credential managers for sensitive environments

## Troubleshooting

### Common Issues

1. **Authentication failures**: Verify email/password in `.env`
2. **Browser issues**: Ensure Chrome/Chromium is installed
3. **Permission errors**: Check directory write permissions
4. **Memory issues**: Reduce `WELLBIN_STUDY_LIMIT` for large datasets

### Debug Mode

Enable verbose logging by setting:
```env
WELLBIN_DEBUG=true
```

### Validation

Test your configuration:
```bash
# Dry run to validate settings
uv run wellbin scrape --dry-run

# Check configuration
uv run wellbin config --validate
```
