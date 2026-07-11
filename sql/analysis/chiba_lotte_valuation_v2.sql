-- Part 2 (Analyze), v2: GLOBAL comparable basis, superseding v1's
-- Japan-anchored/regional approach (sql/analysis/chiba_lotte_valuation_v1.sql).
--
-- Decision (change of approach, recorded here and in CLAUDE.md section 4):
-- do NOT discount for Japan's regional market. Japan's naming-rights market
-- is currently below global levels but converging upward, so this values
-- the venue's GLOBAL-STANDARD potential -- what a 33,000-seat modern
-- ballpark commands worldwide -- not what the local Japanese market pays
-- today. Japan rows are therefore treated on the same footing as every
-- other country's rows: NOT down-weighted, NOT excluded, just no longer
-- given comparable priority for being Japanese. Segmentation is by venue
-- type and capacity size only, never by country.
--
-- The ZOZO Marine floor from v1 is kept, but demoted to a sanity check,
-- not a binding constraint -- v2 explicitly expects (and reports on) the
-- global estimate sitting ABOVE it; that gap is the convergence-upside
-- story, not a problem to correct for.

CREATE OR REPLACE VIEW `msbai-capstone-at6787.analysis.chiba_lotte_valuation_v2_tier_rows` AS
SELECT 'Global ballparks (all sizes)' AS valuation_tier, 1 AS tier_order,
  record_id, venue_name, country, capacity, contract_start_year, fee_per_seat_real2024
FROM `msbai-capstone-at6787.analysis.naming_rights_analysis_ready`
WHERE venue_type LIKE '%Ballpark%'

UNION ALL

SELECT 'Global ballparks, 25k-45k capacity band (closest size peers)', 2,
  record_id, venue_name, country, capacity, contract_start_year, fee_per_seat_real2024
FROM `msbai-capstone-at6787.analysis.naming_rights_analysis_ready`
WHERE venue_type LIKE '%Ballpark%' AND capacity BETWEEN 25000 AND 45000;


-- Per-tier fee_per_seat_real2024 distribution (now including p90, since
-- upside can reference it) applied to the target's actual capacity (read
-- live from analysis.target_venues, not hardcoded).

CREATE OR REPLACE VIEW `msbai-capstone-at6787.analysis.chiba_lotte_valuation_v2_summary` AS
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
    APPROX_QUANTILES(fee_per_seat_real2024, 4)[OFFSET(3)] AS p75_fee_per_seat,
    APPROX_QUANTILES(fee_per_seat_real2024, 100)[OFFSET(90)] AS p90_fee_per_seat,
    MAX(fee_per_seat_real2024) AS max_fee_per_seat
  FROM `msbai-capstone-at6787.analysis.chiba_lotte_valuation_v2_tier_rows`
  GROUP BY valuation_tier, tier_order
)
SELECT
  s.*,
  t.target_capacity,
  s.p25_fee_per_seat * t.target_capacity AS implied_fee_p25_usd,
  s.median_fee_per_seat * t.target_capacity AS implied_fee_median_usd,
  s.p75_fee_per_seat * t.target_capacity AS implied_fee_p75_usd,
  s.p90_fee_per_seat * t.target_capacity AS implied_fee_p90_usd
FROM stats s
CROSS JOIN target t
ORDER BY s.tier_order;


-- "Current Japan market" reference column: BOTH OBSERVED and ESTIMATE
-- Japan rows side by side, so the gap between the global estimate above
-- and today's Japan level is visible directly -- that gap is the
-- convergence-upside story this v2 approach is built to surface. Purely
-- descriptive; never fed into the tiers/summary above.

CREATE OR REPLACE VIEW `msbai-capstone-at6787.analysis.chiba_lotte_japan_reference_v2` AS
SELECT
  Record_ID AS record_id,
  Venue_Name AS venue_name,
  Venue_Type AS venue_type,
  row_classification,
  capacity_num AS capacity,
  contract_start_year_num AS contract_start_year,
  annual_fee_original_num AS annual_fee_original,
  Currency AS currency,
  annual_fee_usd_real2024,
  annual_fee_usd_real2024 / capacity_num AS fee_per_seat_real2024,
  normalization_null_reason
FROM `msbai-capstone-at6787.clean.naming_rights_normalized`
WHERE Country = 'Japan' AND row_classification IN ('OBSERVED', 'ESTIMATE');
