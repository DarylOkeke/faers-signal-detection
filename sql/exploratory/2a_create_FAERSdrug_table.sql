--==================================================================================
-- STEP 2: Pull suspect drugs (Primary Suspect only) for the cleaned 2023 US cases.
-- - Filters DRUG rows to those whose PRIMARYID is in faers_demo_2023_latest_us
-- - Restricts to ROLE_COD = 'PS' (Primary Suspect)
-- - Normalizes a working ingredient key 'ingredient_std' using PROD_AI if present
--==================================================================================

DROP TABLE IF EXISTS faers_drug_2023_ps;

CREATE TABLE faers_drug_2023_ps AS
SELECT
  d.primaryid,                                   -- join back to demo/reac/outc/indi
  d.drug_seq,                                    -- needed to tie indications to this specific drug
  UPPER(TRIM(COALESCE(d.role_cod,''))) AS role_cod,
  /* Keep raw names for debugging/audits */
  UPPER(TRIM(d.drugname))  AS drugname_raw,
  UPPER(TRIM(d.prod_ai))   AS prod_ai_raw,

  /* Ingredient key for analysis: prefer PROD_AI (active ingredient), else DRUGNAME */
  CASE
    WHEN TRIM(COALESCE(d.prod_ai,'')) <> '' THEN UPPER(TRIM(d.prod_ai))
    ELSE UPPER(TRIM(d.drugname))
  END AS ingredient_std
FROM faers_drug_2023_all d
JOIN faers_demo_2023_latest_us demo USING (primaryid)  -- restrict to our cleaned, deduped cases
WHERE UPPER(TRIM(COALESCE(d.role_cod,''))) = 'PS';

-- Helpful indexes for performance
CREATE INDEX IF NOT EXISTS idx_drug_ps_primaryid ON faers_drug_2023_ps(primaryid);
CREATE INDEX IF NOT EXISTS idx_drug_ps_drugseq   ON faers_drug_2023_ps(drug_seq);
CREATE INDEX IF NOT EXISTS idx_drug_ps_ing       ON faers_drug_2023_ps(ingredient_std);
