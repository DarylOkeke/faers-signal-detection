-- top 10 reported drugs across two quarters(combines the last two quarters of data)
SELECT
  drugname,
  SUM(cnt) AS total_reports
FROM (
  SELECT drugname, COUNT(*) AS cnt FROM drug24q4 GROUP BY drugname
  UNION ALL
  SELECT drugname, COUNT(*) AS cnt FROM drug25q1 GROUP BY drugname
) AS combined
GROUP BY
  drugname
ORDER BY
  total_reports DESC
LIMIT 10;
