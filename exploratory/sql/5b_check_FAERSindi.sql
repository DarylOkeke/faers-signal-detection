-- 1) Row count
-- Expectation: Many cases have 0 indications; multi-drug cases often have multiple indications (one per drug).
SELECT COUNT(*) AS n_indi_rows FROM faers_indi_2023_keep;

-- 2) Coverage: fraction of suspect-drug rows that have an attached indication
-- Expectation: Often 0.4–0.8 depending on year; indication coding is spotty.
SELECT
  (
    SELECT COUNT(*) 
    FROM faers_indi_2023_keep k
    JOIN faers_drug_2023_ps d
      ON d.primaryid = k.primaryid AND d.drug_seq = k.indi_drug_seq
  ) * 1.0 / 
  (SELECT COUNT(*) FROM faers_drug_2023_ps) AS frac_ps_drugs_with_indi;

-- 3) How many indications per suspect drug (fan-out)
-- Expectation: Usually 0 or 1; sometimes >1 if reporter listed multiple reasons.
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
-- Expectation: You’ll see big chronic diseases (e.g., DIABETES MELLITUS, HYPERTENSION, etc.)
SELECT k.indi_pt, COUNT(DISTINCT k.primaryid) AS cases
FROM faers_indi_2023_keep k
JOIN faers_drug_2023_ps d
  ON d.primaryid = k.primaryid AND d.drug_seq = k.indi_drug_seq
GROUP BY k.indi_pt
ORDER BY cases DESC
LIMIT 15;
