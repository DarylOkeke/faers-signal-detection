-- =========================================
-- STEP 4: Collapse outcomes into boolean flags
-- Source: faers_outc_2023_all (Q1–Q4 stitched view)
-- Filter: only PRIMARYIDs from faers_demo_2023_latest_us
-- Clean: pivot OUTC_COD into columns (DE, LT, HO, DS, CA, RI, OT)
-- Output: faers_outc_2023_flags (1 row per case)
-- =========================================

DROP TABLE IF EXISTS faers_outc_2023_flags;

CREATE TABLE faers_outc_2023_flags AS
SELECT
  o.primaryid,

  -- Individual outcome flags
  MAX(CASE WHEN UPPER(outc_cod) = 'DE' THEN 1 ELSE 0 END) AS outc_de,  -- Death
  MAX(CASE WHEN UPPER(outc_cod) = 'LT' THEN 1 ELSE 0 END) AS outc_lt,  -- Life-threatening
  MAX(CASE WHEN UPPER(outc_cod) = 'HO' THEN 1 ELSE 0 END) AS outc_ho,  -- Hospitalization
  MAX(CASE WHEN UPPER(outc_cod) = 'DS' THEN 1 ELSE 0 END) AS outc_ds,  -- Disability
  MAX(CASE WHEN UPPER(outc_cod) = 'CA' THEN 1 ELSE 0 END) AS outc_ca,  -- Congenital anomaly
  MAX(CASE WHEN UPPER(outc_cod) = 'RI' THEN 1 ELSE 0 END) AS outc_ri,  -- Required intervention
  MAX(CASE WHEN UPPER(outc_cod) = 'OT' THEN 1 ELSE 0 END) AS outc_ot,  -- Other

  -- Summary flag: 1 if any of the serious outcomes is present
  MAX(
    CASE WHEN UPPER(outc_cod) IN ('DE','LT','HO','DS','CA','RI') THEN 1 ELSE 0 END
  ) AS serious_any

FROM faers_outc_2023_all o
JOIN faers_demo_2023_latest_us d USING (primaryid)   -- restrict to our cleaned anchor cases
GROUP BY o.primaryid;

-- Index for quick joining
CREATE INDEX IF NOT EXISTS idx_outc_flags_primaryid ON faers_outc_2023_flags(primaryid);
