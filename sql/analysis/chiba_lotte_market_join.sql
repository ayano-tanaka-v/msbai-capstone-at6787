-- Joins country-level market size (ref.country_market: GDP, population,
-- loaded by scripts/fetch_country_market_data.py) onto the comparable
-- set, for the market-adjustment test in
-- scripts/regression_cross_check.py.
--
-- The country-name -> World Bank ISO3 code mapping already happened at
-- ingestion time (scripts/fetch_country_market_data.py's
-- COUNTRY_NAME_TO_WB_CODE) -- ref.country_market.country already stores
-- the same country-name string analysis_ready.country uses, so this join
-- is a plain equality, not a second mapping step.
--
-- IMPORTANT caveat (see CLAUDE.md section 1): this is COUNTRY-level
-- GDP/population -- every US venue gets the same US-national figure
-- regardless of market (a small college town and New York City are
-- identical on this join). It's a coarse proxy, not metro-level data;
-- finer-grained US metro population is a possible future step, not done
-- here.
--
-- LEFT JOIN, not INNER: a country present in analysis_ready but missing
-- from ref.country_market surfaces as gdp_usd/population = NULL here,
-- rather than silently dropping the row -- see the unmatched-country
-- check run alongside this view.

CREATE OR REPLACE VIEW `msbai-capstone-at6787.analysis.naming_rights_analysis_ready_with_market` AS
SELECT
  a.*,
  m.year AS market_data_year,
  m.gdp_usd,
  m.population,
  m.gdp_usd / m.population AS gdp_per_capita_usd
FROM `msbai-capstone-at6787.analysis.naming_rights_analysis_ready` a
LEFT JOIN `msbai-capstone-at6787.ref.country_market` m
  ON m.country = a.country;
