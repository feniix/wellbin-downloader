# Wellbin Medical Data Downloader - Project Overview

## Purpose
Wellbin Medical Data Downloader is a comprehensive Python tool for downloading and processing medical data from the Wellbin platform. It supports both lab reports (FhirStudy) and medical imaging (DicomStudy) with PDF to Markdown conversion optimized for LLM consumption.

## Key Features
- **Universal Medical Data Downloader**: Download lab reports and medical imaging from Wellbin
- **Intelligent PDF Processing**: Convert medical PDFs to LLM-optimized markdown
- **Enhanced Mode**: Page chunking, table detection, and word-level extraction
- **Medical-Optimized Headers**: Automatic detection of medical report sections
- **Flexible Configuration**: Environment variables + command-line arguments
- **Structured Output**: Organized directories with proper categorization

## Tech Stack
- **Language**: Python 3.9+
- **Package Manager**: uv (mandatory - never use pip or python directly)
- **CLI Framework**: Click
- **Web Scraping**: Selenium WebDriver with Chrome/Chromium
- **PDF Processing**: pymupdf4llm for medical-optimized conversion
- **Configuration**: python-dotenv for environment variable management
- **Testing**: pytest with coverage, mocking, and integration tests
- **Code Quality**: Black, isort, flake8, pyright, bandit, safety
- **Pre-commit Hooks**: Automated code quality enforcement

## Architecture Components

### Core Modules
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

## Medical Data Processing Pipeline
1. **Authentication**: Login to Wellbin platform using Selenium WebDriver
2. **Discovery**: Navigate to explorer page and filter studies by type
3. **Date Extraction**: Extract study dates from page content and metadata
4. **Download**: Retrieve PDF files from S3 pre-signed URLs
5. **Organization**: Sort files into structured directories by study type
6. **Conversion**: Process PDFs to LLM-optimized markdown with medical headers

## Study Type Architecture
Medical data is categorized into two main types:
- **FhirStudy**: Lab reports stored in `lab_reports/` subdirectory
- **DicomStudy**: Medical imaging stored in `imaging_reports/` subdirectory

File naming follows the pattern: `YYYYMMDD-{type}-{counter}.pdf` where type is "lab" or "imaging".
