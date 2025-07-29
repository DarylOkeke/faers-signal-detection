-- Create normalized adverse event rate analysis combining FAERS and Medicare data
DROP TABLE IF EXISTS normalized_ae_rates_dupixent_adbry;

CREATE TABLE normalized_ae_rates_dupixent_adbry AS
SELECT 
    f.drug_name,
    f.faers_report_count,
    m.total_claims as medicare_claims_2023,
    m.total_30day_fills as medicare_30day_fills_2023,
    m.total_beneficiaries as medicare_beneficiaries_2023,
    m.total_drug_cost as medicare_cost_2023,
    -- Calculate rates per 1,000 claims
    ROUND((CAST(f.faers_report_count AS REAL) / CAST(m.total_claims AS REAL)) * 1000, 2) as ae_reports_per_1000_claims,
    -- Calculate rates per 1,000 beneficiaries  
    ROUND((CAST(f.faers_report_count AS REAL) / CAST(m.total_beneficiaries AS REAL)) * 1000, 2) as ae_reports_per_1000_beneficiaries,
    -- Calculate reporting rate ratio (Dupixent rate / Adbry rate)
    CASE 
        WHEN f.drug_name = 'Dupixent' THEN 'Reference'
        ELSE 'Comparison'
    END as analysis_role
FROM faers_dupixent_adbry_counts f
JOIN medicare_dupixent_adbry_prescriptions m ON f.drug_name = m.drug_name
WHERE f.quarter = 'Total'
ORDER BY f.drug_name;

-- Add a summary comparison row
INSERT INTO normalized_ae_rates_dupixent_adbry
SELECT 
    'Rate Ratio (Dupixent/Adbry)' as drug_name,
    NULL as faers_report_count,
    NULL as medicare_claims_2023,
    NULL as medicare_30day_fills_2023, 
    NULL as medicare_beneficiaries_2023,
    NULL as medicare_cost_2023,
    ROUND(
        (SELECT ae_reports_per_1000_claims FROM normalized_ae_rates_dupixent_adbry WHERE drug_name = 'Dupixent') /
        (SELECT ae_reports_per_1000_claims FROM normalized_ae_rates_dupixent_adbry WHERE drug_name = 'Adbry'), 
        2
    ) as ae_reports_per_1000_claims,
    ROUND(
        (SELECT ae_reports_per_1000_beneficiaries FROM normalized_ae_rates_dupixent_adbry WHERE drug_name = 'Dupixent') /
        (SELECT ae_reports_per_1000_beneficiaries FROM normalized_ae_rates_dupixent_adbry WHERE drug_name = 'Adbry'),
        2  
    ) as ae_reports_per_1000_beneficiaries,
    'Rate Ratio' as analysis_role;
