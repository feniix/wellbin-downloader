# System-Specific Notes (macOS/Darwin)

## Operating System
- **Platform**: Darwin (macOS)
- **Shell**: /bin/zsh

## Important System Characteristics

### GNU Toolchain
- This system uses GNU toolchain (not BSD tools)
- Commands like `sed`, `grep`, `find` are GNU-compatible
- This means standard GNU flags and options work as expected

### Common Utilities

#### File Operations
```bash
ls -la                    # List files with details
find . -name "*.py"       # Find Python files
grep -r "pattern" .       # Recursive grep (GNU version)
```

#### Process Management
```bash
lsof -i :8000            # Find process on port 8000
                         # IMPORTANT: dev.sh runs on port 8000
ps aux | grep python     # Find Python processes
pkill -f chrome          # Kill Chrome processes by name
```

#### System Monitoring
```bash
df -h                    # Disk space
top                      # Process monitor
htop                     # Better process monitor (if installed)
```

## Development Server

### Port Configuration
- **Default port**: 8000
- **Start command**: `./dev.sh run`
- **Find running server**: `lsof -i :8000`

### Server Management
```bash
# Start server
./dev.sh run

# Find if server is running
lsof -i :8000

# Kill server if needed
kill $(lsof -t -i :8000)
```

## Browser and Selenium

### Chrome/Chromium
- Required for Selenium WebDriver
- Selenium 4.15+ auto-manages ChromeDriver
- Check installation: `google-chrome --version` or `chromium --version`

### Browser Processes
```bash
# Find Chrome processes
ps aux | grep -E "(chrome|chromium)"

# Kill stuck browser processes
pkill -f chrome
pkill -f chromium

# Clean up temporary files
rm -rf /tmp/.org.chromium.* 2>/dev/null || true
```

## Python Environment

### Package Manager: uv
- **CRITICAL**: Always use `uv` for Python operations
- **NEVER** use `pip`, `python`, `python3`, or `pipenv`
- All Python commands must be prefixed with `uv run`

### Examples
```bash
# Correct
uv run python script.py
uv run pytest
uv run wellbin scrape

# Incorrect - DO NOT USE
python script.py
pytest
pip install package
```

## File System

### Path Separators
- Use forward slashes: `/` (standard Unix)
- Example: `medical_data/lab_reports/`

### Permissions
```bash
# Check permissions
ls -la directory/

# Make script executable
chmod +x script.sh

# Create directories with parents
mkdir -p path/to/directory
```

## Network and Connectivity

### Testing Connectivity
```bash
# Test Wellbin platform
curl -I https://wellbin.co

# Test S3 access
curl -I "https://wellbin-uploads.s3.amazonaws.com/"

# Check DNS resolution
nslookup wellbin.co
```

### Port Usage
```bash
# Find what's using a port
lsof -i :8000
lsof -i :3000

# List all listening ports
lsof -i -P -n | grep LISTEN
```

## Git Operations

### Common Commands
```bash
git status
git log --oneline
git diff
git add <files>
git commit -m "message"
```

### Important Notes
- Never use `--no-verify` flag (skips pre-commit hooks)
- Never force push to main/master
- Pre-commit hooks run automatically on commit

## Environment Variables

### Setting Variables
```bash
# Temporary (current session)
export WELLBIN_DEBUG=true

# Inline for single command
WELLBIN_DEBUG=true uv run wellbin scrape

# Persistent (add to .env file)
echo "WELLBIN_DEBUG=true" >> .env
```

### Checking Variables
```bash
# Check if variable is set
echo $WELLBIN_DEBUG

# List all environment variables
env | grep WELLBIN
```

## Debugging Tools

### Process Inspection
```bash
# Find Python processes
ps aux | grep python

# Find specific process
pgrep -f "wellbin scrape"

# Kill process by name
pkill -f "wellbin scrape"
```

### Log Files
```bash
# View logs
tail -f combined.log
tail -f error.log

# Search logs
grep "ERROR" combined.log
grep -i "failed" error.log
```

### Resource Monitoring
```bash
# Disk usage
df -h

# Directory size
du -sh directory/

# Memory usage (if available)
vm_stat

# Top processes by memory
top -o mem
```

## Special Considerations

### Selenium on macOS
- May require security permissions for Chrome
- Headless mode recommended for CI/CD
- Visible mode useful for debugging

### File Paths
- Use absolute paths when possible
- Workspace path: `/Users/feniix/src/personal/cursor/wellbin`
- Terminals folder: `/Users/feniix/.cursor/projects/Users-feniix-src-personal-cursor-wellbin/terminals`

### Shell Behavior
- Default shell: zsh (not bash)
- Shell configuration: `~/.zshrc`
- Command history: `~/.zsh_history`
