-- Part 2 (Analyze), first pass: a simple ratio (comparables) valuation for
-- the Chiba Lotte Marines new stadium, with NO market-size adjustment yet
-- (that's a later step, per CLAUDE.md section 4's method) and no
-- regression cross-check yet (also later). This is deliberately the
-- simplest defensible pass: fee_per_seat_real2024 x target capacity, by
-- comparable tier.
--
-- Tiers (a row can appear in more than one -- Tier 1 is a subset of Tier 2 --
-- so this is built as three independent UNION ALL branches, not a
-- mutually-exclusive CASE):
--   Tier 1 (tightest): Japan OBSERVED ballparks only (ZOZO Marine, Rakuten
--                      Park) -- CLAUDE.md section 4's first comparable
--                      priority.
--   Tier 2: all Japan OBSERVED comparables (adds large stadiums --
--           Ajinomoto, Panasonic Suita, Yodoko Sakura, Nissan, EDION,
--           Fukuda Denshi, GMO Arena).
--   Tier 3: North American OBSERVED ballparks -- the statistical base
--           (largest n), used as an unadjusted upper reference before
--           market-size adjustment narrows the gap in a later pass.
-- No ESTIMATE or TARGET rows in any tier -- analysis.naming_rights_analysis_ready
-- already excludes them (and the sub-$10k floor outlier).

CREATE OR REPLACE VIEW `msbai-capstone-at6787.analysis.chiba_lotte_valuation_tier_rows` AS
SELECT 'Tier 1: Japan ballparks (tightest)' AS valuation_tier, 1 AS tier_order,
  record_id, venue_name, venue_type, capacity, contract_start_year, fee_per_seat_real2024
FROM `msbai-capstone-at6787.analysis.naming_rights_analysis_ready`
WHERE country = 'Japan' AND venue_type LIKE '%Ballpark%'

UNION ALL

SELECT 'Tier 2: Japan comparables (all)', 2,
  record_id, venue_name, venue_type, capacity, contract_start_year, fee_per_seat_real2024
FROM `msbai-capstone-at6787.analysis.naming_rights_analysis_ready`
WHERE country = 'Japan'

UNION ALL

SELECT 'Tier 3: North American ballparks', 3,
  record_id, venue_name, venue_type, capacity, contract_start_year, fee_per_seat_real2024
FROM `msbai-capstone-at6787.analysis.naming_rights_analysis_ready`
WHERE country IN ('United States', 'Canada') AND venue_type LIKE '%Ballpark%';


-- Per-tier distribution of fee_per_seat_real2024, and that distribution
-- applied to the target's actual capacity (33,000 -- read from
-- analysis.target_venues, not hardcoded, so this stays correct if the
-- target case is ever revised).
--
-- Note on Tier 1 (n=2): APPROX_QUANTILES on 2 points returns p25 = min and
-- median = min (BigQuery's boundary-index approximation isn't meaningful
-- below ~4-5 points) -- it is NOT a bug, just a reminder that "percentile"
-- language oversells the precision available from 2 comparables. avg_fee_per_seat
-- (plain mean) is included alongside the percentile columns specifically so
-- Tier 1 has an honest single-number summary; VALUATION.md uses the mean
-- for Tier 1, not its (misleading) median column.

CREATE OR REPLACE VIEW `msbai-capstone-at6787.analysis.chiba_lotte_valuation_summary` AS
WITH target AS (
  SELECT capacity AS target_capacity
  FROM `msbai-capstone-at6787.analysis.target_venues`
  WHERE record_id = 'TARGET-CHIBA-LOTTE-2034'
),
stats AS (
  SELECT
    valuation_tier,
    tier_order,
    COUNT(*) AS n_comparables,
    MIN(fee_per_seat_real2024) AS min_fee_per_seat,
    APPROX_QUANTILES(fee_per_seat_real2024, 4)[OFFSET(1)] AS p25_fee_per_seat,
    APPROX_QUANTILES(fee_per_seat_real2024, 2)[OFFSET(1)] AS median_fee_per_seat,
    AVG(fee_per_seat_real2024) AS avg_fee_per_seat,
    APPROX_QUANTILES(fee_per_seat_real2024, 4)[OFFSET(3)] AS p75_fee_per_seat,
    MAX(fee_per_seat_real2024) AS max_fee_per_seat
  FROM `msbai-capstone-at6787.analysis.chiba_lotte_valuation_tier_rows`
  GROUP BY valuation_tier, tier_order
)
SELECT
  s.*,
  t.target_capacity,
  s.p25_fee_per_seat * t.target_capacity AS implied_fee_p25_usd,
  s.median_fee_per_seat * t.target_capacity AS implied_fee_median_usd,
  s.avg_fee_per_seat * t.target_capacity AS implied_fee_avg_usd,
  s.p75_fee_per_seat * t.target_capacity AS implied_fee_p75_usd
FROM stats s
CROSS JOIN target t
ORDER BY s.tier_order;


-- Japanese ESTIMATE rows: NOT part of the comparable set (row_classification
-- = 'ESTIMATE', kept out of the disclosed-only benchmark per CLAUDE.md
-- section 2/5) -- shown purely as a side-by-side sanity/triangulation
-- reference, computed the same way (fee_per_seat_real2024) so it's
-- comparable in kind, but never fed into chiba_lotte_valuation_summary.

CREATE OR REPLACE VIEW `msbai-capstone-at6787.analysis.chiba_lotte_japan_estimates_reference` AS
SELECT
  Record_ID AS record_id,
  Venue_Name AS venue_name,
  Venue_Type AS venue_type,
  capacity_num AS capacity,
  contract_start_year_num AS contract_start_year,
  annual_fee_original_num AS annual_fee_original,
  Currency AS currency,
  annual_fee_usd_real2024,
  annual_fee_usd_real2024 / capacity_num AS fee_per_seat_real2024,
  normalization_null_reason
FROM `msbai-capstone-at6787.clean.naming_rights_normalized`
WHERE Country = 'Japan' AND row_classification = 'ESTIMATE';
