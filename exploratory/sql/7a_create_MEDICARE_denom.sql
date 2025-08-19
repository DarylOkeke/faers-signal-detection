-- =========================================================
-- STEP 7: Medicare denominators (2023)
-- Goal: one row per ingredient with summed exposure measures
-- Source: medicare_part_d_2023 (prescriber-level rows)
-- Key: ingredient_std (UPPER(TRIM(Gnrc_Name or Brnd_Name)))
-- =========================================================

DROP TABLE IF EXISTS medicare_denoms_2023;

CREATE TABLE medicare_denoms_2023 AS
SELECT
  -- Ingredient key aligned to FAERS ingredient_std
  UPPER(TRIM(COALESCE(Gnrc_Name, Brnd_Name))) AS ingredient_std,

  -- Primary exposure metrics (choose your favorite later)
  SUM(COALESCE(Tot_30day_Fills, 0))  AS tot_30day_fills,  -- my preferred denominator
  SUM(COALESCE(Tot_Clms, 0))         AS tot_clms,         -- scripts
  SUM(COALESCE(Tot_Day_Suply, 0))    AS tot_day_suply,    -- exposure time
  SUM(COALESCE(Tot_Benes, 0))        AS tot_benes,        -- unique beneficiaries

  -- 65+ splits (if present; will be 0 if missing in your file)
  SUM(COALESCE(GE65_Tot_30day_Fills, 0)) AS ge65_tot_30day_fills,
  SUM(COALESCE(GE65_Tot_Clms, 0))        AS ge65_tot_clms,
  SUM(COALESCE(GE65_Tot_Day_Suply, 0))   AS ge65_tot_day_suply,
  SUM(COALESCE(GE65_Tot_Benes, 0))       AS ge65_tot_benes

FROM medicare_part_d_2023
-- Drop rows with no usable name; keeps table tidy
WHERE TRIM(COALESCE(Gnrc_Name, Brnd_Name, '')) <> ''
GROUP BY UPPER(TRIM(COALESCE(Gnrc_Name, Brnd_Name)));

-- Index for fast join on ingredient
CREATE INDEX IF NOT EXISTS idx_med_ing ON medicare_denoms_2023(ingredient_std);

-- =========================================================
-- Join denominators to deduped FAERS event rows
-- This gives pandas everything needed to build 2x2 tables.
-- =========================================================

DROP VIEW IF EXISTS faers_events_with_denoms_2023;

CREATE VIEW faers_events_with_denoms_2023 AS
SELECT
  e.year, e.quarter,
  e.caseid, e.primaryid,
  e.age_yrs, e.sex,
  e.ingredient_std,
  e.reaction_pt,
  e.indi_pt,
  e.serious_any,
  -- denominators (overall & 65+)
  m.tot_30day_fills,
  m.tot_clms,
  m.tot_day_suply,
  m.tot_benes,
  m.ge65_tot_30day_fills,
  m.ge65_tot_clms,
  m.ge65_tot_day_suply,
  m.ge65_tot_benes
FROM faers_events_2023_unique e
LEFT JOIN medicare_denoms_2023 m
  ON m.ingredient_std = e.ingredient_std;
