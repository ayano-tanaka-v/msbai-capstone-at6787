-- Part 1 (Clean), step 1 only: type casts + OBSERVED/ESTIMATE/TARGET
-- classification. No currency conversion, no CPI/inflation adjustment --
-- those are later steps in CLAUDE.md's normalization pipeline.
--
-- All raw STRING columns from raw.naming_rights_raw are passed through
-- unchanged (r.*) so the original, as-loaded values stay auditable. The
-- new columns below are additive: typed numeric versions (suffixed
-- `_num`) of the fields the valuation engine needs, plus a row
-- classification flag.
--
-- Classification logic (decision, recorded in CLAUDE.md section 2):
--   1. TARGET      -- Data_Type_Value_Basis = 'Target valuation case', or
--                     Source_ID prefix SRC-TARGET (the Chiba Lotte case).
--   2. Rows with Data_Type_Value_Basis populated (only SRC-ASIA, ~3% of
--      rows) are classified directly from that field:
--        'Actual disclosed'                       -> OBSERVED
--        'Actual reported but partially disclosed'-> OBSERVED
--        'Media estimate'                         -> ESTIMATE
--        'Minimum asking price'                   -> ESTIMATE (an ask,
--                                                    not a consummated
--                                                    disclosed fee --
--                                                    keeping it out of
--                                                    the disclosed-only
--                                                    benchmark per
--                                                    CLAUDE.md section 5)
--   3. For the ~97% of rows where Data_Type_Value_Basis is NULL
--      (SRC-SBJ, SRC-KROLL), fall back to the Source ID prefix, per
--      CLAUDE.md section 1's source descriptions:
--        SRC-KROLL -> ESTIMATE ("football club estimates ... reference
--                     only, flag separately")
--        SRC-SBJ   -> OBSERVED ("Sports Business Journal directory
--                     extract" -- not labeled an estimate)
--   4. Anything not covered above -> UNCLASSIFIED (should be empty; a
--      non-empty count here means a new Source ID or Data_Type_Value_Basis
--      value appeared that this rule doesn't know about yet).

CREATE OR REPLACE VIEW `msbai-capstone-at6787.clean.naming_rights_clean` AS
SELECT
  r.*,

  REGEXP_EXTRACT(r.Source_ID, r'^(SRC-[A-Z]+)') AS source_id_prefix,

  SAFE_CAST(r.Annual_Fee_Original AS FLOAT64) AS annual_fee_original_num,
  SAFE_CAST(r.Total_Contract_Value_Original AS FLOAT64) AS total_contract_value_original_num,
  SAFE_CAST(r.Capacity AS FLOAT64) AS capacity_num,
  -- Values are stored like '2018.0' (decimal string); BigQuery's string ->
  -- INT64 SAFE_CAST rejects any decimal point and silently returns NULL for
  -- every row, so cast to FLOAT64 first, then to INT64.
  SAFE_CAST(SAFE_CAST(r.Contract_Start_Year AS FLOAT64) AS INT64) AS contract_start_year_num,
  SAFE_CAST(SAFE_CAST(r.Contract_End_Year AS FLOAT64) AS INT64) AS contract_end_year_num,
  SAFE_CAST(r.Contract_Length_years AS FLOAT64) AS contract_length_years_num,

  CASE
    WHEN r.Data_Type_Value_Basis = 'Target valuation case'
      OR REGEXP_EXTRACT(r.Source_ID, r'^(SRC-[A-Z]+)') = 'SRC-TARGET'
      THEN 'TARGET'
    WHEN r.Data_Type_Value_Basis IN ('Actual disclosed', 'Actual reported but partially disclosed')
      THEN 'OBSERVED'
    WHEN r.Data_Type_Value_Basis IN ('Media estimate', 'Minimum asking price')
      THEN 'ESTIMATE'
    WHEN r.Data_Type_Value_Basis IS NULL
      AND REGEXP_EXTRACT(r.Source_ID, r'^(SRC-[A-Z]+)') = 'SRC-KROLL'
      THEN 'ESTIMATE'
    WHEN r.Data_Type_Value_Basis IS NULL
      AND REGEXP_EXTRACT(r.Source_ID, r'^(SRC-[A-Z]+)') = 'SRC-SBJ'
      THEN 'OBSERVED'
    ELSE 'UNCLASSIFIED'
  END AS row_classification

FROM `msbai-capstone-at6787.raw.naming_rights_raw` r;
