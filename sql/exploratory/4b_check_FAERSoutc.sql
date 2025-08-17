-- 1) Row count
-- Expectation: You should see a count lower than 50% of the total demo cases.
SELECT COUNT(*) AS n_outc_rows FROM faers_outc_2023_flags;

-- 2) Fraction of demo cases with an OUTC row
-- Expectation: Around 30%-40% (about .35 for 2023 data)
SELECT
  (SELECT COUNT(*) FROM faers_outc_2023_flags) * 1.0
  / (SELECT COUNT(*) FROM faers_demo_2023_latest_us) AS frac_cases_with_outc;

-- 3) Distribution of serious_any
-- Expectation: usually ~40-50%% of reports flagged serious (FAERS is biased to serious).
-- Note that this means only around 10-20% of all US reports are serious for 2023
SELECT serious_any, COUNT(*) AS n
FROM faers_outc_2023_flags
GROUP BY serious_any;

-- 4) Top outcome types (counts of each flag)
-- Expectation: Besides 'Other', Hospitalization should be the highest and Death should be second most common.
SELECT
  SUM(outc_de) AS n_death,
  SUM(outc_lt) AS n_life_threat,
  SUM(outc_ho) AS n_hosp,
  SUM(outc_ds) AS n_disability,
  SUM(outc_ca) AS n_congenital,
  SUM(outc_ri) AS n_intervention,
  SUM(outc_ot) AS n_other
FROM faers_outc_2023_flags;
