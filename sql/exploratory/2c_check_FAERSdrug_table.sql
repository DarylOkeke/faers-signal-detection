-- 1) How many PS drug rows did we get?
-- Expectation: 890081
SELECT COUNT(*) AS n_drug_ps FROM faers_drug_2023_ps;

-- 2) Role codes present (should be only PS- so make sure they're the same number)
-- Expectation: 890081
SELECT role_cod, COUNT(*) AS n
FROM faers_drug_2023_ps
GROUP BY role_cod;

-- 3) What fraction of cases have at least one PS drug?
-- Expectation: Most of them, >.97
SELECT 
  (SELECT COUNT(DISTINCT primaryid) FROM faers_drug_2023_ps) * 1.0 
  / (SELECT COUNT(*) FROM faers_demo_2023_latest_us) AS frac_cases_with_ps;

-- 4) Added this in so we can do some quick analysis of the top 10 ingredients with PS drugs
-- Expectation: Dupilumab should be the top ingredient by a landslide
SELECT ingredient_std, COUNT(DISTINCT primaryid) AS cases_with_ps
FROM faers_drug_2023_ps
GROUP BY ingredient_std
ORDER BY cases_with_ps DESC
LIMIT 10;
