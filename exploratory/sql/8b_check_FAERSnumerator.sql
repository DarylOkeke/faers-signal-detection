-- 1) How many (drug, reaction) pairs?
-- Expectation: Thousands; there were 348355 in 2023.
SELECT COUNT(*) FROM faers_counts_drug_reac_2023;

-- 2) Spot top signals by raw count
-- Expectation: We can see which ingredients are tied to the highest reaction counts
-- EVOLOCUMAB should be among the top
SELECT * FROM faers_counts_drug_reac_2023
ORDER BY cases_with_event DESC
LIMIT 10;

-- 3) Consistency: total events should match
-- Expectation:Sum of drug-event cases should equal total event rows
SELECT
  (SELECT COUNT(*) FROM faers_events_2023_unique)    AS event_rows,
  (SELECT SUM(cases_with_event) FROM faers_counts_drug_reac_2023) AS summed_pairs;

-- 4) How many unique PTs overall?
-- Expectation: There are 12577 PTs in 2023
SELECT COUNT(*) FROM faers_counts_reac_all_2023;
