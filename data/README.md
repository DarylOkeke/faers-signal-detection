# Data Directory

This folder contains datasets used by the analysis scripts and Streamlit application. Large raw files and database files are excluded from the repository via `.gitignore`.

## What is included

- `anydrug_2023.parquet` — Pre-processed FAERS 2×2 snapshot used by the Streamlit app. Generated from the DuckDB database by `app/sqlite_to_parquet.py`.

## What is not included (and how to get it)

### FAERS quarterly ASCII files

Download the four 2023 quarters from the FDA:

- **Download page:** https://fis.fda.gov/extensions/FPD-QDE-FAERS/FPD-QDE-FAERS.html
- Select: ASCII format, year 2023, quarters Q1–Q4
- Extract each zip archive into the corresponding subfolder:

```
data/raw/
├── FAERSQ1_2023/   # Contains DEMO23Q1.txt, DRUG23Q1.txt, REAC23Q1.txt, OUTC23Q1.txt, INDI23Q1.txt
├── FAERSQ2_2023/
├── FAERSQ3_2023/
└── FAERSQ4_2023/
```

Each quarterly folder should contain five `$`-delimited ASCII files: DEMO, DRUG, REAC, OUTC, and INDI.

### Medicare Part D Prescriber PUF (2023)

Download the 2023 Part D Prescribers by Provider and Drug file from CMS:

- **Download page:** https://data.cms.gov/provider-summary-by-type-of-service/medicare-part-d-prescribers/medicare-part-d-prescribers-by-provider-and-drug
- Select year 2023, download the CSV
- Place the file in `data/raw/` — the pipeline will detect it automatically

### Building the database

After placing all raw files in `data/raw/`, run the data loading step:

```bash
python -m pipeline.00_load_data
```

This creates `data/faers+medicare.duckdb`. Then continue with the rest of the pipeline as described in the main [README](../README.md).

### Regenerating the Streamlit parquet snapshot

After the full pipeline has run and `data/faers+medicare.duckdb` exists:

```bash
python app/sqlite_to_parquet.py
```

This exports the pre-computed 2×2 table view to `data/anydrug_2023.parquet`, which the Streamlit app reads directly.

## External references

- [FAERS Public Dashboard](https://www.fda.gov/drugs/questions-and-answers-fdas-adverse-event-reporting-system-faers/fda-adverse-event-reporting-system-faers-public-dashboard)
- [FAERS column definitions](../docs/FAERS_column_reference.md)
- [Medicare Part D column definitions](../docs/Medicare_column_reference.md)
- [Database schema reference](../docs/database_reference.md)
