# Suggested Commands for Wellbin Project

## CRITICAL: Package Management
**ALWAYS use `uv` for Python package management and execution**
**NEVER use `pip`, `python`, `python3`, or `pipenv` directly**

## Environment Setup
```bash
# Install development dependencies
uv sync --dev

# Install in development mode
uv pip install -e .
```

## Application Commands
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

## Testing Commands
```bash
# Run all tests with coverage
uv run pytest

# Run tests with detailed coverage report
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

# Debug test failures
uv run pytest -v -s tests/test_utils.py::TestValidateCredentials
```

## Code Quality Commands
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

# Security vulnerability scanning
uv run bandit -r wellbin/

# Check for known security vulnerabilities in dependencies
uv run safety check

# Run all pre-commit hooks
uv run pre-commit run --all-files
```

## Pre-commit Hooks Setup
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

## Debug Mode
```bash
# Enable verbose logging and detailed output
WELLBIN_DEBUG=true uv run wellbin scrape

# Debug mode with dry run for testing
WELLBIN_DEBUG=true uv run wellbin scrape --dry-run

# Full debug mode with visible browser
WELLBIN_DEBUG=true uv run wellbin scrape --no-headless --limit 1

# PDF conversion debugging
WELLBIN_DEBUG=true uv run wellbin convert --file-type lab
```

## System Utility Commands (macOS/Darwin)
**Note: This system uses GNU toolchain (not BSD), so commands are GNU-compatible**

```bash
# File operations
ls -la                    # List files with details
find . -name "*.py"       # Find Python files
grep -r "pattern" .       # Recursive grep

# Process management
lsof -i :8000            # Find process on port 8000 (dev server runs on 8000)
ps aux | grep python     # Find Python processes
pkill -f chrome          # Kill Chrome processes

# System monitoring
df -h                    # Disk space
free -h                  # Memory usage (if available)
top                      # Process monitor
htop                     # Better process monitor (if installed)

# Git operations
git status
git log --oneline
git diff
```

## Development Server (if applicable)
```bash
# Run development server
./dev.sh run             # Server runs on port 8000

# Find running server
lsof -i :8000
```

## Configuration Management
```bash
# Generate .env configuration file
uv run wellbin config

# Test credentials without downloading
uv run wellbin scrape --dry-run

# Validate configuration with debug mode
WELLBIN_DEBUG=true uv run wellbin scrape --dry-run
```
