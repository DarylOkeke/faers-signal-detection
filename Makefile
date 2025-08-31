# Makefile - cross-platform compatible
VENV := .venv
ifeq ($(OS),Windows_NT)
    PY := $(VENV)\Scripts\python.exe
    PIP := $(VENV)\Scripts\pip.exe
    RM := rmdir /s /q
    MKDIR := mkdir
else
    PY := $(VENV)/bin/python
    PIP := $(VENV)/bin/pip
    RM := rm -rf
    MKDIR := mkdir -p
endif
APP_FILE := app/app.py
ANALYSIS_MODULE := scripts.run_analysis

.PHONY: all install test analysis app clean doctor pipeline

all: test

pipeline: install
	$(PY) -m pipeline.01_create_views
	$(PY) -m pipeline.02_compute_summary --db data/faers+medicare.duckdb --out results/tables/cardiac_complete.csv
	$(PY) -m pipeline.03_make_trimmed_tables --input results/tables/cardiac_complete.csv --output results/tables/minoxidil_trimmed.csv
	$(PY) -m $(ANALYSIS_MODULE)
	@echo "✓ Full pipeline completed successfully!"

ifeq ($(OS),Windows_NT)
$(VENV)\Scripts\activate: requirements.txt
	python -m venv $(VENV)
	$(PY) -m pip install --upgrade pip
	@if exist vendor ( $(PIP) install --no-index --find-links vendor -r requirements.txt ) else ( echo vendor/ not found; cannot install behind proxy. & echo See OFFLINE_INSTRUCTIONS.md for how to generate vendor/. )

install: $(VENV)\Scripts\activate
else
$(VENV)/bin/activate: requirements.txt
	python -m venv $(VENV)
	$(PY) -m pip install --upgrade pip
	@if [ -d vendor ]; then $(PIP) install --no-index --find-links vendor -r requirements.txt; else echo "vendor/ not found; cannot install behind proxy."; echo "See OFFLINE_INSTRUCTIONS.md for how to generate vendor/."; exit 0; fi

install: $(VENV)/bin/activate
endif

test: install
	$(PY) -m pytest -q

analysis: install
	$(PY) -m $(ANALYSIS_MODULE)

app: install
	$(PY) -m streamlit run $(APP_FILE) --server.headless true

clean:
	$(RM) $(VENV) .pytest_cache __pycache__ */__pycache__ 2>nul || true

doctor:
	@echo "Python: $$($(PY) -V || echo 'not installed')"
	@echo "Pip: $$($(PIP) -V || echo 'not installed')"
	@echo "Streamlit import: $$($(PY) -c 'import streamlit, sys; print(streamlit.__version__)' 2>&1 || echo 'missing')"
	@echo "NumPy import: $$($(PY) -c 'import numpy as np; print(np.__version__)' 2>&1 || echo 'missing')"
