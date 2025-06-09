# Development Guide

This guide covers development setup, testing, and contributing to the Wellbin Medical Data Downloader.

## Development Setup

### Prerequisites

- Python 3.9+
- Chrome/Chromium browser (for Selenium)
- ChromeDriver (automatically managed by Selenium)
- uv package manager

### Installation

```bash
# Clone the repository
git clone <repository-url> wellbin
cd wellbin

# Install development dependencies
uv sync --dev

# Install in development mode
uv pip install -e .
```

## Package Structure

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

## Development Workflow

### Code Quality

```bash
# Run linting
uv run flake8 wellbin/
uv run black --check wellbin/
uv run isort --check-only wellbin/

# Auto-format code
uv run black wellbin/
uv run isort wellbin/

# Run type checking
uv run mypy wellbin/
```

### Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=wellbin

# Run specific test file
uv run pytest tests/test_scraper.py

# Run with verbose output
uv run pytest -v
```

### Local Development

```bash
# Test CLI commands locally
uv run wellbin config
uv run wellbin scrape --dry-run
uv run wellbin convert --help

# Debug mode
WELLBIN_DEBUG=true uv run wellbin scrape
```

## Migration from Old Scripts

If you were using the old standalone scripts, here's how to migrate:

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

## Contributing

### Getting Started

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes
4. Run tests and linting
5. Commit your changes: `git commit -am 'Add some feature'`
6. Push to the branch: `git push origin feature/your-feature-name`
7. Submit a pull request

### Code Standards

- Follow PEP 8 style guidelines
- Use type hints for all functions
- Write docstrings for public functions and classes
- Add tests for new functionality
- Update documentation as needed

### Commit Messages

Use conventional commit format:
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `test:` for test additions/changes
- `refactor:` for code refactoring

### Pull Request Process

1. Ensure all tests pass
2. Update documentation if needed
3. Add tests for new functionality
4. Ensure code coverage doesn't decrease
5. Request review from maintainers

## Architecture

### Core Components

- **WellbinMedicalScraper**: Handles authentication and data downloading
- **PDFToMarkdownConverter**: Processes PDFs into LLM-optimized markdown
- **CLI Commands**: User-facing command interface
- **Configuration**: Environment variable and argument handling

### Design Principles

- **Separation of Concerns**: Each module has a single responsibility
- **Configuration Flexibility**: Support both env vars and CLI args
- **Error Handling**: Graceful failure with informative messages
- **Extensibility**: Easy to add new study types or output formats

## Debugging

### Common Development Issues

1. **Selenium WebDriver Issues**
   ```bash
   # Update ChromeDriver
   uv run python -c "from selenium import webdriver; webdriver.Chrome()"
   ```

2. **PDF Processing Issues**
   ```bash
   # Test with single file
   uv run wellbin convert --input-dir test_pdfs --file-type lab
   ```

3. **Authentication Issues**
   ```bash
   # Test credentials
   uv run wellbin scrape --dry-run --email test@example.com
   ```

### Debug Mode

Enable detailed logging:
```bash
export WELLBIN_DEBUG=true
uv run wellbin scrape
```

## Release Process

### Version Management

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create git tag: `git tag v1.0.0`
4. Push tag: `git push origin v1.0.0`

### Building and Publishing

```bash
# Build package
uv build

# Test installation
uv pip install dist/wellbin-*.whl

# Publish to PyPI (maintainers only)
uv publish
```

## Performance Considerations

### Memory Usage

- Large PDF files can consume significant memory
- Use `--limit` option for testing with large datasets
- Monitor memory usage during development

### Browser Performance

- Headless mode is faster for production
- Use `--no-headless` for debugging
- Consider browser cleanup in long-running processes

## Security

### Credential Handling

- Never commit credentials to version control
- Use environment variables for sensitive data
- Consider credential rotation for production use

### Web Scraping Ethics

- Respect rate limits and server resources
- Use appropriate delays between requests
- Follow the platform's terms of service

## Support and Maintenance

### Issue Triage

1. Reproduce the issue locally
2. Check for existing similar issues
3. Gather system information and logs
4. Provide minimal reproduction case

### Documentation Updates

- Keep README.md user-focused
- Update CONFIG.md for new configuration options
- Update this DEVELOPMENT.md for process changes
- Add inline code documentation

## Future Enhancements

### Planned Features

- Support for additional medical platforms
- Enhanced PDF processing algorithms
- Batch processing improvements
- API integration options

### Technical Debt

- Improve error handling consistency
- Add more comprehensive test coverage
- Optimize PDF processing performance
- Enhance configuration validation
