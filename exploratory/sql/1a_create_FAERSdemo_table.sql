-- ================================
-- STEP 1 (REBUILD CLEAN ANCHOR)
-- Latest US cases received in 2023
-- Dedup by CASEID → max CASEVERSION
-- Normalize: date, sex (M/F/U only), age in years, year/quarter
-- ================================

BEGIN;

DROP TABLE IF EXISTS faers_demo_2023_latest_us;

CREATE TABLE faers_demo_2023_latest_us AS
WITH
  /* 1) Normalize dates to a single receipt_date */
  demo_norm AS (
    SELECT
      primaryid,            -- join key to other FAERS tables
      caseid,               -- stable across versions (used for dedup)
      caseversion,          -- higher = newer version of the same case
      occr_country,         -- occurrence country (will filter to US/USA)
      sex,                  -- raw sex code (will be standardized)
      age,                  -- raw age value
      age_cod,              -- units for age (YR/MON/WK/DY/HR/etc.)
      /* Choose a receipt-like date and parse yyyymmdd → yyyy-mm-dd */
      CASE
        WHEN length(COALESCE(fda_dt, init_fda_dt, rept_dt)) = 8
        THEN DATE(
               substr(COALESCE(fda_dt, init_fda_dt, rept_dt),1,4) || '-' ||
               substr(COALESCE(fda_dt, init_fda_dt, rept_dt),5,2) || '-' ||
               substr(COALESCE(fda_dt, init_fda_dt, rept_dt),7,2)
             )
        ELSE DATE(COALESCE(fda_dt, init_fda_dt, rept_dt))
      END AS receipt_date
    FROM faers_demo_2023_all
  ),

  /* 2) Keep only US reports received in calendar 2023 */
  demo_2023_us AS (
    SELECT *
    FROM demo_norm
    WHERE UPPER(TRIM(COALESCE(occr_country,''))) IN ('US','USA')
      AND receipt_date >= DATE('2023-01-01')
      AND receipt_date <  DATE('2024-01-01')
  ),

  /* 3) Deduplicate to the latest version per CASEID */
  latest_per_case AS (
    SELECT
      *,
      ROW_NUMBER() OVER (
        PARTITION BY caseid
        ORDER BY caseversion DESC, primaryid DESC
      ) AS rn
    FROM demo_2023_us
  ),

  /* 4) Standardize sex and convert age to years */
  standardized AS (
    SELECT
      primaryid,
      caseid,
      caseversion,
      /* Normalize country to a single 'US' value for consistency */
      'US' AS occr_country,
      /* Strict sex mapping → only M, F, or U */
      CASE
        WHEN UPPER(TRIM(sex)) IN ('M','MALE') THEN 'M'
        WHEN UPPER(TRIM(sex)) IN ('F','FEMALE') THEN 'F'
        ELSE 'U'   -- UNK/UNKNOWN/NR/NA/blank/etc. → U
      END AS sex,
      receipt_date,
      /* Convert age to years using FAERS age_cod */
      CASE UPPER(COALESCE(age_cod,''))
        WHEN 'YR'  THEN CAST(age AS REAL)
        WHEN 'MON' THEN CAST(age AS REAL) / 12.0
        WHEN 'WK'  THEN CAST(age AS REAL) / 52.1429
        WHEN 'DY'  THEN CAST(age AS REAL) / 365.25
        WHEN 'HR'  THEN CAST(age AS REAL) / (24.0*365.25)
        ELSE NULL  -- unknown or odd units → leave missing
      END AS age_yrs
    FROM latest_per_case
    WHERE rn = 1
  )

/* 5) Final select with time slices */
SELECT
  primaryid,
  caseid,
  caseversion,
  receipt_date,
  CAST(strftime('%Y', receipt_date) AS INT) AS year,
  ((CAST(strftime('%m', receipt_date) AS INT) - 1) / 3) + 1 AS quarter,
  occr_country,       -- now always 'US'
  sex,                -- now only M/F/U
  age_yrs
FROM standardized;

COMMIT;

-- Indexes for fast joins & filters
CREATE INDEX IF NOT EXISTS idx_demo_latest_primaryid ON faers_demo_2023_latest_us(primaryid);
CREATE INDEX IF NOT EXISTS idx_demo_latest_caseid    ON faers_demo_2023_latest_us(caseid);
