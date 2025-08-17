-- =========================================
-- STEP 5: Indications for valid 2023 US cases
-- Source: faers_indi_2023_all (Q1–Q4 stitched view)
-- Filter: PRIMARYIDs in faers_demo_2023_latest_us
-- Clean: uppercase/trim indi_pt; drop blanks
-- Output: faers_indi_2023_keep
-- =========================================

DROP TABLE IF EXISTS faers_indi_2023_keep;

CREATE TABLE faers_indi_2023_keep AS
SELECT
  i.primaryid,                   -- join key to demo/drug
  i.indi_drug_seq,               -- links to DRUG.DRUG_SEQ (use this to attach indication to the right drug)
  UPPER(TRIM(i.indi_pt)) AS indi_pt
FROM faers_indi_2023_all i
JOIN faers_demo_2023_latest_us d USING (primaryid)   -- only our cleaned, deduped 2023 US cases
WHERE TRIM(COALESCE(i.indi_pt,'')) <> '';            -- drop missing/blank indication terms

-- Helpful index: matches how we’ll join (to suspect drug rows)
CREATE INDEX IF NOT EXISTS idx_indi_keep_pid_seq ON faers_indi_2023_keep(primaryid, indi_drug_seq);
CREATE INDEX IF NOT EXISTS idx_indi_keep_pt      ON faers_indi_2023_keep(indi_pt);
