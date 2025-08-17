# Cardiac Endpoints Signal Detection Analysis

**Analysis Date:** August 17, 2025  
**Database:** FAERS 2023 (4 quarters)  
**Methodology:** Disproportionality Analysis (PRR, ROR, Chi-square)  
**Cohorts:** Hydralazine, Minoxidil Systemic, Minoxidil Topical  

## Executive Summary

This analysis examined cardiac adverse event signals for three drug cohorts using FDA Adverse Event Reporting System (FAERS) data from 2023. **Hydralazine demonstrated the strongest cardiac safety signals**, with extremely elevated reporting ratios for serious cardiac endpoints.

### Key Findings

🔴 **HIGH PRIORITY SIGNALS**
- **Hydralazine + Cardiac Tamponade**: PRR = 165.8 (95% CI: 73.1-375.7)
- **Hydralazine + Pericardial Effusion**: PRR = 51.0 (95% CI: 28.4-91.8)
- **Minoxidil Systemic + Cardiac Tamponade**: PRR = 49.2 (95% CI: 18.2-133.5)
- **Minoxidil Systemic + Pericardial Effusion**: PRR = 12.5 (95% CI: 5.6-27.9)

⚪ **NO SIGNALS DETECTED**
- **Minoxidil Topical**: No cardiac endpoints reported (all PRR = 0.0)

## Detailed Results

### Flagging Criteria
- **PRR ≥ 2.0** (at least 2x higher reporting than background)
- **χ² ≥ 4.0** (statistically significant association)  
- **N ≥ 3** (minimum case count for reliability)

### Complete Analysis Table

| Cohort | Cardiac Endpoint | Cases (N) | PRR | 95% CI Lower | 95% CI Upper | χ² | Signal | Decision |
|--------|------------------|-----------|-----|--------------|--------------|----|---------| ---------|
| **HYDRALAZINE** | Cardiac Tamponade | 6 | 165.8 | 73.1 | 375.7 | 924.4 | 🔴 **YES** | Reject H₀ |
| **HYDRALAZINE** | Pericardial Effusion | 11 | 51.0 | 28.4 | 91.8 | 529.4 | 🔴 **YES** | Reject H₀ |
| **HYDRALAZINE** | Pericarditis | 2 | 30.2 | 7.5 | 121.1 | 55.8 | ⚫ **NO** | Fail to reject H₀* |
| **HYDRALAZINE** | Pleural Effusion | 1 | 2.4 | 0.3 | 17.1 | 0.8 | ⚫ **NO** | Fail to reject H₀* |
| **MINOXIDIL_SYSTEMIC** | Cardiac Tamponade | 4 | 49.2 | 18.2 | 133.5 | 181.5 | 🔴 **YES** | Reject H₀ |
| **MINOXIDIL_SYSTEMIC** | Pericardial Effusion | 6 | 12.5 | 5.6 | 27.9 | 63.1 | 🔴 **YES** | Reject H₀ |
| **MINOXIDIL_SYSTEMIC** | Pericarditis | 1 | 6.8 | 1.0 | 48.6 | 4.9 | ⚫ **NO** | Fail to reject H₀* |
| **MINOXIDIL_SYSTEMIC** | Pleural Effusion | 2 | 2.2 | 0.5 | 8.8 | 1.3 | ⚫ **NO** | Fail to reject H₀* |
| **MINOXIDIL_TOPICAL** | Cardiac Tamponade | 0 | 0.0 | - | - | 0.0 | ⚫ **NO** | Fail to reject H₀ |
| **MINOXIDIL_TOPICAL** | Pericardial Effusion | 0 | 0.0 | - | - | 0.0 | ⚫ **NO** | Fail to reject H₀ |
| **MINOXIDIL_TOPICAL** | Pericarditis | 0 | 0.0 | - | - | 0.0 | ⚫ **NO** | Fail to reject H₀ |
| **MINOXIDIL_TOPICAL** | Pleural Effusion | 0 | 0.0 | - | - | 0.0 | ⚫ **NO** | Fail to reject H₀ |

*\*Not flagged due to insufficient case count (N < 3)*

## Clinical Interpretation

### Hydralazine Cardiac Risk Profile
**Hydralazine shows exceptionally strong signals for serious cardiac complications:**

- **Cardiac Tamponade (PRR=165.8)**: 166× higher reporting than background rate
  - *Clinical significance*: Life-threatening emergency requiring immediate intervention
  - *Mechanism*: Possible drug-induced lupus leading to pericardial inflammation

- **Pericardial Effusion (PRR=51.0)**: 51× higher reporting than background
  - *Clinical significance*: Can progress to cardiac tamponade
  - *Mechanism*: Inflammatory response affecting pericardium

### Minoxidil Systemic Risk Profile
**Moderate but significant cardiac signals:**

- **Cardiac Tamponade (PRR=49.2)**: 49× higher reporting than background
- **Pericardial Effusion (PRR=12.5)**: 13× higher reporting than background
- *Mechanism*: Likely related to fluid retention and cardiovascular effects

### Minoxidil Topical Safety Profile
**No cardiac signals detected:**
- Zero cases reported for all cardiac endpoints
- Supports safety of topical route vs. systemic exposure

## Risk Assessment Summary

| Drug | Overall Cardiac Risk | Key Concerns | Recommendation |
|------|---------------------|--------------|----------------|
| **Hydralazine** | 🔴 **Very High** | Tamponade, Pericardial effusion | Enhanced monitoring required |
| **Minoxidil Systemic** | 🟡 **Moderate** | Tamponade, Pericardial effusion | Cardiac monitoring advised |
| **Minoxidil Topical** | 🟢 **Low** | No signals detected | Standard monitoring |

## Methodology Notes

- **Study Design**: Retrospective disproportionality analysis
- **Data Source**: FDA FAERS database, 2023 (all 4 quarters)
- **Statistical Method**: Proportional Reporting Ratio (PRR) with Haldane-Anscombe correction
- **Cohort Definition**: Drug-specific cohorts with route-based classification
- **Limitations**: Observational data, reporting bias, confounding factors

## Clinical Recommendations

1. **Hydralazine patients**: Implement cardiac monitoring protocols, especially for pericardial complications
2. **Systemic minoxidil patients**: Consider baseline and periodic cardiac assessment
3. **Topical minoxidil patients**: Standard care protocols appear adequate
4. **Healthcare providers**: Maintain awareness of these differential risk profiles

---

**Analysis Generated**: August 17, 2025  
**Contact**: FAERS Signal Detection Team  
**Repository**: faers-signal-detection  

*This analysis is for research purposes. Clinical decisions should not be based solely on FAERS disproportionality analysis. Always consult healthcare professionals and consider multiple data sources for drug safety evaluation.*
