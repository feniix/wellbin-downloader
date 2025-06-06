# Wellbin Medical Data Scraper

A comprehensive Python scraper for the Wellbin medical platform (https://wellbin.co/) that downloads and processes medical data including laboratory reports and medical imaging studies.

## ✨ Features

### 🩺 **Medical Data Support**
- **FhirStudy**: Laboratory reports (blood tests, chemistry panels, etc.)
- **DicomStudy**: Medical imaging reports (MRI, CT, X-ray, ultrasound, etc.)
- Automatic file categorization and organized storage
- Date-based naming with deduplication

### 🛠️ **Professional CLI**
- Built with `click` for robust command-line interface
- Environment-based configuration for security
- Flexible filtering and limiting options
- Comprehensive help and examples

### 📄 **PDF to Markdown Conversion**
- LLM-optimized markdown extraction using PyMuPDF4LLM
- Preserves medical data structure (tables, values, units)
- Batch processing with type filtering
- Perfect for AI/LLM analysis

### 🔒 **Security & Configuration**
- Environment variables for sensitive credentials
- Configurable defaults via `.env` file
- Git-safe with proper `.gitignore` setup

## 🏗️ Requirements

- Python 3.9+
- Google Chrome browser
- ChromeDriver (automatically managed by Selenium)
- uv package manager

## 📦 Installation

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd wellbin
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your Wellbin credentials
   ```

## ⚙️ Configuration

Create your `.env` file from the example:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Wellbin Login Credentials
WELLBIN_EMAIL=your-email@example.com
WELLBIN_PASSWORD=your-password

# Default Directories
DEFAULT_OUTPUT_DIR=medical_data
DEFAULT_MARKDOWN_DIR=markdown_reports

# Scraper Settings
DEFAULT_STUDY_LIMIT=
DEFAULT_STUDY_TYPES=FhirStudy
DEFAULT_HEADLESS=true

# PDF Converter Settings
DEFAULT_INPUT_DIR=medical_data
DEFAULT_PRESERVE_STRUCTURE=true
DEFAULT_FILE_TYPE=all
```

## 🚀 Usage

### Medical Data Scraper

#### **Download Lab Reports (FhirStudy)**
```bash
# Download 5 recent lab reports
uv run python wellbin_scrape_labs.py --limit 5 --types FhirStudy

# Download all lab reports
uv run python wellbin_scrape_labs.py --limit 0 --types FhirStudy
```

#### **Download Imaging Reports (DicomStudy)**
```bash
# Download 10 imaging studies
uv run python wellbin_scrape_labs.py --limit 10 --types DicomStudy

# Download all imaging studies
uv run python wellbin_scrape_labs.py --limit 0 --types DicomStudy
```

#### **Download Everything**
```bash
# Download both lab and imaging studies
uv run python wellbin_scrape_labs.py --types FhirStudy,DicomStudy

# Download all study types
uv run python wellbin_scrape_labs.py --types all
```

#### **Custom Configuration**
```bash
# Custom output directory
uv run python wellbin_scrape_labs.py --output my_medical_data --types DicomStudy

# Visible browser (for debugging)
uv run python wellbin_scrape_labs.py --no-headless --limit 1
```

### PDF to Markdown Converter

#### **Convert Medical Data**
```bash
# Convert all PDFs using environment defaults
uv run python convert_pdfs_to_markdown.py

# Convert organized medical data preserving structure
uv run python convert_pdfs_to_markdown.py --input-dir medical_data --preserve-structure

# Convert only lab reports
uv run python convert_pdfs_to_markdown.py --file-type lab

# Convert only imaging reports
uv run python convert_pdfs_to_markdown.py --file-type imaging
```

### CLI Help

Get comprehensive help for any command:

```bash
uv run python wellbin_scrape_labs.py --help
uv run python convert_pdfs_to_markdown.py --help
```

## 📁 File Organization

The scraper automatically organizes files by type:

```
medical_data/
├── lab_reports/
│   ├── 20250604-lab-0.pdf      # Latest lab results
│   ├── 20250210-lab-0.pdf      # Blood chemistry panel
│   └── 20190119-lab-0.pdf      # Historical lab data
└── imaging_reports/
    ├── 20250416-imaging-0.pdf  # MRI report
    ├── 20250318-imaging-0.pdf  # CT scan report
    └── 20250314-imaging-0.pdf  # X-ray report

markdown_reports/
├── lab_reports_markdown/
│   ├── 20250604-lab-0.md       # LLM-ready lab data
│   └── ...
└── imaging_reports_markdown/
    ├── 20250416-imaging-0.md   # LLM-ready imaging reports
    └── ...
```

## 🤖 LLM Integration

The markdown converter creates LLM-optimized output perfect for AI analysis:

```bash
# Feed all medical data to an LLM
cat markdown_reports/**/*.md | llm "analyze my health trends over time"

# Extract specific medical values
grep -h 'mg/dL\|g/dL' markdown_reports/**/*.md

# Find abnormal results
grep -i 'alto\|bajo\|high\|low' markdown_reports/**/*.md

# Search across all reports
grep -r 'cholesterol\|glucose' markdown_reports/
```

## 🏥 Medical Data Types

### **FhirStudy (Laboratory Reports)**
- Blood chemistry panels
- Complete blood count (CBC)
- Lipid profiles
- Liver function tests
- Kidney function tests
- Hormone levels
- Tumor markers

### **DicomStudy (Medical Imaging)**
- MRI (Magnetic Resonance Imaging)
- CT (Computed Tomography) scans
- X-rays
- Ultrasounds
- Mammograms
- Nuclear medicine studies

## 🔧 Development

### Project Structure

```
wellbin/
├── wellbin_scrape_labs.py      # Main medical data scraper
├── convert_pdfs_to_markdown.py # PDF to markdown converter
├── pyproject.toml              # Project dependencies
├── .env.example               # Environment template
├── .env                       # Your credentials (gitignored)
├── .gitignore                # Git exclusions
├── CONFIG.md                 # Configuration guide
└── README.md                 # This file
```

### Adding New Study Types

To support additional medical data types, update the `study_config` in `WellbinMedicalScraper`:

```python
self.study_config = {
    'FhirStudy': {
        'name': 'lab',
        'description': 'Laboratory Reports',
        'icon': '🧪',
        'subdir': 'lab_reports'
    },
    'DicomStudy': {
        'name': 'imaging',
        'description': 'Medical Imaging',
        'icon': '🩻',
        'subdir': 'imaging_reports'
    },
    'NewStudyType': {
        'name': 'new_type',
        'description': 'New Medical Data',
        'icon': '📋',
        'subdir': 'new_reports'
    }
}
```

## 🛡️ Security & Privacy

### **Credential Security**
- ✅ Credentials stored in `.env` file (gitignored)
- ✅ No hardcoded passwords in source code
- ✅ Environment-based configuration

### **Medical Data Privacy**
- ✅ All medical data directories gitignored
- ✅ Local processing only
- ✅ No data transmitted to external services
- ⚠️ **Important**: This contains your personal medical data - handle with care

### **Safe Usage**
- Only access your own medical data
- Respect Wellbin's terms of service
- Use reasonable rate limiting
- Store downloaded data securely

## 🐛 Troubleshooting

### **Common Issues**

1. **Login Fails**
   ```bash
   # Check credentials in .env file
   cat .env

   # Test with visible browser
   uv run python wellbin_scrape_labs.py --no-headless --limit 1
   ```

2. **No Studies Found**
   ```bash
   # Verify study types available
   uv run python wellbin_scrape_labs.py --types all --limit 1
   ```

3. **Environment Issues**
   ```bash
   # Verify environment loading
   uv run python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('WELLBIN_EMAIL'))"
   ```

4. **ChromeDriver Problems**
   - Ensure Google Chrome is installed
   - Selenium 4+ manages ChromeDriver automatically
   - Check for browser version compatibility

### **Debug Mode**

Enable verbose debugging:

```bash
# Run with visible browser
uv run python wellbin_scrape_labs.py --no-headless

# Limit to 1 study for testing
uv run python wellbin_scrape_labs.py --limit 1 --types FhirStudy
```

## 📊 Examples

### **Complete Medical History Download**

```bash
# 1. Download all medical data
uv run python wellbin_scrape_labs.py --types all --output complete_medical_history

# 2. Convert to LLM-ready markdown
uv run python convert_pdfs_to_markdown.py \
  --input-dir complete_medical_history \
  --preserve-structure \
  --output-dir medical_analysis

# 3. Analyze with AI
cat medical_analysis/**/*.md | llm "Summarize my medical history and identify any concerning trends"
```

### **Monitoring Recent Results**

```bash
# Download latest 5 lab reports
uv run python wellbin_scrape_labs.py --limit 5 --types FhirStudy

# Convert and analyze recent trends
uv run python convert_pdfs_to_markdown.py --file-type lab
grep -h "glucose\|cholesterol" markdown_reports/**/*.md
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📄 License

This project is for educational and personal medical data management. Please:
- Respect Wellbin's terms of service
- Only access your own medical data
- Use responsibly and ethically
- Comply with applicable privacy laws (HIPAA, GDPR, etc.)

## 🔗 Dependencies

- **Click**: Professional CLI interface
- **Selenium**: Web automation
- **Requests**: HTTP client
- **BeautifulSoup4**: HTML parsing
- **PyMuPDF4LLM**: LLM-optimized PDF processing
- **python-dotenv**: Environment configuration
