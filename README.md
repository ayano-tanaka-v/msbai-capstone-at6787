# msbai-capstone-at6787
Capstone data product: naming-rights benchmark pipeline in BigQuery with a Streamlit valuation dashboard.

## Live dashboard

**https://naming-rights-dashboard-dyskbb5rka-an.a.run.app**

Public, no-login Cloud Run service (`asia-northeast1`), deployed from `dashboard/`. Reads live from the BigQuery
analysis/valuation tables (cached per session, not re-queried on every interaction — see `dashboard/spec.md`).

- **Load time:** ~1.2s on a warm cache (measured locally against the same image before deploy; well under the
  spec's 3s target — see `dashboard/spec.md`'s Verify targets).
- Answers: what fee should Chiba Lotte ask, is it grounded in real comparables, why not just match what Japan
  pays today, and — via the "Price any venue" panel — what would the same engine recommend for any other venue.

## Project layout

| Path | What it is |
|---|---|
| `raw/`, `reference/`, `scripts/`, `sql/clean/` | Part 1: load + clean the naming-rights workbook and public macro data into BigQuery |
| `sql/analysis/`, `scripts/regression_cross_check.py` | Part 2: the analysis-ready comparable table, the valuation (ratio method + regression cross-check), market-size test |
| `analysis/VALUATION.md` | The full written valuation methodology and findings |
| `dashboard/` | Part 3: the Streamlit dashboard (`app.py`), its spec (`spec.md`), and its Cloud Run deploy config |
| `CLAUDE.md` | Project memory — every non-obvious decision, with its reason |
