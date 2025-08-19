-- =====================================================
-- STEP 8A ingredient × reaction counts
-- =====================================================

DROP TABLE IF EXISTS faers_counts_drug_reac_2023;

CREATE TABLE faers_counts_drug_reac_2023 AS
SELECT
  ingredient_std,
  reaction_pt,
  route,
  COUNT(DISTINCT caseid) AS cases_with_event
FROM faers_events_2023_unique
GROUP BY ingredient_std, route, reaction_pt;

-- Helpful for quick lookups
CREATE INDEX IF NOT EXISTS idx_counts_drug_reac ON faers_counts_drug_reac_2023(ingredient_std, route, reaction_pt);


-- =====================================================
--  all-drug totals per reaction
-- =====================================================

DROP TABLE IF EXISTS faers_counts_reac_all_2023;

CREATE TABLE faers_counts_reac_all_2023 AS
SELECT
  reaction_pt,
  COUNT(DISTINCT caseid) AS cases_with_event
FROM faers_events_2023_unique
GROUP BY reaction_pt;

CREATE INDEX IF NOT EXISTS idx_counts_reac_all ON faers_counts_reac_all_2023(reaction_pt);

-- =====================================================
--  total cases per drug( incase we want to make our denominator
--  "all cases on a certain drug in FAERS" for PRR/ROR)
-- =====================================================

DROP TABLE IF EXISTS faers_counts_drug_all_2023;

CREATE TABLE faers_counts_drug_all_2023 AS
SELECT
  ingredient_std,
  COUNT(DISTINCT caseid) AS cases_with_drug
FROM faers_events_2023_unique
GROUP BY ingredient_std;

CREATE INDEX IF NOT EXISTS idx_counts_drug_all ON faers_counts_drug_all_2023(ingredient_std);
