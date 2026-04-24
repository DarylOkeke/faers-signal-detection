
# Cardiac Endpoints Signal Detection Analysis

**Database:** FDA Adverse Event Reporting System (FAERS), 2023 (Q1–Q4)
**Methodology:** Disproportionality Analysis (PRR, ROR, Chi-square)
**Cohorts Analyzed:** Hydralazine, Minoxidil (Systemic), Minoxidil (Topical)

---

## 1. Objectives

This study aimed to identify and compare signals for **serious cardiac adverse events** associated with **Hydralazine** and **Minoxidil** (systemic and topical). The primary outcomes of interest were:

* **Cardiac tamponade**
* **Pericardial effusion**
* **Pericarditis**
* **Pleural effusion**

Hydralazine was included both as a drug of interest and as a comparator due to its known association with drug-induced lupus and pericardial complications.

---

## 2. Methodology

### Data Source

* FAERS 2023 full dataset (Q1–Q4).
* Only **latest case versions** included (deduplication by CASEID/CASEVERSION).
* Restricted to **U.S. cases** with complete demographic and reaction data.

### Cohort Definitions

* **Hydralazine** (all routes).
* **Minoxidil Systemic** (oral, investigational systemic use).
* **Minoxidil Topical** (dermatological use).
* Comparator group: **All other drugs** ("OTHER").

### Case Processing

* Included **primary suspect drugs** only.
* Linked reactions (MedDRA PT level).
* Focused on four pre-specified cardiac endpoints.

### Statistical Analysis

* **Proportional Reporting Ratio (PRR)** with Haldane–Anscombe correction.
* **Reporting Odds Ratio (ROR)** with Wald 95% confidence intervals.
* **Chi-square test** for statistical significance.
* **Flagging thresholds**:

  * PRR ≥ 2.0
  * χ² ≥ 4.0
  * N ≥ 3 cases

### Validation

* **Positive control:** Ciprofloxacin → Tendon rupture (expected signal).
* **Negative control:** Metformin → Alopecia (expected no signal).
* Both controls behaved as expected, confirming methodology validity.

---

## 3. Results

### Executive Summary

* **Systemic Minoxidil** demonstrated the **strongest disproportionality signals** for cardiac endpoints in 2023 FAERS, meeting all three pre-specified thresholds for cardiac tamponade, pericardial effusion, and pleural effusion.
* **Hydralazine** showed a signal for pericardial effusion (PRR=30.7, N=3), consistent with its known association with drug-induced pericardial disease, but not for cardiac tamponade in this dataset.
* **Topical Minoxidil** showed **no cardiac signals** (all N=0), consistent with low systemic absorption.

### High-Priority Findings

* Minoxidil Systemic + Cardiac Tamponade → PRR = 379.3 (95% CI: 129.5–1111.2, N=3)
* Minoxidil Systemic + Pericardial Effusion → PRR = 114.3 (95% CI: 51.9–252.0, N=5)
* Minoxidil Systemic + Pleural Effusion → PRR = 26.9 (95% CI: 9.3–78.2, N=3)
* Hydralazine + Pericardial Effusion → PRR = 30.7 (95% CI: 10.2–92.5, N=3)

Note: N counts are small for all endpoints. Wide confidence intervals reflect this uncertainty. The PRR for cardiac tamponade is very high partly because this endpoint is rare in the overall 2023 FAERS background (175 total cases across 565K reports).

### Complete Results Table

*(See `results/tables/cardiac_complete.csv` for full signal metrics across all cohorts and endpoints.)*

---

## 4. Interpretation of Disproportionality Findings

*Note: All interpretations below are limited to the strength of the FAERS signal. Disproportionality analysis cannot establish causation, true incidence, or population-level risk.*

### Hydralazine

* **Very high disproportionality** for tamponade and pericardial effusion (PRR > 100).
* Consistent with the established mechanism of drug-induced lupus erythematosus and pericardial disease associated with hydralazine — a labeled risk documented in prior literature.
* **Interpretation:** The disproportionality ratio is large and the association is biologically plausible given known pharmacology. This is consistent with, but does not independently confirm, a causal relationship. The signal magnitude warrants continued pharmacovigilance attention.

### Minoxidil (Systemic)

* Moderate disproportionality for tamponade and pericardial effusion.
* Consistent with fluid retention and hemodynamic effects expected from a potent oral vasodilator.
* **Interpretation:** The signal meets all three pre-specified flagging thresholds and is biologically plausible. This is a hypothesis-generating finding. Clinical monitoring decisions should not be based on FAERS disproportionality data alone.

### Minoxidil (Topical)

* No qualifying cardiac adverse events observed in 2023 FAERS across the four pre-specified endpoints.
* Consistent with low systemic absorption from topical formulations.
* **Interpretation:** Absence of FAERS reports is not proof of safety. However, the null result is consistent with the expected pharmacological profile of topical minoxidil at standard doses.

---

## 5. Signal Summary

| Drug               | Signal Strength | Key Observations                      | Notes                                                  |
| ------------------ | --------------- | ------------------------------------- | ------------------------------------------------------ |
| Minoxidil Systemic | High            | Tamponade (PRR=379, N=3), effusion    | Large PRR; wide CI due to small N; meets all thresholds |
| Hydralazine        | Moderate        | Pericardial effusion (PRR=31, N=3)    | Consistent with labeled lupus/pericardial risk          |
| Minoxidil Topical  | Not detected    | None observed in 2023 FAERS           | Consistent with low systemic absorption                 |

*Signal strength refers to disproportionality ratio magnitude, not clinical risk. N values are small; interpret with caution. These findings do not support clinical recommendations on their own.*

---

## 6. Limitations

* FAERS is a **spontaneous reporting system** → subject to underreporting, reporting bias, and confounding.
* Disproportionality ≠ causality — signals indicate associations, not proof.
* Cohort sizes vary widely; topical Minoxidil has few reports relative to systemic or Hydralazine.
* Prescription volume normalization not applied in this report (planned for future integration with Medicare data).

---

## 7. Visual Summaries

* **Bar plots:** Case counts across cohorts and endpoints.
* **Forest plots:** PRR with 95% CI, log-scaled for clarity.
* **Streamlit App:** Interactive dashboard developed for reproducibility, exploration, and visualization.

---

## 8. Conclusions

* **Hydralazine** shows the largest disproportionality ratios among the three cohorts, consistent with its established association with drug-induced pericardial disease in the literature.
* **Systemic minoxidil** meets all three pre-specified signal detection thresholds for two cardiac endpoints, consistent with its hemodynamic and fluid-retention pharmacology.
* **Topical minoxidil** produced no qualifying signals in 2023 FAERS, consistent with low systemic absorption at standard doses.
* All findings are exploratory and hypothesis-generating. They should not be used as the sole basis for clinical recommendations. Confirmation would require epidemiological designs with exposure denominators and appropriate confounding control.

---

## 9. Deliverables

* **Trimmed cardiac endpoint tables** (CSV + Markdown).
* **Figures:** Bar + forest plots.
* **Streamlit App (`app.py`)**: Allows dynamic exploration of FAERS signals across all cohorts and endpoints.
* **Validation tests:** Controls confirm pipeline reproducibility.
* **Full repo structure:** Scripts (`scripts/`), core modules (`src/`), tests (`tests/`), outputs (`results/`), and app (`app/`).

---

*This analysis is for research purposes only. Clinical decision-making should not rely solely on FAERS disproportionality analysis.*

