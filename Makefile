# Makefile - offline friendly
VENV := .venv
PY   := $(VENV)/bin/python
PIP  := $(VENV)/bin/pip
APP_FILE := app/app.py
ANALYSIS_MODULE := scripts.run_analysis

.PHONY: all install test analysis app clean doctor

all: test

$(VENV)/bin/activate: requirements.txt
	python -m venv $(VENV)
	$(PY) -m pip install --upgrade pip
	@if [ -d vendor ]; then $(PIP) install --no-index --find-links vendor -r requirements.txt; else echo "vendor/ not found; cannot install behind proxy."; echo "See OFFLINE_INSTRUCTIONS.md for how to generate vendor/."; exit 0; fi
	touch $(VENV)/bin/activate

install: $(VENV)/bin/activate

test: install
	$(PY) -m pytest -q

analysis: install
	$(PY) -m $(ANALYSIS_MODULE)

app: install
	$(PY) -m streamlit run $(APP_FILE) --server.headless true

clean:
	rm -rf $(VENV) .pytest_cache __pycache__ */__pycache__

doctor:
	@echo "Python: $$($(PY) -V || echo 'not installed')"
	@echo "Pip: $$($(PIP) -V || echo 'not installed')"
	@echo "Streamlit import: $$($(PY) -c 'import streamlit, sys; print(streamlit.__version__)' 2>&1 || echo 'missing')"
	@echo "NumPy import: $$($(PY) -c 'import numpy as np; print(np.__version__)' 2>&1 || echo 'missing')"
