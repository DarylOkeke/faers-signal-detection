-- @conn FAERS

SELECT
    (SELECT
     COUNT(primaryid) FROM reac24q4) AS total_reports_24q4,
    (SELECT COUNT(primaryid) FROM reac25q1) AS total_reports_25q1,
    (SELECT COUNT(primaryid) FROM demo24q4) AS total_demo_24q4,
    (SELECT COUNT(primaryid) FROM demo25q1) AS total_demo_25q1