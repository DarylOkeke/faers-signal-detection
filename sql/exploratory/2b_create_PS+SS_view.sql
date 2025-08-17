/*This part is optional, but I'm adding it in because
we may want to analyze both Primary Suspect and Secondary
Suspect later */

CREATE VIEW IF NOT EXISTS faers_drug_2023_psss AS
SELECT
  d.primaryid,
  d.drug_seq,
  UPPER(TRIM(COALESCE(d.role_cod,''))) AS role_cod,
  UPPER(TRIM(d.drugname))  AS drugname_raw,
  UPPER(TRIM(d.prod_ai))   AS prod_ai_raw,
  CASE
    WHEN TRIM(COALESCE(d.prod_ai,'')) <> '' THEN UPPER(TRIM(d.prod_ai))
    ELSE UPPER(TRIM(d.drugname))
  END AS ingredient_std
FROM faers_drug_2023_all d
JOIN faers_demo_2023_latest_us demo USING (primaryid)
WHERE UPPER(TRIM(COALESCE(d.role_cod,''))) IN ('PS','SS');
