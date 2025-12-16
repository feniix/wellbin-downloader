# Onboarding Summary - Wellbin Medical Data Downloader

## Quick Reference

This document provides a quick reference to all onboarding information. For detailed information, refer to the specific memory files listed below.

## Memory Files Created

1. **project_overview.md**
   - Project purpose and key features
   - Tech stack and architecture
   - Core components and configuration system
   - Medical data processing pipeline

2. **suggested_commands.md**
   - Essential commands for development
   - Testing, linting, formatting commands
   - Application usage commands
   - Debug mode and system utilities

3. **code_style_and_conventions.md**
   - Python code style (PEP 8, Black, isort)
   - Type hints and naming conventions
   - Error handling patterns
   - Testing conventions
   - Git commit guidelines

4. **task_completion_checklist.md**
   - Step-by-step checklist for completing tasks
   - Code quality checks
   - Testing requirements
   - Security checks
   - Pre-commit hooks
   - Manual testing procedures

5. **codebase_structure.md**
   - Directory layout
   - Core modules and their responsibilities
   - Test structure
   - Configuration files
   - Generated directories
   - Key design patterns

6. **system_specific_notes.md**
   - macOS/Darwin specific information
   - GNU toolchain usage
   - Process management
   - Development server (port 8000)
   - Browser and Selenium notes
   - File system and network utilities

7. **design_patterns_and_guidelines.md**
   - Architecture patterns
   - Medical data processing patterns
   - Code organization patterns
   - Testing patterns
   - Performance patterns
   - Security patterns
   - Common patterns to follow
   - Anti-patterns to avoid

## Critical Information

### Must-Know Rules
1. **ALWAYS use `uv run` for Python commands** - Never use `pip`, `python`, or `python3` directly
2. **Pre-commit hooks are mandatory** - They run automatically on commit
3. **Minimum 30% test coverage** - Currently achieving 60%+
4. **Type hints are required** - Strict type checking with Pyright
5. **Environment variables prefix**: `WELLBIN_*` for all configuration

### Quick Start for Development
```bash
# Setup
uv sync --dev

# Before committing (using Ruff)
uv run ruff format wellbin/
uv run ruff check --fix wellbin/
uv run pyright wellbin/
uv run pytest --cov=wellbin

# Or use pre-commit hooks (runs all checks automatically)
uv run pre-commit run --all-files
```

### Application Usage
```bash
# Generate config
uv run wellbin config

# Download medical data
uv run wellbin scrape --types all --limit 10

# Convert to markdown
uv run wellbin convert --enhanced-mode
```

### Debug Mode
```bash
# Enable debug output
WELLBIN_DEBUG=true uv run wellbin scrape --dry-run

# Visible browser for debugging
WELLBIN_DEBUG=true uv run wellbin scrape --no-headless --limit 1
```

## Project Structure Summary

```
wellbin/
├── wellbin/              # Main package
│   ├── cli.py           # CLI entry point
│   ├── commands/        # CLI commands (config, scrape, convert)
│   └── core/            # Core logic (scraper, converter, utils)
├── tests/               # Test suite
│   ├── fixtures/        # Test data
│   └── test_*.py        # Test files
├── medical_data/        # Downloaded PDFs (generated)
├── medical_data_markdown/  # Converted markdown (generated)
└── pyproject.toml       # Project configuration
```

## Key Classes and Functions

### Core Classes
- **WellbinMedicalDownloader**: Selenium-based web scraping and PDF downloads
- **PDFToMarkdownConverter**: PDF to markdown conversion with medical optimization

### Key Functions
- **get_env_or_default()**: Configuration retrieval
- **validate_credentials()**: Credential validation
- **convert_structured_directories()**: Batch directory conversion

## Configuration Precedence
1. Command-line arguments (highest)
2. Environment variables (.env)
3. Built-in defaults (lowest)

## Medical Data Types
- **FhirStudy**: Lab reports → `lab_reports/`
- **DicomStudy**: Medical imaging → `imaging_reports/`

## File Naming Pattern
`YYYYMMDD-{type}-{counter}.pdf`
- Example: `20240604-lab-0.pdf`, `20240604-imaging-1.pdf`

## Testing Categories
- **unit**: Individual function tests with mocking
- **integration**: Component interaction with real data
- **slow**: Long-running tests (exclude with `-m "not slow"`)

## Common Commands Reference

### Testing
```bash
uv run pytest                           # All tests
uv run pytest -m "not slow"            # Fast tests only
uv run pytest tests/test_utils.py      # Specific file
```

### Code Quality (Ruff-based)
```bash
uv run ruff format wellbin/            # Format (includes import sorting)
uv run ruff check --fix wellbin/       # Lint and auto-fix
uv run pyright wellbin/                # Type check
```

### Security
```bash
uv run bandit -r wellbin/              # Security scan
uv run safety check                    # Dependency vulnerabilities
```

### Pre-commit
```bash
uv run pre-commit install              # Setup hooks
uv run pre-commit run --all-files      # Run manually
```

## System Specifics (macOS)
- **Shell**: zsh
- **Dev server port**: 8000
- **Find server**: `lsof -i :8000`
- **GNU toolchain**: Standard GNU commands available

## Next Steps

1. Read through the specific memory files for detailed information
2. Run `uv sync --dev` to set up the development environment
3. Install pre-commit hooks: `uv run pre-commit install`
4. Try running tests: `uv run pytest`
5. Generate a config file: `uv run wellbin config`
6. Review the codebase structure in your editor

## Getting Help

- Check `CLAUDE.md` for comprehensive development guide
- Review `README.md` for user documentation
- Check `CONFIG.md` for configuration details
- Look at test files for usage examples
- Use debug mode for troubleshooting: `WELLBIN_DEBUG=true`

## Onboarding Complete

All necessary information has been captured in the memory files. You can now start working on the project with a solid understanding of:
- Project purpose and architecture
- Development commands and workflows
- Code style and conventions
- Testing requirements
- System-specific considerations
- Design patterns and best practices

Refer to the specific memory files for detailed information on each topic.
