# FAERS Signal Detection

A self-contained analysis pipeline and Streamlit interface for exploring potential safety signals in the FDA Adverse Event Reporting System (FAERS).

## Quick start
1. **Install dependencies**
   ```bash
   make install
   ```
   This creates `.venv/` and installs all Python packages from a local `vendor/` wheel cache. If `vendor/` is absent, the command prints instructions and refers to [`OFFLINE_INSTRUCTIONS.md`](OFFLINE_INSTRUCTIONS.md).
2. **Regenerate the minoxidil figure**
   ```bash
   make analysis
   ```
   Outputs `results/figures/cardiac_combined_plot.png` from precomputed metrics in `results/tables/cardiac_complete.csv`.
3. **Launch the Streamlit app**
   ```bash
   make app
   ```
   Starts the interactive FAERS signal explorer (headless mode). The app expects `data/anydrug_2023.parquet`; if missing, create it with `python app/sqlite_to_parquet.py` against the source SQLite database.

### Additional commands
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
