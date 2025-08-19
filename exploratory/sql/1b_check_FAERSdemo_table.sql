--Check that everything matches our expectations for the new table



-- 1) Row count: how many latest US 2023 cases do we have?
-- Expectation: 890192
SELECT COUNT(*) AS n_rows FROM faers_demo_2023_latest_us;

-- 2) Distinct CASEIDs vs PRIMARYIDs
-- Expectation: 1:1 after dedup, but PRIMARYID is the join key
SELECT 
  COUNT(DISTINCT caseid)    AS n_caseids,
  COUNT(DISTINCT primaryid) AS n_primaryids
FROM faers_demo_2023_latest_us;

-- 3) Date window check: are all receipts in 2023?
-- Expectation: Min date should be 2023-01-01, max date should be 2023-12-31
SELECT MIN(receipt_date) AS min_dt, MAX(receipt_date) AS max_dt
FROM faers_demo_2023_latest_us;

-- 4) Quarter distribution (should be 1..4 only)
-- Expectation: 4 quarters
SELECT quarter, COUNT(*) AS n
FROM faers_demo_2023_latest_us
GROUP BY quarter
ORDER BY quarter;

-- 5) Country and sex sanity check
-- Expectation: should be US/USA only and sex standardized to M/F/U
SELECT occr_country, sex, COUNT(*) AS n
FROM faers_demo_2023_latest_us
GROUP BY occr_country, sex
ORDER BY n DESC;

-- 6) Age completeness snapshot
-- Expectation: Apparently it is common for FAERS to only have around half missing
SELECT
  SUM(CASE WHEN age_yrs IS NULL THEN 1 ELSE 0 END) AS n_age_missing,
  ROUND(100.0 * SUM(CASE WHEN age_yrs IS NULL THEN 1 ELSE 0 END) / COUNT(*), 2) AS pct_age_missing
FROM faers_demo_2023_latest_us;


