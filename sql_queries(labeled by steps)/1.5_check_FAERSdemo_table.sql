--Check that everything matches our expectations for the new table



-- 1) Row count: how many latest US 2023 cases do we have? If nothing was changed, you should have 890192 rows
SELECT COUNT(*) AS n_rows FROM faers_demo_2023_latest_us;

-- 2) Distinct CASEIDs vs PRIMARYIDs (usually 1:1 after dedup, but PRIMARYID is the join key)
SELECT 
  COUNT(DISTINCT caseid)    AS n_caseids,
  COUNT(DISTINCT primaryid) AS n_primaryids
FROM faers_demo_2023_latest_us;

-- 3) Date window check: are all receipts in 2023?
SELECT MIN(receipt_date) AS min_dt, MAX(receipt_date) AS max_dt
FROM faers_demo_2023_latest_us;

-- 4) Quarter distribution (should be 1..4 only)
SELECT quarter, COUNT(*) AS n
FROM faers_demo_2023_latest_us
GROUP BY quarter
ORDER BY quarter;

-- 5) Country and sex sanity (should be US/USA only; sex standardized to M/F/U)
SELECT occr_country, sex, COUNT(*) AS n
FROM faers_demo_2023_latest_us
GROUP BY occr_country, sex
ORDER BY n DESC;

-- 6) Age completeness snapshot
SELECT
  SUM(CASE WHEN age_yrs IS NULL THEN 1 ELSE 0 END) AS n_age_missing,
  ROUND(100.0 * SUM(CASE WHEN age_yrs IS NULL THEN 1 ELSE 0 END) / COUNT(*), 2) AS pct_age_missing
FROM faers_demo_2023_latest_us;


