
-- Compare FAERS report counts for Dupixent vs. Adbry in Q1 2025
SELECT
  drugname,
  COUNT(*) AS report_count, quarter
FROM
  drug25q1
WHERE
  drugname IN ('DUPIXENT', 'ADBRY')
GROUP BY
  drugname;

