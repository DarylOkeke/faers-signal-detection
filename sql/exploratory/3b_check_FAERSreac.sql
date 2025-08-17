-- 1) Row count
-- Expectation: multiple reactions per case is common;there should be more reaction rows than demo cases.
SELECT COUNT(*) AS n_reac_rows FROM faers_reac_2023_keep;

-- 2) Coverage: how many demo cases have at least one reaction row?
-- Expectation: Should be 1.00 or extremely close to it - if you accidentally dropped some rows, then it will be lower than 1.
SELECT
  (SELECT COUNT(DISTINCT primaryid) FROM faers_reac_2023_keep) * 1.0
  / (SELECT COUNT(*) FROM faers_demo_2023_latest_us) AS frac_cases_with_any_pt;

-- 3) Average # of PTs per case
-- Expectation: usually between 1.3 and 2.5 depending on quarter/year(2.73 in 2023); >1 means multiple PTs per case.
SELECT
  AVG(pt_count) AS avg_pts_per_case,
  MIN(pt_count) AS min_pts_per_case,
  MAX(pt_count) AS max_pts_per_case
FROM (
  SELECT primaryid, COUNT(*) AS pt_count
  FROM faers_reac_2023_keep
  GROUP BY primaryid
);

-- 4) Top 15 reaction PTs by number of distinct cases
-- Expectation: For 2023, you'll see 'DRUG INEFFECTIVE' and 'OFF LABEL USE' as the top reactions.
SELECT reaction_pt, COUNT(DISTINCT primaryid) AS cases_reporting
FROM faers_reac_2023_keep
GROUP BY reaction_pt
ORDER BY cases_reporting DESC
LIMIT 15;

-- 5) Quick blank check (should be zero due to WHERE clause)
-- Expectation: 0 blank PTs, this tells us that we've cleaned properly - we don't want any missing reactions.
SELECT COUNT(*) AS blank_pts
FROM faers_reac_2023_keep
WHERE reaction_pt IS NULL OR reaction_pt = '';
