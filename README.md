# FAERS Signal Detection

A pharmacovigilance disproportionality analysis pipeline for 2023 FDA Adverse Event Reporting System (FAERS) data. The primary case study examines cardiac adverse event signals — pericardial effusion, cardiac tamponade, pericarditis — associated with oral minoxidil, topical minoxidil, and hydralazine, using 2023 FAERS data integrated with 2023 Medicare Part D prescriber data.

> **Important data limitation:** FAERS is a spontaneous reporting system. Adverse events are voluntarily submitted by patients, providers, and manufacturers and are subject to reporting bias, duplicate submissions, missing values, and inconsistent coding. FAERS has no prescribing denominator, so raw report counts cannot be converted to incidence rates. Disproportionality statistics (PRR, ROR) measure whether a drug–event pair appears at a higher rate than expected relative to the overall reporting background — they detect potential signals, not causal relationships. Nothing in this project should be interpreted as proof of causation or as a basis for clinical decisions.

## What this project does

1. **Ingests** FAERS Q1–Q4 2023 ASCII files and 2023 Medicare Part D prescriber data into a DuckDB database.
2. **Normalizes** the data: deduplicates by latest case version per `CASEID`, restricts to US cases, retains primary suspect drugs only, and links MedDRA preferred term (PT) reactions.
3. **Computes** 2×2 contingency table statistics — PRR, ROR, and Pearson chi-square — with Haldane–Anscombe continuity correction applied when any cell is zero.
4. **Validates** the pipeline using a positive control (ciprofloxacin → tendon rupture) and a negative control (metformin → alopecia).
5. **Generates** publication-ready bar charts and PRR forest plots for the minoxidil/hydralazine cardiac endpoint case study.
6. **Provides** an interactive Streamlit application for single-drug signal screening across all drugs in the FAERS database.

## Methods

This project implements standard pharmacovigilance disproportionality analysis:

- **PRR (Proportional Reporting Ratio):** Ratio of the proportion of a specific event among all events for the target drug vs. the same proportion across all other drugs. See Evans et al. (2001).
- **ROR (Reporting Odds Ratio):** Odds-ratio equivalent; asymptotically equivalent to PRR for rare events, more conservative in sparse tables.
- **Chi-square test:** Tests whether the 2×2 table differs meaningfully from independence.
- **Signal flagging threshold (Evans et al. 2001):** PRR ≥ 2, χ² ≥ 4, N ≥ 3 cases simultaneously.
- **Continuity correction:** Haldane–Anscombe (+0.5 to all cells) applied only when any cell equals zero.

Pre-specified hypotheses, comparators, and controls are documented in [`reports/hypothesis.md`](reports/hypothesis.md).

## Repository structure

```
analysis/        # Figure generation scripts (minoxidil case study)
app/             # Streamlit application for interactive signal screening
data/            # Dataset files — see data/README.md for download instructions
docs/            # Column references and database schema
exploratory/     # Notebooks and ad-hoc SQL queries from initial exploration
pipeline/        # Data ingestion and view creation (run in order: 00 → 03)
reports/         # Hypothesis specification, analysis log, final report
results/         # Generated output tables (CSV) and figures (PNG)
src/             # Shared statistics module (PRR, ROR, chi-square)
tests/           # Method validation using positive/negative controls
Makefile         # Common task automation
requirements.txt
```

## Reproducibility

### 1. Clone the repository

```bash
git clone https://github.com/DarylOkeke/faers-signal-detection.git
cd faers-signal-detection/faers-signal-detection
```

### 2. Install dependencies

```bash
make install
```

Creates `.venv/` and installs all packages from `requirements.txt`. For offline or air-gapped environments, see [`OFFLINE_INSTRUCTIONS.md`](OFFLINE_INSTRUCTIONS.md).

**Without `make` (Windows):**
```cmd
python -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\pip.exe install -r requirements.txt
```

### 3. Prepare the data

Raw FAERS and Medicare files are not included in this repository due to size. See [`data/README.md`](data/README.md) for download links and step-by-step instructions for building the database.

Two files are required before running the pipeline:
- `data/faers+medicare.duckdb` — main analysis database (built by `pipeline/00_load_data.py`)
- `data/anydrug_2023.parquet` — pre-processed snapshot for the Streamlit app (built by `app/sqlite_to_parquet.py` after the pipeline runs)

### 4. Load data into DuckDB

This step is not included in `make pipeline` and must be run once after downloading raw data:

```bash
python -m pipeline.00_load_data
```

This ingests all FAERS quarterly ASCII files and the Medicare Part D CSV from `data/raw/` into `data/faers+medicare.duckdb`.

### 5. Run the analysis pipeline

```bash
make pipeline
```

This runs the remaining steps in sequence:

| Step | Script | Output |
|------|--------|--------|
| Create views | `pipeline/01_create_views.py` | Normalized DuckDB views |
| Compute statistics | `pipeline/02_compute_summary.py` | `results/tables/cardiac_complete.csv` |
| Filter endpoints | `pipeline/03_make_trimmed_tables.py` | `results/tables/minoxidil_trimmed.csv` |
| Generate figures | `scripts/run_analysis.py` | `results/figures/cardiac_combined_plot.png` |

Or run each step individually:

```bash
python -m pipeline.01_create_views
python -m pipeline.02_compute_summary --db data/faers+medicare.duckdb --out results/tables/cardiac_complete.csv
python -m pipeline.03_make_trimmed_tables --input results/tables/cardiac_complete.csv --output results/tables/minoxidil_trimmed.csv
python -m analysis.minoxidil_analysis --input results/tables/cardiac_complete.csv --combined-output results/figures/cardiac_combined_plot.png
```

### 6. Launch the Streamlit app

```bash
make app
# or
streamlit run app/app.py
```

Requires `data/anydrug_2023.parquet`. To regenerate it from the database after the pipeline runs:

```bash
python app/sqlite_to_parquet.py
```

### 7. Run tests and check environment

```bash
make test      # Run method validation tests (positive/negative controls)
make doctor    # Print Python and dependency versions
make clean     # Remove .venv and caches
```

Both control tests should pass before interpreting any pipeline output.

## Limitations

- **Reporting bias:** Healthcare providers, patients, and manufacturers submit reports at different rates. Serious, novel, or media-covered adverse events are systematically over-reported relative to the background.
- **No prescribing denominator:** FAERS contains no prescribing volume data. PRR and ROR reflect proportional differences in reporting, not absolute or comparative incidence rates.
- **Duplicate reports:** Deduplication by latest `CASEVERSION` per `CASEID` reduces but does not eliminate narratively duplicate reports, which require manual review to identify.
- **Confounding:** FAERS reports rarely contain data sufficient to control for indication, comorbidities, age, or co-medications.
- **Missingness:** Route of administration, sex, age, and outcome fields are frequently blank or inconsistently coded across reporters.
- **PRR ≠ causation:** A flagged signal means the drug–event pair is reported at a higher rate than expected relative to the background. It does not establish that the drug caused the event.
- **Route coding:** The topical vs. systemic minoxidil distinction relies on reporter-submitted route codes, which may be incomplete or inaccurate in a subset of cases.

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.
