-- Create table with prescription counts for Dupixent vs Adbry from Medicare Part D 2023 data
DROP TABLE IF EXISTS medicare_dupixent_adbry_prescriptions;

CREATE TABLE medicare_dupixent_adbry_prescriptions AS
SELECT 
    CASE 
        WHEN Gnrc_Name = 'Dupilumab' THEN 'Dupixent'
        WHEN Gnrc_Name = 'Tralokinumab-Ldrm' THEN 'Adbry'
    END AS drug_name,
    Gnrc_Name as generic_name,
    COUNT(*) as prescriber_records,
    SUM(CAST(COALESCE(Tot_Clms, '0') AS INTEGER)) as total_claims,
    SUM(CAST(COALESCE(Tot_30day_Fills, '0') AS INTEGER)) as total_30day_fills,
    SUM(CAST(COALESCE(Tot_Benes, '0') AS INTEGER)) as total_beneficiaries,
    ROUND(SUM(CAST(COALESCE(Tot_Drug_Cst, '0') AS REAL)), 2) as total_drug_cost
FROM medicare_part_d_2023 
WHERE Gnrc_Name IN ('Dupilumab', 'Tralokinumab-Ldrm')
  AND Tot_Clms IS NOT NULL 
  AND Tot_Clms != ''
GROUP BY drug_name, generic_name
ORDER BY total_claims DESC;