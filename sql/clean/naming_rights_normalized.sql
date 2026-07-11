-- Currency + inflation normalization (CLAUDE.md section 3 pipeline):
-- raw original value (kept) -> USD at contract-year average FX -> real USD
-- at 2024 price level (US CPI). Built on `clean.naming_rights_clean` (every
-- row, TARGET included) so both `naming_rights_comparable` and the TARGET
-- row can use it; this view does not filter or segment anything -- that is
-- the analysis-ready step's job, not this one.
--
-- Currency -> World Bank entity mapping (decision recorded in CLAUDE.md
-- section 3): USD->USA, JPY->JPN, EUR->Euro area (EMU), GBP->GBR, CAD->CAN,
-- SGD->SGP. The join itself is keyed on the ISO currency code directly
-- (ref.fx_rates.currency), since that's how ref.fx_rates is stored; the
-- mapping below exists to (a) document which World Bank entity backs each
-- currency and (b) flag any currency in the data this list doesn't cover.
--
-- FX = contract START YEAR annual average (ref.fx_rates, World Bank
-- PA.NUS.FCRF). USD rows divide by 1.0 (ref.fx_rates carries an explicit
-- USD=1.0 row per year), so no special-cased branch is needed for USD.
--
-- Inflation = rebase to 2024 (ref.us_cpi, World Bank FP.CPI.TOTL) -- 2024
-- is the latest published actual CPI year, per CLAUDE.md section 3's
-- decision to not project 2025/2026.
--
-- ref.fx_rates / ref.us_cpi cover 2000-2026 (2000-2024 all actual; 2025/2026
-- are actual where World Bank has published, carried-forward from the
-- latest actual year otherwise -- see CLAUDE.md section 1 and
-- scripts/fetch_ref_data.py). Rows with a contract start year outside
-- 2000-2026, or before 2000, still get a NULL normalized fee for that
-- reason, not because anything is broken -- `normalization_null_reason`
-- makes that explicit. `fx_value_basis` / `cpi_start_value_basis` carry the
-- underlying ref row's 'actual' | 'carried_forward' flag through so a
-- normalized fee can always be traced back to whether it relied on a
-- carried-forward year.

CREATE OR REPLACE VIEW `msbai-capstone-at6787.clean.naming_rights_normalized` AS
WITH mapped AS (
  SELECT
    c.*,
    CASE c.Currency
      WHEN 'USD' THEN 'USA'
      WHEN 'JPY' THEN 'JPN'
      WHEN 'EUR' THEN 'EMU'
      WHEN 'GBP' THEN 'GBR'
      WHEN 'CAD' THEN 'CAN'
      WHEN 'SGD' THEN 'SGP'
      ELSE NULL
    END AS currency_wb_entity
  FROM `msbai-capstone-at6787.clean.naming_rights_clean` c
),

joined AS (
  SELECT
    m.*,
    fx.lcu_per_usd AS fx_rate_used,
    fx.value_basis AS fx_value_basis,
    cpi_start.cpi_index AS cpi_contract_start_year,
    cpi_start.value_basis AS cpi_start_value_basis,
    cpi_2024.cpi_index AS cpi_2024_index
  FROM mapped m
  LEFT JOIN `msbai-capstone-at6787.ref.fx_rates` fx
    ON fx.currency = m.Currency AND fx.year = m.contract_start_year_num
  LEFT JOIN `msbai-capstone-at6787.ref.us_cpi` cpi_start
    ON cpi_start.year = m.contract_start_year_num
  LEFT JOIN `msbai-capstone-at6787.ref.us_cpi` cpi_2024
    ON cpi_2024.year = 2024
),

with_usd AS (
  SELECT
    j.*,
    CASE
      WHEN j.annual_fee_original_num IS NULL THEN NULL
      WHEN j.fx_rate_used IS NULL THEN NULL
      ELSE j.annual_fee_original_num / j.fx_rate_used
    END AS annual_fee_usd
  FROM joined j
)

SELECT
  w.*,
  CASE
    WHEN w.annual_fee_usd IS NULL THEN NULL
    WHEN w.cpi_contract_start_year IS NULL OR w.cpi_2024_index IS NULL THEN NULL
    ELSE w.annual_fee_usd * w.cpi_2024_index / w.cpi_contract_start_year
  END AS annual_fee_usd_real2024,

  CASE
    WHEN w.annual_fee_original_num IS NULL THEN 'missing_fee'
    WHEN w.contract_start_year_num IS NULL THEN 'missing_start_year'
    WHEN w.currency_wb_entity IS NULL THEN 'currency_not_supported'
    WHEN w.fx_rate_used IS NULL OR w.cpi_contract_start_year IS NULL OR w.cpi_2024_index IS NULL
      THEN 'year_out_of_ref_range'
    ELSE NULL
  END AS normalization_null_reason
FROM with_usd w;
