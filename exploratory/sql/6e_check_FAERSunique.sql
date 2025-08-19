-- 1) Row count
-- Expectation: Should drop vs faers_events_2023(n_after < n_before)
SELECT 
  (SELECT COUNT(*) FROM faers_events_2023)        AS n_before,
  (SELECT COUNT(*) FROM faers_events_2023_unique) AS n_after;

-- 2) Confirm no duplicates remain within a case
--  Expectation: Max dup count per (caseid, ing, pt) should now be 1
SELECT MAX(cnt) AS max_dups_after
FROM (
  SELECT caseid, ingredient_std, reaction_pt, COUNT(*) AS cnt
  FROM faers_events_2023_unique
  GROUP BY caseid, ingredient_std, reaction_pt
);

-- 3) Coverage: fraction of cases that have at least one deduped event
-- Expectation: Extremely close to one
SELECT
  (SELECT COUNT(DISTINCT caseid) FROM faers_events_2023_unique) * 1.0
  / (SELECT COUNT(*) FROM faers_demo_2023_latest_us) AS frac_cases_with_event;

-- 4) Top 10 ingredients (distinct cases) using the UNIQUE table
-- Expectation: There'll be a slight reduction for some ingredients, but Dupilumab will still be the most common.
SELECT ingredient_std, COUNT(DISTINCT caseid) AS cases
FROM faers_events_2023_unique
GROUP BY ingredient_std
ORDER BY cases DESC
LIMIT 10;

-- 5) Top 15 PTs (distinct cases) using the UNIQUE table
-- Expectation: Similar to ingredients, some reduction in counts but key PTs remain prominent.
SELECT reaction_pt, COUNT(DISTINCT caseid) AS cases
FROM faers_events_2023_unique
GROUP BY reaction_pt
ORDER BY cases DESC
LIMIT 15;
