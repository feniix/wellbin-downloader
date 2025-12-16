# Codebase Structure

## Directory Layout

```
wellbin/
├── wellbin/                    # Main package
│   ├── __init__.py
│   ├── cli.py                 # CLI entry point (Click framework)
│   ├── commands/              # CLI command implementations
│   │   ├── __init__.py
│   │   ├── config.py         # Configuration file generation
│   │   ├── scrape.py         # Medical data downloading
│   │   └── convert.py        # PDF to Markdown conversion
│   └── core/                  # Core business logic
│       ├── __init__.py
│       ├── scraper.py        # WellbinMedicalDownloader class
│       ├── converter.py      # PDFToMarkdownConverter class
│       └── utils.py          # Utility functions
├── tests/                     # Test suite
│   ├── __init__.py
│   ├── conftest.py           # Pytest configuration and fixtures
│   ├── fixtures/             # Test fixtures
│   │   ├── medical_data/     # Anonymized medical data
│   │   ├── medical_fixtures.py
│   │   └── README.md
│   ├── test_cli.py           # CLI tests
│   ├── test_converter.py     # Converter tests
│   ├── test_integration.py   # Integration tests
│   ├── test_scraper.py       # Scraper tests
│   └── test_utils.py         # Utility tests
├── medical_data/              # Downloaded PDFs (generated)
│   ├── lab_reports/
│   └── imaging_reports/
├── medical_data_markdown/     # Converted markdown (generated)
│   ├── lab_reports_markdown/
│   └── imaging_reports_markdown/
├── medical_data_source/       # Source medical data
│   ├── lab_reports/
│   └── imaging_reports/
├── scripts/                   # Utility scripts
│   └── typecheck.sh
├── htmlcov/                   # Coverage reports (generated)
├── .pre-commit-config.yaml    # Pre-commit hooks configuration
├── pyproject.toml             # Project configuration and dependencies
├── uv.lock                    # Dependency lock file
├── README.md                  # User documentation
├── CLAUDE.md                  # Development guide
├── CONFIG.md                  # Configuration documentation
├── DEVELOPMENT.md             # Development documentation
└── LICENSE                    # MIT License
```

## Core Modules

### wellbin/cli.py
- Main CLI entry point using Click framework
- Functions:
  - `cli()`: Main CLI group
  - `main()`: Entry point for console script

### wellbin/core/scraper.py
- `WellbinMedicalDownloader` class
- Methods:
  - `__init__()`: Initialize downloader with configuration
  - `setup_driver()`: Configure Selenium WebDriver
  - `login()`: Authenticate with Wellbin platform
  - `extract_study_dates_from_explorer()`: Extract dates from explorer page
  - `parse_date_from_text()`: Parse date from text content
  - `extract_date_from_study_id()`: Extract date from study ID
  - `extract_dates_for_studies()`: Batch date extraction
  - `extract_date_from_study_page()`: Extract date from individual study page
  - `get_study_links()`: Discover study links
  - `get_pdf_from_study()`: Extract PDF URL from study page
  - `generate_filename()`: Generate unique filename with deduplication
  - `download_pdf()`: Download PDF from S3 URL
  - `scrape_studies()`: Main scraping orchestration

### wellbin/core/converter.py
- `PDFToMarkdownConverter` class
- Methods:
  - `__init__()`: Initialize converter with configuration
  - `medical_header_detector()`: Custom header detection for medical documents
  - `extract_enhanced_markdown()`: Enhanced extraction with metadata
  - `save_enhanced_chunks()`: Save page-by-page chunks
  - `convert_pdf_to_markdown()`: Main conversion method
  - `convert_all_pdfs()`: Batch conversion
- Functions:
  - `convert_structured_directories()`: Convert organized directory structure

### wellbin/core/utils.py
- Utility functions:
  - `get_env_default()`: Get environment variable with default
  - `get_env_or_default()`: Get environment variable or default value
  - `create_config_file()`: Generate .env configuration file
  - `validate_credentials()`: Validate user credentials

### wellbin/commands/
- **config.py**: Configuration file generation command
- **scrape.py**: Medical data downloading command with CLI options
- **convert.py**: PDF to Markdown conversion command with CLI options

## Test Structure

### Test Files
- **test_utils.py**: Core utilities (configuration, validation)
- **test_cli.py**: CLI commands and Click integration
- **test_converter.py**: PDF to markdown conversion
- **test_scraper.py**: Web scraping with Selenium (mocked)
- **test_integration.py**: Component interaction testing with real medical data

### Test Fixtures
- **conftest.py**: Pytest configuration and shared fixtures
- **fixtures/medical_data/**: Anonymized Spanish medical reports
  - Lab reports: normal values (recent) and elevated values (older)
  - Imaging reports: MRI with findings (recent) and normal CT (older)
- **fixtures/medical_fixtures.py**: Fixture helper functions

## Configuration Files

### pyproject.toml
- Project metadata and dependencies
- Tool configurations:
  - Black (formatting)
  - isort (import sorting)
  - flake8 (linting)
  - pytest (testing)
  - pyright (type checking)
- Build system: hatchling
- Console script entry point: `wellbin = "wellbin.cli:main"`

### .pre-commit-config.yaml
- Pre-commit hooks configuration
- Local hooks: black, isort, flake8
- External hooks: trailing-whitespace, end-of-file-fixer, check-yaml, check-added-large-files, check-merge-conflict

### uv.lock
- Dependency lock file managed by uv
- Ensures reproducible builds

## Generated Directories

### medical_data/
- Downloaded PDF files organized by type
- Subdirectories: `lab_reports/`, `imaging_reports/`
- Filename pattern: `YYYYMMDD-{type}-{counter}.pdf`

### medical_data_markdown/
- Converted markdown files
- Subdirectories: `lab_reports_markdown/`, `imaging_reports_markdown/`
- Filename pattern: `YYYYMMDD-{type}-{counter}.md`

### htmlcov/
- HTML coverage reports generated by pytest-cov
- View in browser: `htmlcov/index.html`

## Key Design Patterns

### Configuration Precedence
1. Command-line arguments (highest)
2. Environment variables (.env)
3. Built-in defaults (lowest)

### Date Extraction Fallbacks
1. MM/DD/YYYY or DD/MM/YYYY format
2. YYYY/MM/DD ISO format
3. Natural language formats
4. Study ID embedded timestamp
5. Page content scanning
6. Default fallback: 20240101

### Filename Deduplication
- Counter-based naming: `YYYYMMDD-{type}-{counter}.pdf`
- Deduplication key: `{study_type}_{study_date}`
- Per-type counters in `date_counters` dictionary

### Medical Header Detection
- H2: Main sections (PATIENT INFORMATION, LABORATORY RESULTS)
- H3: Subsections (CHEMISTRY, HEMATOLOGY, LIPID PANEL)
- H4: Parameters (text ending with colon)
- Font size and styling cues for hierarchy
