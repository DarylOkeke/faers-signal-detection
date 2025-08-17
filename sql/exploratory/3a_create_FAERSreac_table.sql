-- =========================================
-- STEP 3: Keep reactions for valid 2023 US cases
-- Source: faers_reac_2023_all (Q1–Q4 stitched view)
-- Filter: PRIMARYIDs in faers_demo_2023_latest_us
-- Clean: uppercase/trim PT; drop blanks
-- Output: faers_reac_2023_keep
-- =========================================

DROP TABLE IF EXISTS faers_reac_2023_keep;

CREATE TABLE faers_reac_2023_keep AS
SELECT DISTINCT
  r.primaryid,                 -- join key to demo & drugs
  UPPER(TRIM(r.pt)) AS reaction_pt  -- normalized MedDRA Preferred Term
FROM faers_reac_2023_all r
JOIN faers_demo_2023_latest_us d USING (primaryid)  -- only our cleaned cases
WHERE TRIM(COALESCE(r.pt,'')) <> '';               -- drop missing/blank PTs

-- Helpful indexes
CREATE INDEX IF NOT EXISTS idx_reac_keep_primaryid ON faers_reac_2023_keep(primaryid);
CREATE INDEX IF NOT EXISTS idx_reac_keep_pt        ON faers_reac_2023_keep(reaction_pt);
