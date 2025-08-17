
-- START HERE

-- Combine all 2023 quarters into 5 major view: demo, drug, reac, outc, and indi

-- DEMO: all 2023
CREATE VIEW IF NOT EXISTS faers_demo_2023_all AS
SELECT * FROM faers_demo_2023q1
UNION ALL SELECT * FROM faers_demo_2023q2
UNION ALL SELECT * FROM faers_demo_2023q3
UNION ALL SELECT * FROM faers_demo_2023q4;

-- DRUG: all 2023
CREATE VIEW IF NOT EXISTS faers_drug_2023_all AS
SELECT * FROM faers_drug_2023q1
UNION ALL SELECT * FROM faers_drug_2023q2
UNION ALL SELECT * FROM faers_drug_2023q3
UNION ALL SELECT * FROM faers_drug_2023q4;

-- REAC: all 2023
CREATE VIEW IF NOT EXISTS faers_reac_2023_all AS
SELECT * FROM faers_reac_2023q1
UNION ALL SELECT * FROM faers_reac_2023q2
UNION ALL SELECT * FROM faers_reac_2023q3
UNION ALL SELECT * FROM faers_reac_2023q4;

-- OUTC: all 2023
CREATE VIEW IF NOT EXISTS faers_outc_2023_all AS
SELECT * FROM faers_outc_2023q1
UNION ALL SELECT * FROM faers_outc_2023q2
UNION ALL SELECT * FROM faers_outc_2023q3
UNION ALL SELECT * FROM faers_outc_2023q4;

-- INDI: all 2023
CREATE VIEW IF NOT EXISTS faers_indi_2023_all AS
SELECT * FROM faers_indi_2023q1
UNION ALL SELECT * FROM faers_indi_2023q2
UNION ALL SELECT * FROM faers_indi_2023q3
UNION ALL SELECT * FROM faers_indi_2023q4;


