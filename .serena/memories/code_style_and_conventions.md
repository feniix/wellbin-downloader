# Code Style and Conventions

## Python Code Style

### PEP 8 Compliance
- Follow PEP 8 guidelines enforced by Black formatter
- Line length: 88 characters (Black default)
- Target Python version: 3.9+

### Formatting Tools (Ruff v0.8.0+)
- **Ruff**: Fast, unified linting and formatting tool
  - Replaces: Black, isort, flake8, and other individual tools
  - Configuration: `pyproject.toml` [tool.ruff] section
  - Line length: 120 characters
  - **ruff format**: Code formatting
  - **ruff check**: Linting with auto-fix capability (`--fix` flag)
  - **ruff check --watch**: Watch mode for development

### Type Hints
- **Strict type checking** with Pyright
- Use type hints throughout the codebase
- Type checking mode: strict
- All functions should have type annotations for parameters and return values

### Import Organization
- Ruff automatically handles import organization
- Configured via isort compatibility in `[tool.ruff.isort]` section
- Imports automatically organized by `ruff check --fix`
- No separate isort step needed

### Naming Conventions
- **Classes**: PascalCase (e.g., `WellbinMedicalDownloader`, `PDFToMarkdownConverter`)
- **Functions/Methods**: snake_case (e.g., `extract_study_dates`, `convert_pdf_to_markdown`)
- **Variables**: snake_case (e.g., `study_type`, `output_dir`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `WELLBIN_EMAIL`, `DEFAULT_TIMEOUT`)
- **Private methods**: Leading underscore (e.g., `_internal_method`)

### Docstrings
- Use descriptive docstrings for classes and public methods
- Follow Google or NumPy docstring format
- Include parameter types and return types in docstrings

### Error Handling
- Graceful failure with informative error messages
- Comprehensive try-catch blocks in scraper methods
- Progress indicators and status reporting throughout operations
- Log errors with context for debugging

### Code Organization
- Keep related functionality together
- Separate concerns: CLI, core logic, utilities
- Use classes for stateful operations (scraper, converter)
- Use functions for stateless utilities (configuration, validation)

## Project-Specific Conventions

### Configuration Management
- Environment variables prefixed with `WELLBIN_`
- Precedence: CLI args > env vars > defaults
- Use `python-dotenv` for .env file loading
- Validate credentials before operations

### File Naming
- Medical files: `YYYYMMDD-{type}-{counter}.pdf` format
- Type values: "lab" or "imaging"
- Counter-based deduplication per date and type

### Directory Structure
- Lab reports: `lab_reports/` subdirectory
- Imaging reports: `imaging_reports/` subdirectory
- Markdown output: `{type}_markdown/` subdirectories

### Medical Data Handling
- Study types: FhirStudy (lab), DicomStudy (imaging)
- Date extraction with multiple fallback patterns
- S3 pre-signed URL handling for downloads
- Medical header detection for markdown conversion

## Testing Conventions

### Test Structure
- Test files: `test_*.py` pattern
- Test classes: `Test*` pattern
- Test functions: `test_*` pattern
- Use pytest fixtures for common setup

### Test Categories
- **Unit tests**: Individual function testing with mocking (marker: `unit`)
- **Integration tests**: Component interaction testing (marker: `integration`)
- **Slow tests**: Long-running tests (marker: `slow`)

### Coverage Requirements
- Minimum 30% code coverage required
- Current coverage: 60%+
- HTML coverage reports in `htmlcov/`

### Test Data
- Use anonymized medical data in `tests/fixtures/`
- Spanish medical terminology maintained
- Safe for public repositories

## Git Commit Guidelines
- Never include references to Claude or AI assistance in commit messages
- Focus on technical changes and functional improvements
- Use conventional commit format when possible
- Keep commit messages concise and descriptive of the actual changes made

## Pre-commit Hooks
Automated checks run on every commit:
- **ruff lint**: Fast linting with auto-fix (replaces flake8, pylint, etc.)
- **ruff format**: Code formatting (replaces Black)
  - Automatically handles import sorting (replaces isort)
  - Line length: 120 characters
  - Includes all code quality checks
- **trailing-whitespace**: Remove trailing whitespace
- **end-of-file-fixer**: Ensure files end with newline
- **check-yaml**: Validate YAML syntax
- **check-toml**: Validate TOML files (pyproject.toml)
- **check-json**: Validate JSON files
- **check-added-large-files**: Prevent large file commits
- **check-merge-conflict**: Detect merge conflict markers
- **mixed-line-ending**: Enforce LF line endings
- **python-check-blanket-noqa**: Prevent blanket `# noqa` comments
- **python-check-blanket-type-ignore**: Prevent blanket `# type: ignore` comments
- **python-use-type-annotations**: Enforce type annotations over type comments
