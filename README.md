<<<<<<< HEAD
# CSV Data Cleaner

A small, complete Streamlit application for inspecting CSV files, choosing safe cleaning operations, comparing results, and exporting both clean data and a plain-text audit report.

## Features

- Robust CSV upload with encoding and delimiter detection
- Dataset metrics, data types, statistics, and missing-value chart
- Per-column missing-value strategies (mean, median, mode, custom, `Unknown`, or row removal)
- Duplicate removal using whole rows or selected key columns
- Collision-safe snake_case column names
- Whitespace cleanup and configurable text capitalization
- Numeric, date, text, and boolean conversion
- Rule-based email, age, phone, and non-negative value checks
- IQR outlier detection for review (outliers are never automatically deleted)
- Automatic cleaning suggestions, history, before/after comparison, CSV download, and report download
- Unit-tested cleaning functions and a deliberately messy sample dataset

## Setup

Python 3.10 or newer is recommended.

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Upload `sample_data/messy_customer_data.csv` to try the application.

## Tests

```bash
python -m pytest -q
```

## Project structure

```text
app.py                         Streamlit interface
cleaner/                       Reusable cleaning and validation modules
utils/                         CSV parsing and report generation
sample_data/                   Example input
tests/                         Unit tests
requirements.txt               Runtime and test dependencies
```

## Design notes

- Cleaning always starts from the uploaded dataset, so repeatedly clicking the button does not compound transformations.
- Potentially destructive choices are explicit. Outliers and invalid values are surfaced but not automatically removed.
- The browser upload remains unchanged; users download a new cleaned file.
=======
# Data-Cleaner
A web-based data cleaner
>>>>>>> 411dbd4fa8cdc9f9a43a163cb32c4a776a5604c3
