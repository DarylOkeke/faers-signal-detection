# Analysis Log

## 2025-07-16

- **Set up environment:** Created project folder with `data/`, `scripts/`, `queries/`, `outputs/`, `reports/`, and `docs/` directories.
- **Virtual environment:** Initialized `.venv`, activated it, and installed `sqlite3`, `pandas`, and other dependencies via `pip install -r requirements.txt`.
- **Data ingestion:** Downloaded FAERS Q4 2024 and Q1 2025 raw data into `data/`, ran `scripts/load_faers_to_db.py` to build `faers.db`.

## 2025-07-17

- **Top‑10 AE events per drug:** Ran `queries/top_10_reported_drugs.sql` (output in `outputs/top_10_reported_drugs.md`).
  - *Key finding:* **Dupixent** topped the list for both Q4 2024 and Q1 2025 with over 35,000 reports.

## 2025-07-19

- **Drug background research:**
  - **Dupixent (dupilumab):** monoclonal antibody blocking IL‑4 and IL‑13 signaling, used for moderate‑to‑severe atopic dermatitis and asthma.
  - **Adbry (tralokinumab):** monoclonal antibody targeting IL‑13 only, approved for atopic dermatitis.
- **Analytical insight:** High report count for Dupixent may reflect its broader indication and higher prescription volume—not necessarily greater inherent risk.
- **Next steps:** Fetch 2023 Medicare Part D prescription counts for Dupixent and Adbry, then calculate an AE rate per 1,000 prescriptions to normalize and compare safety signals.
