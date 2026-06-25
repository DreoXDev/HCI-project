# Getting Started

## Prerequisites

- Python 3.11 or newer.
- LibreOffice if you want automatic PDF export.
- PowerPoint or another PPTX editor for final manual review.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m src.cli doctor
```

## Validate Inputs

```powershell
python -m src.cli validate
python -m src.cli validate-final-data
```

## Generate Outputs

```powershell
python -m src.cli full-pipeline --plot-style both --generate-slides --no-export-pdf
```

Use `--export-pdf` only when `outputs/slides/final_report.pdf` is not open in Acrobat or another PDF viewer.

## Main Outputs

- `outputs/slides/final_report.pptx`
- `outputs/slides/final_report.pdf`
- `outputs/reports/final_data_validation.md`
- `outputs/reports/pipeline_run.md`
