-- 1) Row count (event rows)
-- Expectation: Much more than #cases, because each case can have multiple PTs and you can have multiple PS ingredients per case.
SELECT COUNT(*) AS n_event_rows FROM faers_events_2023;

-- 2) Coverage: what fraction of demo cases appear in events (via a PS drug and at least one PT)?
-- Expectation: high (>> 0.95). Some anchor cases might have no PS or blank PTs (rare).
SELECT
  (SELECT COUNT(DISTINCT primaryid) FROM faers_events_2023) * 1.0
  / (SELECT COUNT(*) FROM faers_demo_2023_latest_us) AS frac_cases_with_event;

-- 3) Top 10 ingredients by distinct cases
-- Expectation: Dupilumab by a landslide
SELECT ingredient_std, COUNT(DISTINCT primaryid) AS cases
FROM faers_events_2023
GROUP BY ingredient_std
ORDER BY cases DESC
LIMIT 10;

-- 4) Top 15 reaction PTs overall (distinct cases)
-- Expectation: Most common reactions - Drug Ineffective, off-label use, product does omission issue
SELECT reaction_pt, COUNT(DISTINCT primaryid) AS cases
FROM faers_events_2023
GROUP BY reaction_pt
ORDER BY cases DESC
LIMIT 15;

-- 5) Quick serious-only slice coverage
-- Expectation: substantially fewer rows since OUTC is barely populated; this should be normal.
SELECT COUNT(*) AS n_serious_events
FROM faers_events_2023
WHERE serious_any = 1;

-- 6) Quarter trend
-- Expectation: similar magnitudes across quarters
SELECT quarter, COUNT(DISTINCT primaryid) AS cases
FROM faers_events_2023
GROUP BY quarter
ORDER BY quarter;

-- 7) One more: de-dup within case/ingredient/PT
-- Expectation: FAERS report can evolve (new info comes in), so you get duplicates. This query shows 3 per reaction in 2023.
SELECT ingredient_std, reaction_pt,
       MAX(cnt) AS max_dups
FROM (
  SELECT primaryid, ingredient_std, reaction_pt, COUNT(*) AS cnt
  FROM faers_events_2023
  GROUP BY primaryid, ingredient_std, reaction_pt
)
GROUP BY ingredient_std, reaction_pt
ORDER BY max_dups DESC
LIMIT 5;
