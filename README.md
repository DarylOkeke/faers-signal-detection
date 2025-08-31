# FAERS Signal Detection

A self-contained analysis pipeline and Streamlit ## Additional commands
- `make pipeline` – run the complete analysis pipeline (views → summary → figures)
- `make analysis` – generate minoxidil case study figure only  
- `make test` – run the unit tests
- `make doctor` – report Python and dependency versions
- `make clean` – remove the virtual environment and cachesrface for exploring potential safety signals in the FDA Adverse Event Reporting System (FAERS).


## Reproducibility: Step-by-step for a Fresh Clone

Follow these steps to fully reproduce the summary tables, minoxidil case study figures, and launch the Streamlit app—even on a new machine or after a fresh clone.

### 1. Clone the repository
```bash
git clone https://github.com/DarylOkeke/faers-signal-detection.git
cd faers-signal-detection/faers-signal-detection
```

### 2. Set up the Python environment and dependencies
```bash
make install
```
This creates a `.venv/` and installs all required packages from `requirements.txt` (using `vendor/` for offline installs if present).

**Windows users without `make`:** Run these commands manually:
```cmd
python -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\pip.exe install --no-index --find-links vendor -r requirements.txt
```

### 3. Prepare the data

- **Required:** `data/faers+medicare.duckdb` (main database) and `data/anydrug_2023.parquet` (for the app).
- If these files are missing, see [`OFFLINE_INSTRUCTIONS.md`](OFFLINE_INSTRUCTIONS.md) and `data/README.md` for how to generate or obtain them.
- **Note:** `data/anydrug_2023.parquet` is already included in the repository. Only regenerate it if needed:
  ```bash
  python app/sqlite_to_parquet.py
  ```

### 4. Run the full analysis pipeline

**Option A: Use the automated pipeline (recommended):**
```bash
make pipeline
```
This runs all steps below automatically.

**Option B: Run individual steps:**

**A. Set up database views:**
```bash
python -m pipeline.01_create_views
```

**B. Compute summary statistics and export CSV:**
```bash
python -m pipeline.02_compute_summary --db data/faers+medicare.duckdb --out results/tables/cardiac_complete.csv
```

**C. Filter and format the summary for minoxidil endpoints:**
```bash
python -m pipeline.03_make_trimmed_tables --input results/tables/cardiac_complete.csv --output results/tables/minoxidil_trimmed.csv
```

**D. Generate the minoxidil case study figure:**
```bash
python -m analysis.minoxidil_analysis --input results/tables/cardiac_complete.csv --combined-output results/figures/cardiac_combined_plot.png
```

### 5. Launch the Streamlit app
```bash
make app
# or
streamlit run app/app.py
```
The app expects `data/anydrug_2023.parquet` to exist (already included).

### 6. (Optional) Run tests and check environment
```bash
make test      # Run unit tests
make doctor    # Show Python and dependency versions
make clean     # Remove .venv and caches
```

---

## Additional commands
- `make test` – run the unit tests
- `make doctor` – report Python and key dependency versions
- `make clean` – remove the virtual environment and caches

## Repository layout
```
analysis/       # Plotting utilities and figure scripts
app/            # Streamlit application
scripts/        # Command-line entry points
pipeline/       # Data ingestion and preprocessing
data/           # Project datasets (see data/README.md)
docs/           # Reference documentation
exploratory/    # Notebooks and ad-hoc scripts
reports/        # Project reports and logs
results/        # Generated tables and figures
src/            # Reusable Python modules
tests/          # Unit tests
Makefile        # Common tasks (install, analysis, app)
requirements.txt
```

## Development
Run tests before committing changes:
```bash
make test
```

## License
Distributed under the MIT License. See [LICENSE](LICENSE) for details.
