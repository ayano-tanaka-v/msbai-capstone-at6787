-- The TARGET case(s) (Chiba Lotte), kept separate from the comparable
-- sample -- this is what Part 2 will price, never something to benchmark
-- against itself. Same column shape as naming_rights_analysis_ready where
-- applicable; fee columns are null by construction (there is no disclosed
-- fee to look up for an unbuilt stadium), which fee_per_seat_real2024
-- inherits automatically since its numerator is null -- no hardcoding needed.

CREATE OR REPLACE TABLE `msbai-capstone-at6787.analysis.target_venues` AS
SELECT
  Record_ID AS record_id,
  Venue_Name AS venue_name,
  Sponsor_Name AS sponsor_name,
  Country AS country,
  City AS city,
  Venue_Type AS venue_type,
  League_Tier_Level AS league_tier_level,
  capacity_num AS capacity,
  contract_start_year_num AS contract_start_year,
  annual_fee_original_num AS annual_fee_original,
  Currency AS currency,
  annual_fee_usd,
  annual_fee_usd_real2024,
  row_classification,
  annual_fee_usd_real2024 / capacity_num AS fee_per_seat_real2024
FROM `msbai-capstone-at6787.clean.naming_rights_normalized`
WHERE row_classification = 'TARGET';
