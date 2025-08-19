-- Example view for age buckets
CREATE VIEW IF NOT EXISTS faers_events_2023_with_agebins AS
SELECT *,
       CASE 
         WHEN age_yrs IS NULL THEN 'UNK'
         WHEN age_yrs < 18    THEN '<18'
         WHEN age_yrs < 45    THEN '18-44'
         WHEN age_yrs < 65    THEN '45-64'
         WHEN age_yrs < 75    THEN '65-74'
         ELSE '75+'
       END AS age_bin
FROM faers_events_2023;

-- Serious events view for quick toggline
CREATE VIEW IF NOT EXISTS faers_events_2023_serious AS
SELECT * FROM faers_events_2023 WHERE serious_any = 1;
