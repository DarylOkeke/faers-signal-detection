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
  - Set up development environment and studied SQL documentation to prepare for more advanced queries to test my hypothesis once formulated

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

  * Realized my earliest analysis (July 16–25) was based on inflated counts due to duplicates, missing suspect drug filtering, and inclusion of foreign cases.
  * CThe new cleaned, aligned dataset will produce AE rates that are both reproducible and meaningful.
