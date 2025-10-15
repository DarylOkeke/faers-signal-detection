
# Basis and Relevance of Hypothesis

## Pharmacology / Biology

* Oral minoxidil is a potent vasodilator → fluid retention, pericardial fluid accumulation are biologically plausible.
* Topical exposure is minimal systemically → you don’t expect the same cardiac risk.

## Prior Evidence

* Case reports/series and safety blurbs from 2023–2025 flagged **pericardial effusion, pericarditis, and tamponade** with oral minoxidil.
* Historical high-dose antihypertensive use of minoxidil also had fluid-related AEs.
* This is enough to justify a **directional hypothesis** without “proving” anything yet.

## Epidemiologic Aspect

* In 2023, there was a surge in **off-label oral use** → more exposure, more chances to see rare serious AEs in FAERS.
* Topical minoxidil is common but has low systemic absorption → makes a built-in comparator expected to be near-null.

## Clinical Impact

* **Pericardial effusion → tamponade is severe.**
* Even small disproportionality is clinically meaningful, so it’s worth looking into.

---

# Primary Drug–Event Hypotheses (per PT)

**Drug:** Oral minoxidil (`ingredient_std = MINOXIDIL`, `route = ORAL/PO`)
**Events (PTs):**

* Primary: **PERICARDIAL EFFUSION**

* Secondary: **PERICARDITIS, CARDIAC TAMPONADE**

* **H₀:** Reporting of the event with oral minoxidil is not disproportionate vs all other drugs in 2023 FAERS (PRR = 1; χ² not significant).

* **H₁ (directional):** Reporting is disproportionately higher (PRR > 1) and meets prespecified thresholds:

  * PRR ≥ 2
  * χ² ≥ 4
  * N ≥ 3

---

# Negative / Low-Exposure Comparators (Falsification Checks)

**Topical minoxidil (route = TOPICAL / CUTANEOUS)** for the same PTs:

* **H₀:** No disproportion (PRR ≈ 1).
* **H₁:** Any observed signal should be weaker than oral and unlikely to meet thresholds.

**Therapeutic comparator (e.g., hydralazine):**

* **H₀:** No disproportion for the same PTs.
* **Purpose:** Show the signal isn’t just “cardio patients get cardio AEs.”

---

# Controls (Method Validity)

* **Positive control:** Ciprofloxacin → Tendon rupture → expect a clear signal (should meet thresholds).
* **Negative control:** Metformin → Alopecia → expect no signal (PRR ≈ 1).

---


**Decision criteria:** Flag a signal if all are true:

* PRR ≥ 2
* χ² ≥ 4
* N ≥ 3

**Caveat:** FAERS ≠ incidence; signal ≠ causation.

---

# If–Then Interpretation

* **If oral PRR meets thresholds and topical does not:**
  “Supports a route-consistent, disproportionate reporting signal.”

* **If both oral and topical are null:**
  “No disproportion in 2023; case reports may reflect rare idiosyncrasy or earlier periods—further monitoring warranted.”

* **If only PS flags but PS+SS doesn’t:**
  “Signal is sensitive to role-code noise; retain as hypothesis-generating.”

* **If positive control fails or negative control flags:**
  “Methodological issue—revisit joins, dedup, role filters.”

