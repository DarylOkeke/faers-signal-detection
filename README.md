# faers-signal-detection
End-to-end adverse event signal detection pipeline using FAERS data, SQL, and Python for real-world drug safety insights.
# FAERS Signal Detection Project

This project analyzes the FDA Adverse Event Reporting System (FAERS) data to detect post-market drug safety signals using SQL, Python, and data visualization.

## Goals
- Clean and ingest FAERS public data
- Perform exploratory data analysis (EDA)
- Calculate disproportionality metrics (PRR, ROR)
- Visualize trends by drug, age group, and reaction type

## Tech Stack
- **Python**: pandas, matplotlib, seaborn, scikit-learn
- **SQL**: SQLite + raw SQL queries
- **Data**: FAERS ASCII quarterly reports
- **Tools**: Jupyter/Colab, Git, VS Code

## Project Structure

faers-signal-detection/
├── data/ # Raw FAERS files (.txt/.csv)
├── notebooks/ # Jupyter or Colab notebooks for EDA/modeling
├── sql/ # SQL scripts and saved queries
├── scripts/ # Python scripts for ingestion, analysis, and metrics
├── outputs/ # Final results: plots, CSVs, tables for dashboard/report

### Background Check EXAMPLE:
- **PubMed Search:** “Drug X” + “FAERS” + “hepatotoxicity” → 0 direct hits on PRR analyses.
- **FDA Warnings:** No safety communication issued for hepatotoxicity as of April 2025.
- **ClinicalTrials.gov:** Ongoing trials focus on efficacy, not post‐marketing AEs.

## Status
Early-stage: Building ingestion & signal detection engine.