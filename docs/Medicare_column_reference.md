# Medicare Part D Column Reference (2023)

| Column Name              | Meaning                                                                      |
|--------------------------|------------------------------------------------------------------------------|
| Prscrbr_NPI             | National Provider Identifier (NPI) - unique identifier for the prescriber   |
| Prscrbr_Last_Org_Name   | Prescriber's last name or organization name                                  |
| Prscrbr_First_Name      | Prescriber's first name                                                      |
| Prscrbr_City            | City where the prescriber practices                                          |
| Prscrbr_State_Abrvtn    | State abbreviation where the prescriber practices                            |
| Prscrbr_State_FIPS      | FIPS code for the state where the prescriber practices                       |
| Prscrbr_Type            | Type of prescriber (e.g., Internal Medicine, Family Practice, etc.)         |
| Prscrbr_Type_Src        | Source of prescriber type classification                                     |
| Brnd_Name               | Brand name of the drug as marketed                                           |
| Gnrc_Name               | Generic name of the drug                                                     |
| Tot_Clms                | Total number of claims for this drug by this prescriber                     |
| Tot_30day_Fills         | Total number of 30-day equivalent fills                                     |
| Tot_Day_Suply           | Total day supply of the drug prescribed                                      |
| Tot_Drug_Cst            | Total drug cost for all claims                                              |
| Tot_Benes               | Total number of unique beneficiaries who received this drug                 |
| GE65_Sprsn_Flag         | Suppression flag for beneficiaries 65 years and older data                  |
| GE65_Tot_Clms           | Total claims for beneficiaries 65 years and older                           |
| GE65_Tot_30day_Fills    | Total 30-day equivalent fills for beneficiaries 65 years and older         |
| GE65_Tot_Drug_Cst       | Total drug cost for beneficiaries 65 years and older                        |
| GE65_Tot_Day_Suply      | Total day supply for beneficiaries 65 years and older                       |
| GE65_Bene_Sprsn_Flag    | Suppression flag for 65+ beneficiaries count                                |
| GE65_Tot_Benes          | Total number of unique beneficiaries 65 years and older                     |

## Data Notes

- **Data Source**: Medicare Part D Prescriber Public Use File (PUF) for Calendar Year 2023
- **Suppression**: Data is suppressed when fewer than 11 beneficiaries are included (marked with flags)
- **Geographic Coverage**: Includes prescribers practicing in all 50 states, District of Columbia, and U.S. territories
- **Drug Classification**: Both brand and generic names are provided for comprehensive drug identification
- **Age Stratification**: Separate metrics for beneficiaries 65 years and older allow for age-specific analysis
- **Cost Data**: Represents total allowed charges for Medicare Part D covered drugs
- **Claims vs Fills**: Claims represent individual prescription events, while fills are standardized to 30-day equivalents

