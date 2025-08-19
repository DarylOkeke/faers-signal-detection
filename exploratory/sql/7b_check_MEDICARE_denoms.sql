-- 1) How many unique ingredients in Medicare?
-- Expectation: A little over 1700 in 2023
SELECT COUNT(*) AS n_ingredients FROM medicare_denoms_2023;

-- 2) Coverage: amount of FAERS ingredients vs amount of distinct ingredients that are in both Medicare and FAERS.
-- Expectation: For 2023, there's a little under 1000 matched drugs, but there could be slight variances
-- in the names that the query doesn't pick up

SELECT
  (SELECT COUNT(DISTINCT e.ingredient_std) 
     FROM faers_events_2023_unique e)                                     AS faers_ings,
  (SELECT COUNT(DISTINCT e.ingredient_std)
     FROM faers_events_2023_unique e
     JOIN medicare_denoms_2023 m ON m.ingredient_std = e.ingredient_std)  AS matched_ings;

-- 3) Spot top 10 Medicare exposure by fills
-- Expectation: Common drugs will dominate.Most common is ATORVASTATIN CALCIUM.
SELECT ingredient_std, tot_30day_fills
FROM medicare_denoms_2023
ORDER BY tot_30day_fills DESC
LIMIT 10;

-- 4) Quick join row count
-- Expectation: Should equal events table size; it's a left join in the view (2428270 for 2023)
SELECT COUNT(*) AS n_rows
FROM faers_events_with_denoms_2023;

