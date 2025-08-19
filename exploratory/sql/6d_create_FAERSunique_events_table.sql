-- ==========================================================
--  Important! - Case-level de-dup of drug–event pairs
-- Input : faers_events_2023  (may contain repeats per case)
-- Output: faers_events_2023_unique (one row per CASE × ING × PT)
-- ==========================================================

DROP TABLE IF EXISTS faers_events_2023_unique;

-- 1) Get the unique keys we care about
CREATE TEMP TABLE tmp_unique_keys AS
SELECT DISTINCT
  caseid,
  ingredient_std,
  reaction_pt,
  route
FROM faers_events_2023;

CREATE INDEX IF NOT EXISTS idx_tmp_keys ON tmp_unique_keys(caseid, ingredient_std, reaction_pt,route);

-- 2) Reattach context columns deterministically
--    (Pick ONE representative row per unique key from the source table.)
CREATE TABLE faers_events_2023_unique AS
WITH chosen AS (
  SELECT
    e.caseid,
    e.ingredient_std,
    e.reaction_pt,
    e.route,
    -- choose a stable representative row using ROW_NUMBER over a deterministic order
    ROW_NUMBER() OVER (
      PARTITION BY e.caseid, e.ingredient_std, e.reaction_pt
      ORDER BY e.year, e.quarter, e.primaryid
    ) AS rn,
    e.*
  FROM faers_events_2023 e
  JOIN tmp_unique_keys k
    ON  k.caseid         = e.caseid
    AND k.ingredient_std = e.ingredient_std
    AND k.reaction_pt    = e.reaction_pt
)
SELECT
  year,
  quarter,
  primaryid,
  caseid,
  age_yrs,
  sex,
  route,
  ingredient_std,
  role_cod,         -- should be 'PS'
  reaction_pt,
  indi_pt,          -- nullable
  serious_any,
  outc_de, outc_lt, outc_ho, outc_ds, outc_ca, outc_ri, outc_ot
FROM chosen
WHERE rn = 1;

-- Indexes for fast counting/slicing
CREATE INDEX IF NOT EXISTS idx_events_u_ing_pt   ON faers_events_2023_unique(ingredient_std, reaction_pt);
CREATE INDEX IF NOT EXISTS idx_events_u_case_ing ON faers_events_2023_unique(caseid, ingredient_std);
CREATE INDEX IF NOT EXISTS idx_events_u_year_q   ON faers_events_2023_unique(year, quarter);
