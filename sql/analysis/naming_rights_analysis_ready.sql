-- Part 1's final layer: the comparable sample the valuation will stand on.
-- Materialized (not a view) -- this is a frozen analysis input, not something
-- that should silently reflow if clean.naming_rights_normalized changes
-- underneath it; re-run this script deliberately to refresh it.
--
-- Filter (CLAUDE.md section 4/5 -- disclosed-only benchmark, keep estimates
-- out): row_classification = 'OBSERVED' AND a real-2024-USD fee AND a
-- capacity both computed. TARGET rows never belong here -- see
-- sql/analysis/target_venues.sql.
--
-- fee_per_seat_real2024 is the core comparable metric CLAUDE.md section 4
-- segments on (capacity band x league tier x venue type).

CREATE OR REPLACE TABLE `msbai-capstone-at6787.analysis.naming_rights_analysis_ready` AS
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
WHERE row_classification = 'OBSERVED'
  AND annual_fee_usd_real2024 IS NOT NULL
  AND capacity_num IS NOT NULL;
