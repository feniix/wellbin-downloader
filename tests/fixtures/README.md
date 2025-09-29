# Test Fixtures

This directory contains anonymized medical data fixtures for testing the wellbin medical data downloader and converter.

## Overview

The fixtures are based on real medical reports but with all personal identifiers (names, ID numbers, addresses, etc.) replaced with fictional data to ensure privacy while maintaining medical authenticity.

## Structure

```text
fixtures/
├── medical_data/
│   ├── lab_reports/
│   │   ├── 20230615-lab-0.md    # Recent lab report with normal values
│   │   └── 20180425-lab-1.md    # Older lab report with some elevated values
│   └── imaging_reports/
│       ├── 20240318-imaging-0.md # Recent MRI knee with findings
│       └── 20190815-imaging-1.md # Older CT chest, normal
├── medical_fixtures.py          # Fixture utilities and access functions
└── README.md                   # This file
```

## Fixture Types

### Lab Reports

- **Recent (20230615-lab-0.md)**: Contains normal blood work values including:
  - Complete blood count (HEMOGRAMA COMPLETO)
  - Liver function tests
  - Lipid panel
  - Basic metabolic panel

- **Older (20180425-lab-1.md)**: Contains some elevated values showing:
  - Slightly elevated cholesterol
  - Borderline thyroid function
  - Elevated ESR (inflammatory marker)

### Imaging Reports

- **Recent (20240318-imaging-0.md)**: MRI of right knee showing:
  - Chondromalacia (cartilage damage)
  - Meniscal degeneration
  - Active synovitis

- **Older (20190815-imaging-1.md)**: CT of chest showing:
  - Normal lung parenchyma
  - Normal mediastinum
  - No pathological findings

## Medical Terminology

The fixtures contain authentic Spanish medical terminology commonly found in Latin American medical reports:

### Lab Report Terms

- **HEMOGRAMA COMPLETO** - Complete Blood Count
- **SERIE ERITROCITARIA** - Red Blood Cell Series
- **SERIE LEUCOCITARIA** - White Blood Cell Series
- **QUIMICA CLINICA** - Clinical Chemistry

### Imaging Report Terms

- **RESONANCIA MAGNETICA** - Magnetic Resonance Imaging
- **TOMOGRAFIA COMPUTADA** - Computed Tomography
- **HALLAZGOS** - Findings
- **CONCLUSION** - Conclusion

## Usage in Tests

### Basic Usage

```python
from tests.fixtures.medical_fixtures import get_fixture_content

# Get content of a specific fixture
lab_content = get_fixture_content("lab", "recent")
imaging_content = get_fixture_content("imaging", "older")
```

### Using with Pytest Fixtures

```python
def test_medical_processing(sample_lab_report_recent):
    # sample_lab_report_recent contains the fixture content
    assert "HEMOGRAMA COMPLETO" in sample_lab_report_recent
```

### Validation

```python
from tests.fixtures.medical_fixtures import validate_fixture_content

# Validate that content contains expected medical patterns
is_valid = validate_fixture_content("lab", content)
```

## Anonymization Details

All personal identifiers have been replaced:

| Original Data Type | Anonymized With |
|-------------------|----------------|
| Patient names     | Generic Spanish names (MARTINEZ, RODRIGUEZ, etc.) |
| ID numbers        | Sequential fictional numbers |
| Dates            | Adjusted to maintain realistic age patterns |
| Doctor names     | Generic medical professional names |
| Medical license numbers | Fictional MN numbers |
| Institution codes | Generic numeric codes |

## Medical Values

- Lab values are within realistic ranges for the conditions being represented
- Reference ranges match standard laboratory values
- Imaging findings describe common pathological conditions
- All measurements use standard medical units (mg/dl, g/dl, mm, etc.)

## File Naming Convention

Files follow the standard wellbin naming pattern:

- `YYYYMMDD-{type}-{sequence}.md`
- Where `type` is either "lab" or "imaging"
- Sequence numbers start at 0

## Testing Integration

These fixtures enable:

1. **Unit testing** of conversion logic without external dependencies
2. **Integration testing** with realistic medical terminology
3. **Validation testing** of Spanish medical report processing
4. **Regression testing** with consistent, version-controlled test data
5. **CI/CD compatibility** without requiring external medical data

## Privacy and Ethics

- No real patient data is included
- All identifiers are fictional
- Medical conditions described are common and non-stigmatizing
- Content is suitable for public repositories and CI systems

## Maintenance

When updating fixtures:

1. Ensure medical terminology remains authentic
2. Maintain realistic value ranges
3. Keep anonymization consistent
4. Update tests if structure changes
5. Validate with `validate_fixture_content()` function
