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
  - Did more environment remodeling and SQL online learning to prepare for more advanced queries to be able to test my hypothesis once formulated

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