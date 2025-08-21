# Makefile for FAERS Signal Detection project
+.PHONY: install analysis app
+
+install:
+	pip install -r requirements.txt
+
+analysis:
+	python analysis/minoxidil_analysis.py
+
+app:
+	streamlit run app/app.py
