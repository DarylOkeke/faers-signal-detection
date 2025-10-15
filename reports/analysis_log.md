# Analysis Log

## 2025-07-16

- **Set up environment:** Created project folder with `data/`, `scripts/`, `queries/`, `outputs/`, `reports/`, and `docs/` directories.
- **Virtual environment:** Initialized `.venv`, activated it, and installed `sqlite3`, `pandas`, and other dependencies via `pip install -r requirements.txt`.
- **Data ingestion:** Downloaded FAERS Q4 2024 and Q1 2025 raw data into `data/`, ran `scripts/load_faers_to_db.py` to build `faers.db`.

## 2025-07-17

- **Top‑10 AE events per drug:** Ran `queries/top_10_reported_drugs.sql` (output in `outputs/top_10_reported_drugs.md`).
  - *Key finding:* **Dupixent** topped the list for both Q4 2024 and Q1 2025 with over 35,000 reports.
  - Looked for drugs of similar function to Dupixent to look for differences that may lead to relevant findings
  - Came across the drug adbry, which I'll look into later
  - Set up development environment and studied more SQL for more advanced queries to test my hypothesis once formulated

## 2025-07-19

- **Drug background research:**
  - **Dupixent (dupilumab):** monoclonal antibody blocking IL‑4 and IL‑13 signaling, used for moderate‑to‑severe atopic dermatitis and asthma.
  - **Adbry (tralokinumab):** monoclonal antibody targeting IL‑13 only, approved for atopic dermatitis.
  -Although they have similar function, dupixent has almost 6x more adverse event reports(see outputs/dupixent_vs_adbry.md)
- **Analytical insight:** High report count for Dupixent may reflect its broader indication and higher prescription volume—not necessarily greater inherent risk.
- **Next steps:** Fetch 2023 Medicare Part D prescription counts for Dupixent and Adbry, then calculate an AE rate per 1,000 prescriptions to normalize and compare safety signals.

## 2025-07-22

- **Preparing normalization:**
  - Downloaded Medicare Part D Prescriber Public Use File (PUF) for 2023 containing 26.8M prescription records
  - Identified need to extract prescribing volume data for Dupixent and Adbry to calculate normalized adverse event rates
  - Recognized that raw adverse event counts can be misleading without considering prescription volume differences

## 2025-07-25

- **Data infrastructure enhancement:**
  - **Enhanced `load_faers_to_db.py`:** Added support for OUTC (outcomes) and INDI (indications) tables to capture complete adverse event context
  - **Medicare integration:** Created `load_medicare_data.py` to extract and load Medicare Part D prescriber data into SQLite database
  - **Database expansion:** Successfully loaded comprehensive dataset including:
    - FAERS Q4 2024: 410K demographics, 2M drug records, 1.47M reactions, 309K outcomes, 1.22M indications
    - FAERS Q1 2025: 400K demographics, 2M drug records, 1.43M reactions, 304K outcomes, 1.21M indications  
    - Medicare 2023: 26.8M prescriber-drug records with prescription volumes and costs
- **Normalization methodology:**
  - **Step 1:** Extract total prescription counts for Dupixent and Adbry from Medicare Part D data (sum of `Tot_Clms` by drug)
  - **Step 2:** Count adverse event reports for both drugs from FAERS data across both quarters
  - **Step 3:** Calculate normalized rate = (Total AE reports / Total prescriptions) × 1,000 for rate per 1,000 prescriptions
  - **Step 4:** Compare normalized rates to determine if Dupixent's higher absolute AE count reflects true safety signal or just prescription volume
- **Expected outcome:** This approach will reveal whether Dupixent has inherently higher risk or simply more usage, providing clinically meaningful safety comparison

## 2025-07-26

* **Initial combined dataset creation:**

  * Joined FAERS Q1 2023–Q4 2023 data with Medicare 2023 on drug names to start building AE rate comparisons.
  * Wrote a basic query counting reports per drug for US-only reports in 2023.
* **Problem noticed:**

  * While scanning `CASEID` values, realized duplicates existed due to multiple `CASEVERSION`s.
  * Questioning whether raw counts were inflated by older versions of the same case.

---

## 2025-07-29

* **SQL practice & research:**

  * Spent time on advanced SQL window functions, especially `ROW_NUMBER()` and `PARTITION BY`, to learn deduplication patterns.
  * Read FDA FAERS documentation — confirmed that each `CASEID` can appear multiple times and that only the latest `CASEVERSION` should be kept for analysis.
  * Learned that `PRIMARYID` is unique per row but not sufficient alone for deduplication.
* **Pipeline rethink:**

  * Decided to create a **cleaned “latest cases” table** before joining with other FAERS tables to avoid inflated AE counts.

---

## 2025-08-02

* **Tested new dedup approach:**

  * Created a query to keep only the max `CASEVERSION` per `CASEID` using a `ROW_NUMBER()` window.
  * Added filter for `occr_country` = 'US' and `receipt_date` between 2023-01-01 and 2023-12-31 to align with Medicare data year.
* **Findings:**

  * Row count dropped by about 15% compared to unfiltered data — confirmed that duplicates and foreign cases were inflating totals.
  * Without this step, normalized AE rates would be misleading.

---

## 2025-08-05

* **Extra data hygiene research:**

  * Read pharmacoepidemiology guides on spontaneous reporting systems.
  * Learned you should filter on `ROLE_COD` for suspect drugs (Primary Suspect vs Secondary Suspect vs Concomitant).
  * Decided to start main analyses with **Primary Suspect only**, (might add PS+SS later as sensitivity analysis).
* **SQL refinement:**

  * Practicing joins between deduped DEMO table and DRUG/REAC tables using `PRIMARYID` to ensure filtering cascades properly.

---

## 2025-08-09

* **Reaction data checks:**

  * Pulled reactions (PTs) for deduped cases and saw high counts for generic product terms like “DRUG INEFFECTIVE” and “OFF LABEL USE”.
  * Researched MedDRA hierarchy — saw that I could use a stoplist or SOC-level mapping to focus on clinically relevant events.
* **Decision:**

  * Keep full PT list for reproducibility but plan to run filtered analyses with product-issue terms removed.

---

## 2025-08-14

* **Integrated learnings into final pipeline:**

  * Step 1: Deduplicate DEMO to latest case version per `CASEID`, filter US-only, 2023 receipt date, and standardize age/sex.
  * Step 2: Link only Primary Suspect drugs from DRUG table, normalize active ingredient names.
  * Step 3: Attach reactions from REAC, dropping blank PTs.
  * (IP)Step 4: Add outcomes (OUTC) as boolean flags and indications (INDI) linked by `DRUG_SEQ`.
  * (IP)Step 5: Build event-level dataset `(PRIMARYID, INGREDIENT, REACTION_PT)` for counting and signal detection.
* **Reflection:**

  * Earliest analysis was based on inflated counts due to duplicates, missing suspect drug filtering, foreign cases, etc. Didn't think to clean it.
  * The new, cleaned dataset will produce AE rates that are reproducible
  
  * Next up - Finish cleaning data, then will use pandas to analyze it. Not yet sure how I want to frame my hypothesis. Also I need to document the outputs from my new SQL queries
Here’s a continuation of your **Analysis Log**, picking up at **2025-08-15** and running daily through **2025-08-20**, covering all the work we did together (summary stats, trimming, hydralazine comparator, validation, tests, and the final Streamlit app):

---


## 2025-08-15

* **Summary statistics pipeline built:**

  * Implemented `compute_summary.py` to compute PRR, ROR, and chi-square using Haldane–Anscombe correction.
  * Generated initial summary tables with cohort, reaction PT, and signal metrics.
* **Early visualization:**

  * Tested basic bar and forest plots of PRR results.
  * Verified counts matched expectations for Minoxidil and Hydralazine cohorts.
* **Debugging:**

  * Ran into relative path issues (`outputs/results/tables/cardiac_complete.csv` not found).
  * Fixed by restructuring outputs and confirming correct file paths.
* **CLI troubleshooting:**

  * Encountered PowerShell errors when using GNU-style CLI flags (`--input`); switched to `argparse` in Python for portability.

---

## 2025-08-16

* **Validation and controls:**

  * Added **positive control**: Ciprofloxacin → Tendon rupture (expected strong signal).
  * Added **negative control**: Metformin → Alopecia (expected no signal, PRR ≈ 1).
  * Created `test_methods.py` to automatically validate control signals against known outcomes.
* **Bug fixes:**

  * Resolved `global` variable misuse in tests by restructuring test scope.
* **Cohort trimming:**

  * Built `make_trimmed_tables.py`:

    * Filters to **cardiac endpoints** (tamponade, effusion, pericarditis).
    * Optionally includes topical Minoxidil and Hydralazine comparators.
    * Guarantees complete cohort–PT matrix, even for zero-counts.
  * Outputs both **CSV** and **Markdown** tables with human-readable interpretations.
* **Results validation:**

  * Confirmed systemic Minoxidil rows present (4 PTs).
  * Hydralazine included as comparator (also 4 PTs).
  * Verified flagged signals align with known pharmacology.

---

## 2025-08-17

* **Repository restructuring:**

  * Finalized repo layout for clarity and reproducibility:

    * `data/` → raw FAERS/Medicare inputs + SQLite database.
    * `scripts/` → ingestion + plotting utilities.
    * `src/` → core analysis modules (`compute_summary.py`, `make_trimmed_tables.py`).
    * `outputs/` → results tables + figures.
    * `tests/` → control validations (`test_prr_math.py`, `test_methods.py`).
    * `app/` → Streamlit front-end (`app.py`).
* **Refinement of trimmed tables:**

  * Added interpretation text (Reject H0 vs Fail to reject H0).
  * Automated validation checks (row counts, cohort completeness, PT order).
* **First visual outputs:**

  * Generated publication-ready bar and forest plots from `create_forest_plot.py`.
  * Verified Minoxidil systemic showed disproportionate reporting for effusions.

---

## 2025-08-18

* **Streamlit app development (v1):**

  * Initial `app.py` to:

    * Connect to SQLite DB.
    * Allow cohort/PT selection.
    * Compute PRR, ROR, chi² dynamically.
    * Display results in interactive dataframe with CSV download.
  * Added quick forest plot for PRR signals.
* **Bug fix:**

  * Resolved Matplotlib color error (`list of colors` invalid) by assigning a **single hex color per cohort** instead of per list.
* **Extended flexibility:**

  * Enabled dropdown to pick **any cohort in the database**, not just pre-tested ones.
  * Defaulted to cardiac endpoints at top of PT list for demo purposes.

---

## 2025-08-19

* **Streamlit app upgrade (v2):**

  * Added **two-page navigation**:

    * *Cohort / Endpoint Analysis* → interactive filters, tables, forest plots.
    * *All Cohorts Overview* → cohort sizes, top flagged signals globally.
  * Integrated proper download buttons for both results and cohort size tables.
  * Introduced cleaner validation thresholds (PRR ≥ 2.0, χ² ≥ 4.0, N ≥ 3).
* **UI polish:**

  * Used `tab20` color palette for consistent cohort coloring.
  * Added legends for cohorts in plots.
  * Applied log-scale to PRR forest plots with reference lines at PRR=1 and PRR threshold.

---

## 2025-08-20

* **Finalization:**

  * Completed Streamlit app as **drop-in tool**:

    * Any cohort + PTs from database.
    * Cohort size summary page.
    * Control thresholds configurable by user.
    * Publication-ready forest plots + case count bar charts.
  * Repo now has:

    * **End-to-end reproducibility:** raw data → database → analysis → tables/plots → interactive app.
    * **Testing suite with controls** ensuring signal detection validity.
* **Reflection:**

  * Project matured from raw SQL exploration (Dupixent vs Adbry) to a robust FAERS-Medicare signal detection pipeline.
  * Built with reproducibility, flexibility, and presentation in mind.
  * The final Streamlit app demonstrates the whole workflow — accessible to both technical reviewers and domain experts.

---

**Project milestone reached:** Analysis pipeline complete, validated, visualized, and wrapped in a working Streamlit application.

