-- 1) Row count
-- Expectation: Each case usually has multiple indications,so you'll likely see over 2x the amount of cases.
SELECT COUNT(*) AS n_indi_rows FROM faers_indi_2023_keep;

-- 2) Fraction of suspect-drug rows that have an  indication
-- Expectation: This tends to vary apparently. But for 2023 it should be > .9
-- Note that the indication coding is spotty
SELECT
  (
    SELECT COUNT(*) 
    FROM faers_indi_2023_keep k
    JOIN faers_drug_2023_ps d
      ON d.primaryid = k.primaryid AND d.drug_seq = k.indi_drug_seq
  ) * 1.0 / 
  (SELECT COUNT(*) FROM faers_drug_2023_ps) AS frac_ps_drugs_with_indi;

-- 3) How many indications per suspect drug 
-- Expectation: Most will be in the 0 or 1 category. Very few will be >1.
SELECT
  CASE 
    WHEN cnt = 0 THEN '0'
    WHEN cnt = 1 THEN '1'
    WHEN cnt BETWEEN 2 AND 3 THEN '2-3'
    ELSE '4+'
  END AS indi_per_ps_drug_bucket,
  COUNT(*) AS n_ps_drugs
FROM (
  SELECT d.primaryid, d.drug_seq, COUNT(k.indi_pt) AS cnt
  FROM faers_drug_2023_ps d
  LEFT JOIN faers_indi_2023_keep k
    ON k.primaryid = d.primaryid AND k.indi_drug_seq = d.drug_seq
  GROUP BY d.primaryid, d.drug_seq
)
GROUP BY indi_per_ps_drug_bucket
ORDER BY indi_per_ps_drug_bucket;

-- 4) Top 15 indication PTs among PS drugs (distinct cases)
--Expectation: You’ll see big chronic diseases ( DIABETES MELLITUS, HYPERTENSION, etc.)
-- Top 15 indication PTs among PS drugs (by distinct cases)

-- This query has issues running using SQLite Tools
SELECT
  indi_pt,
  COUNT(*) AS cases
FROM (
  SELECT DISTINCT
    k.indi_pt,
    k.primaryid
  FROM faers_indi_2023_keep k
  JOIN faers_drug_2023_ps d
    ON d.primaryid = k.primaryid
   AND d.drug_seq  = k.indi_drug_seq
)
GROUP BY indi_pt
ORDER BY cases DESC
LIMIT 15;

