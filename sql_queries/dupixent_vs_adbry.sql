-- Create table with FAERS report counts for Dupixent vs. Adbry across both quarters
DROP TABLE IF EXISTS faers_dupixent_adbry_counts;

CREATE TABLE faers_dupixent_adbry_counts AS
SELECT
  CASE 
    WHEN UPPER(drugname) = 'DUPIXENT' THEN 'Dupixent'
    WHEN UPPER(drugname) = 'ADBRY' THEN 'Adbry'
  END AS drug_name,
  quarter,
  COUNT(*) AS faers_report_count
FROM (
  -- Q4 2024 data
  SELECT drugname, quarter FROM drug24q4 
  WHERE UPPER(drugname) IN ('DUPIXENT', 'ADBRY')
  
  UNION ALL
  
  -- Q1 2025 data  
  SELECT drugname, quarter FROM drug25q1
  WHERE UPPER(drugname) IN ('DUPIXENT', 'ADBRY')
) AS combined_data
GROUP BY drug_name, quarter

UNION ALL

-- Add total across both quarters
SELECT
  drug_name,
  'Total' as quarter,
  SUM(faers_report_count) as faers_report_count
FROM (
  SELECT
    CASE 
      WHEN UPPER(drugname) = 'DUPIXENT' THEN 'Dupixent'
      WHEN UPPER(drugname) = 'ADBRY' THEN 'Adbry'
    END AS drug_name,
    COUNT(*) AS faers_report_count
  FROM (
    SELECT drugname FROM drug24q4 WHERE UPPER(drugname) IN ('DUPIXENT', 'ADBRY')
    UNION ALL
    SELECT drugname FROM drug25q1 WHERE UPPER(drugname) IN ('DUPIXENT', 'ADBRY')
  ) AS all_data
  GROUP BY drug_name
) AS totals
GROUP BY drug_name
ORDER BY drug_name, quarter;