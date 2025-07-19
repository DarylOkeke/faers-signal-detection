# FAERS Column Reference (DEMO, DRUG, REAC, OUTC, THER, INDI, RPSR)

| Table | Column Name   | Meaning                                                       |
|-------|---------------|---------------------------------------------------------------|
| DEMO  | primaryid     | Unique report ID (joins across tables)                        |
| DEMO  | caseid        | Case number assigned to a patient (can have follow‑ups)       |
| DEMO  | age           | Patient age                                                   |
| DEMO  | age_cod       | Age unit (YR = years, MON = months, DY = days)                |
| DEMO  | sex           | Patient sex (M, F, U)                                         |
| DEMO  | wt            | Patient weight                                                |
| DEMO  | wt_cod        | Weight unit (KG, LB)                                          |
| DEMO  | rpt_dt        | Date the report was received                                  |
| DEMO  | occr_country  | Country where the adverse event occurred                      |
| DEMO  | death_dt      | Date of death if the event was fatal                          |
| DRUG  | primaryid     | Unique report ID                                              |
| DRUG  | drug_seq      | Sequence number for multiple drugs in one report              |
| DRUG  | role_cod      | Role of the drug (PS = Primary Suspect, SS = Secondary)       |
| DRUG  | drugname      | Reported drug name                                            |
| DRUG  | route         | Route of administration (ORAL, IV, etc.)                      |
| DRUG  | dose_vbm      | Verbatim dose text as entered                                 |
| DRUG  | doseamt       | Numeric dose amount                                           |
| DRUG  | dosageunit    | Unit for numeric dose (MG, ML, etc.)                          |
| REAC  | primaryid     | Unique report ID                                              |
| REAC  | reac_seq      | Sequence number for multiple reactions in one report          |
| REAC  | pt            | Preferred Term: standardized adverse reaction description     |
| OUTC  | primaryid     | Unique report ID                                              |
| OUTC  | outc_cod      | Outcome of event (DE = Death, HO = Hospitalization, LT = Life‑threatening) |
| THER  | primaryid     | Unique report ID                                              |
| THER  | therapy_seq   | Sequence number for multiple therapy entries                  |
| THER  | start_dt      | Therapy start date                                            |
| THER  | end_dt        | Therapy end date                                              |
| THER  | dur           | Duration of therapy (in days)                                 |
| INDI  | primaryid     | Unique report ID                                              |
| INDI  | indi_seq      | Sequence number for multiple indications in one report        |
| INDI  | indi_pt       | Preferred Term: indication for which the drug was used       |
| RPSR  | primaryid     | Unique report ID                                              |
| RPSR  | rpsr_cod      | Reporter type (e.g., 1 = Physician, 2 = Pharmacist)           |
