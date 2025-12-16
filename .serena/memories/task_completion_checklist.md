# Task Completion Checklist

## When a Task is Completed

### 1. Code Quality Checks (Ruff-based)

#### Formatting and Linting Combined
```bash
# Auto-format code and fix linting errors
uv run ruff format wellbin/
uv run ruff check --fix wellbin/

# Or do both in one command via pre-commit
uv run pre-commit run --all-files
```

#### Checking Without Fixing
```bash
# Check code quality without modifying
uv run ruff check wellbin/

# Verify formatting without modifying
uv run ruff format --check wellbin/
```

#### Type Checking
```bash
# Run strict type checking
uv run pyright wellbin/
```

### 2. Testing

#### Run Tests
```bash
# Run all tests with coverage
uv run pytest --cov=wellbin --cov-report=term-missing

# Ensure minimum 30% coverage is met
# Current target: 60%+
```

#### Test Specific Areas
```bash
# If you modified core utilities
uv run pytest tests/test_utils.py

# If you modified CLI commands
uv run pytest tests/test_cli.py

# If you modified converter
uv run pytest tests/test_converter.py

# If you modified scraper
uv run pytest tests/test_scraper.py

# If you modified integration points
uv run pytest tests/test_integration.py -v
```

### 3. Security Checks

```bash
# Security vulnerability scanning
uv run bandit -r wellbin/

# Check for known security vulnerabilities in dependencies
uv run safety check
```

### 4. Pre-commit Hooks

```bash
# Run all pre-commit hooks manually
uv run pre-commit run --all-files

# This will run:
# - ruff check (unified linting - replaces flake8, pylint, etc.)
# - ruff format (code formatting + import sorting - replaces Black/isort)
# - trailing-whitespace
# - end-of-file-fixer
# - check-yaml
# - check-toml
# - check-json
# - check-added-large-files
# - check-merge-conflict
# - mixed-line-ending
# - python-check-blanket-noqa
# - python-check-blanket-type-ignore
# - python-use-type-annotations
```

### 5. Manual Testing (if applicable)

#### Configuration Testing
```bash
# Test configuration generation
uv run wellbin config

# Validate credentials
uv run wellbin scrape --dry-run
```

#### Scraper Testing
```bash
# Test scraping with debug mode
WELLBIN_DEBUG=true uv run wellbin scrape --limit 1 --dry-run

# Test with visible browser for debugging
WELLBIN_DEBUG=true uv run wellbin scrape --no-headless --limit 1
```

#### Converter Testing
```bash
# Test PDF conversion
uv run wellbin convert --file-type lab

# Test enhanced mode
uv run wellbin convert --enhanced-mode --file-type lab
```

### 6. Documentation

- Update CLAUDE.md if architecture changes
- Update README.md if user-facing features change
- Update CONFIG.md if configuration options change
- Add docstrings to new functions/classes
- Update type hints

### 7. Git Operations

```bash
# Stage changes
git add <files>

# Commit with descriptive message
git commit -m "descriptive message"
# Note: Pre-commit hooks will run automatically

# If hooks fail, fix issues and commit again
```

## Quick Checklist

- [ ] Code formatted with `ruff format`
- [ ] No linting errors from `ruff check`
- [ ] Type checking passes with `pyright`
- [ ] All tests pass with `pytest`
- [ ] Coverage meets minimum threshold (30%+)
- [ ] Security checks pass (`bandit`, `safety`)
- [ ] Pre-commit hooks pass (`uv run pre-commit run --all-files`)
- [ ] Manual testing completed (if applicable)
- [ ] Documentation updated (if needed)
- [ ] Git commit with proper message

## Common Issues and Fixes

### Formatting and Linting Issues
```bash
# Auto-fix formatting issues
uv run ruff format wellbin/

# Auto-fix linting errors
uv run ruff check --fix wellbin/

# Or use pre-commit to fix both
uv run pre-commit run --all-files
```

### Import Errors
```bash
# Check if dependencies are installed
uv sync --dev
```

### Test Failures
```bash
# Run with verbose output to see details
uv run pytest -v -s

# Run specific failing test
uv run pytest tests/test_file.py::test_function -v
```

### Type Checking Errors
```bash
# Run pyright to see detailed errors
uv run pyright wellbin/

# Add type hints or type: ignore comments as needed
```

## Notes

- **Always use `uv run` for Python commands**
- **Never commit without running pre-commit hooks**
- **Ensure tests pass before committing**
- **Keep coverage above 30% minimum**
- **Use debug mode for manual testing**
