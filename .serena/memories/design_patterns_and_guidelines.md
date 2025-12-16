# Design Patterns and Guidelines

## Architecture Patterns

### Configuration Management Pattern
The application uses a three-tier precedence system:

1. **Command-line arguments** (highest priority)
   - Direct user input via CLI flags
   - Overrides all other sources

2. **Environment variables** (middle priority)
   - Loaded from `.env` file via python-dotenv
   - Prefixed with `WELLBIN_`
   - Example: `WELLBIN_EMAIL`, `WELLBIN_STUDY_TYPES`

3. **Built-in defaults** (lowest priority)
   - Hardcoded fallback values
   - Used when no other source provides value

### Error Handling Pattern
- **Graceful degradation**: Continue operation when possible
- **Informative messages**: Provide context for failures
- **Progress indicators**: Show status throughout operations
- **Comprehensive try-catch**: Wrap risky operations
- **Fallback mechanisms**: Multiple strategies for critical operations

Example: Date extraction uses multiple fallback patterns before defaulting to `20240101`.

### Filename Deduplication Pattern
Counter-based naming prevents overwrites:

```python
# Pattern: YYYYMMDD-{type}-{counter}.pdf
# Example: 20240604-lab-0.pdf, 20240604-lab-1.pdf

# Deduplication key: {study_type}_{study_date}
# Per-type counters in date_counters dictionary
```

This ensures:
- No file overwrites
- Chronological ordering
- Type separation
- Predictable naming

## Medical Data Processing Patterns

### Study Type Filtering
URL-based filtering maps study types to medical categories:

- **FhirStudy**: `type=FhirStudy` → lab reports → `lab_reports/`
- **DicomStudy**: `type=DicomStudy` → imaging reports → `imaging_reports/`
- **"all"**: Processes both types

Link discovery uses XPath: `//a[contains(@href, '/study/')]`

### Date Extraction Strategy
Multi-pattern approach with fallbacks:

1. **Primary patterns**:
   - `MM/DD/YYYY` or `DD/MM/YYYY` format
   - `YYYY/MM/DD` ISO format
   - Natural language: `DD Mon YYYY`, `Mon DD, YYYY`
   - Study ID embedded timestamp

2. **Fallback mechanisms**:
   - Page content scanning
   - Study ID parsing
   - Container text analysis
   - Default: `20240101`

### S3 Pre-signed URL Handling
Downloads bypass authentication:

- Direct S3 bucket access without session cookies
- Automatic URL expiration handling with retries
- Streaming downloads (8KB chunks)
- Response validation and error handling

### Medical Header Detection
Custom PyMuPDF4LLM header recognition:

- **H2 (Main sections)**: PATIENT INFORMATION, LABORATORY RESULTS, CLINICAL FINDINGS
- **H3 (Subsections)**: CHEMISTRY, HEMATOLOGY, LIPID PANEL, CBC
- **H4 (Parameters)**: Text ending with colon + appropriate font size

Uses font size and styling cues for hierarchy.

## Code Organization Patterns

### Separation of Concerns
- **CLI layer** (`cli.py`, `commands/`): User interface
- **Core logic** (`core/`): Business logic
- **Utilities** (`utils.py`): Shared functions

### Class-Based Stateful Operations
Use classes for operations that maintain state:

- `WellbinMedicalDownloader`: Maintains browser session, counters
- `PDFToMarkdownConverter`: Maintains configuration, output paths

### Function-Based Stateless Operations
Use functions for pure operations:

- `get_env_or_default()`: Configuration retrieval
- `validate_credentials()`: Credential validation
- `convert_structured_directories()`: Directory processing

## Testing Patterns

### Test Categories
- **Unit tests**: Individual function testing with mocking
- **Integration tests**: Component interaction with real data
- **CLI tests**: Command-line interface testing
- **Slow tests**: Long-running tests (marked for exclusion)

### Fixture Strategy
- **Anonymized data**: Spanish medical reports with privacy protection
- **Realistic scenarios**: Authentic medical terminology and structure
- **Reusable fixtures**: Shared setup in `conftest.py`

### Mocking Strategy
- Mock external dependencies (Selenium, network calls)
- Use `pytest-mock` for flexible mocking
- Preserve core logic for testing

## Performance Patterns

### Rate Limiting
Built-in delays respect platform resources:

- 0.5 seconds between study page processing
- 0.2 seconds between PDF downloads
- 1-3 second delays during authentication

### Memory Management
- Sequential processing (no parallel execution)
- Single browser session per operation
- PDF conversion one file at a time
- Automatic cleanup via Python garbage collection

### Resource Cleanup
- Browser cleanup in `finally` blocks
- Proper session termination
- Temporary file cleanup

## Security Patterns

### Credential Handling
- Environment variables (never hardcoded)
- Validation before operations
- No sensitive data in logs
- Quotes for special characters in passwords

### Browser Automation
- Appropriate user agents
- Respectful delays
- Session management
- No cookie/session exposure

### File Operations
- Validate response status
- Streaming downloads
- Permission checks
- Path sanitization

## CLI Design Patterns

### Click Framework Usage
- Command groups for organization
- Option flags with defaults
- Help text for all commands
- Boolean flags with `--flag/--no-flag` pattern

### Debug Mode
- Environment variable: `WELLBIN_DEBUG=true`
- Detailed logging throughout operations
- Visible browser mode for debugging
- Dry-run mode for testing

## Development Workflow Patterns

### Pre-commit Hooks
Automated quality enforcement via Ruff v0.8.0+:

1. **Code Quality (Ruff)**:
   - `ruff check`: Unified linting (replaces flake8, pylint, etc.)
   - `ruff format`: Code formatting + import sorting (replaces Black + isort)
   - Line length: 120 characters
   - Handles all code quality checks in one pass

2. **File Validation**:
   - trailing whitespace, end-of-file-fixer
   - YAML, TOML, JSON validation
   - Large file detection, merge conflict detection
   - Case conflict detection, mixed line ending detection

3. **Python-Specific Checks**:
   - blanket noqa prevention
   - blanket type ignore prevention
   - type annotations enforcement

### Test-Driven Development
1. Write tests first (or alongside code)
2. Run tests frequently
3. Maintain coverage above 30%
4. Use integration tests for real-world validation

### Continuous Quality
- Type checking with every change
- Security scanning periodically
- Dependency vulnerability checks
- Coverage monitoring

## Common Patterns to Follow

### When Adding New Features
1. Update configuration system if needed
2. Add CLI options with defaults
3. Implement core logic in appropriate module
4. Add comprehensive error handling
5. Write tests (unit + integration)
6. Update documentation
7. Run full quality checks

### When Fixing Bugs
1. Write failing test first
2. Fix the bug
3. Verify test passes
4. Check for similar issues
5. Update documentation if needed
6. Run full test suite

### When Refactoring
1. Ensure tests exist and pass
2. Make incremental changes
3. Run tests after each change
4. Maintain backward compatibility
5. Update type hints
6. Check coverage doesn't decrease

## Anti-Patterns to Avoid

### Don't
- Use `pip` or `python` directly (use `uv run`)
- Hardcode credentials or paths
- Skip error handling
- Ignore type hints
- Skip tests
- Commit without pre-commit hooks
- Use force push to main/master
- Include AI references in commits
- Create files without integration plan
- Guess missing parameters in tool calls

### Do
- Use `uv run` for all Python commands
- Use environment variables for configuration
- Handle errors gracefully with context
- Add type hints to all functions
- Write tests for new code
- Let pre-commit hooks run
- Use conventional commit messages
- Focus on technical changes in commits
- Plan file integration before creation
- Wait for previous tool calls to complete
