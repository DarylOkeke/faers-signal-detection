# Data Directory

This folder contains datasets used by the analysis scripts and Streamlit application.

## Included Files
- `anydrug_2023.parquet`: Pre-processed FAERS snapshot consumed by the Streamlit app.

## External Data Sources
- [FAERS Quarterly Data Download](https://fis.fda.gov/extensions/FPD-QDE-FAERS/FPD-QDE-FAERS.html)
- [Medicare Part D Prescriber PUF](https://data.cms.gov/provider-summary-by-type-of-service/medicare-part-d-prescribers/medicare-part-d-prescribers-by-provider-and-drug)
- [FAERS Public Dashboard](https://www.fda.gov/drugs/questions-and-answers-fdas-adverse-event-reporting-system-faers/fda-adverse-event-reporting-system-faers-public-dashboard)

To recreate `anydrug_2023.parquet` from the original SQLite database, run:

```bash
python app/sqlite_to_parquet.py
```
