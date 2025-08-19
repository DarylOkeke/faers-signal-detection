-- =========================================
-- STEP 6: Event-level table
--  - Unit: (PRIMARYID, INGREDIENT_STD, REACTION_PT)
--  - Scope: PS drugs only, for cleaned 2023 US cases
--  - Adds: age/sex, year/quarter, indication (if present), outcome flags
-- Output: faers_events_2023
-- =========================================

DROP TABLE IF EXISTS faers_events_2023;

CREATE TABLE faers_events_2023 AS
SELECT DISTINCT
  dmo.year,                                  -- for time slicing (2023, but keep it explicit)
  dmo.quarter,                               -- 1-4
  dmo.primaryid,                             -- case key
  dmo.caseid,                                -- stable case ID (dedup context)
  dmo.age_yrs,
  dmo.sex,
  drg.ingredient_std,                        -- normalized active ingredient (PS)
  drg.route,                                 -- route of administration
  drg.role_cod,                              -- should be 'PS'
  rac.reaction_pt,                           -- MedDRA PT
  ind.indi_pt,                               -- MedDRA PT for indication (nullable)
  outc.serious_any,
  outc.outc_de, outc.outc_lt, outc.outc_ho, outc.outc_ds, outc.outc_ca, outc.outc_ri, outc.outc_ot
FROM faers_drug_2023_ps drg
JOIN faers_demo_2023_latest_us dmo
  ON dmo.primaryid = drg.primaryid
JOIN faers_reac_2023_keep rac
  ON rac.primaryid = drg.primaryid
LEFT JOIN faers_indi_2023_keep ind
  ON ind.primaryid    = drg.primaryid
 AND ind.indi_drug_seq = drg.drug_seq         -- link indication to THIS suspect drug
LEFT JOIN faers_outc_2023_flags outc
  ON outc.primaryid = drg.primaryid;

-- Helpful indexes for analysis speed
CREATE INDEX IF NOT EXISTS idx_events_ing_pt ON faers_events_2023(ingredient_std, reaction_pt);
CREATE INDEX IF NOT EXISTS idx_events_year_q ON faers_events_2023(year, quarter);
CREATE INDEX IF NOT EXISTS idx_events_pid    ON faers_events_2023(primaryid);
