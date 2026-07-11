"""Fetch currency FX and US CPI reference data from the World Bank API and
load it into BigQuery, exactly as-is (no joins to the naming-rights fees).

Part 1 (Load) only, for the `ref` dataset -- see CLAUDE.md sections 1 and 3
for how these tables get joined to the fees later; none of that happens here.

Covers 2000-2026. 2000-2024 is fully actual, published data. 2025/2026 use
whatever World Bank has actually published (many series got a 2025 point
during this run) and carry the most recent actual value forward for
whatever that series hasn't published yet -- every row's `value_basis`
column says 'actual' or 'carried_forward' so this is never silently
mistaken for real, newly-observed data. See CLAUDE.md section 1 for the
reasoning (this recovers real, already-collected disclosed contracts whose
start year fell in this gap -- not a new data source).

Usage:
    python3 scripts/fetch_ref_data.py

Requires application-default credentials for a principal with BigQuery
Data Editor + Job User on the target project, e.g.:
    gcloud auth application-default login
    pip install google-cloud-bigquery requests

Env vars:
    BQ_PROJECT   GCP project id (default: msbai-capstone-at6787)
    BQ_DATASET   dataset name   (default: ref)
    BQ_LOCATION  dataset location (default: US)
"""
import json
import os
import time
import urllib.parse
import urllib.request

from google.cloud import bigquery

PROJECT = os.environ.get("BQ_PROJECT", "msbai-capstone-at6787")
DATASET = os.environ.get("BQ_DATASET", "ref")
LOCATION = os.environ.get("BQ_LOCATION", "US")

YEAR_START = 2000
YEAR_END = 2026
# Years through this one were verified fully populated (no gaps) when the
# ref tables were first built covering 2000-2024 -- if any of THOSE years
# ever comes back needing a carried-forward value, that's a real data
# problem, not an expected "not published yet" gap, and should fail loudly
# rather than be silently carried forward like a genuine future-year gap.
PRIOR_VERIFIED_COMPLETE_YEAR = 2024

WORLD_BANK_API = "https://api.worldbank.org/v2/country/{country}/indicator/{indicator}"

# Currency -> World Bank country/entity code for PA.NUS.FCRF (LCU per US$).
# EUR uses the "Euro area" aggregate (entity code EMU, World Bank internal id
# XC) rather than a single member country: it is the entity the euro itself
# is defined against, its PA.NUS.FCRF series is fully populated 2000-2024,
# and its values are identical to any individual euro-area member's (e.g.
# France, Germany) for the years both have data -- so there's no accuracy
# trade-off, and it avoids arbitrarily privileging one member country's
# national identity as "the" euro.
CURRENCY_TO_WB_COUNTRY = {
    "JPY": "JPN",
    "EUR": "EMU",
    "GBP": "GBR",
    "CAD": "CAN",
    "SGD": "SGP",
}

FX_RATES_SCHEMA = [
    bigquery.SchemaField("currency", "STRING"),
    bigquery.SchemaField("year", "INT64"),
    bigquery.SchemaField("lcu_per_usd", "FLOAT64"),
    bigquery.SchemaField("value_basis", "STRING"),
]

US_CPI_SCHEMA = [
    bigquery.SchemaField("year", "INT64"),
    bigquery.SchemaField("cpi_index", "FLOAT64"),
    bigquery.SchemaField("value_basis", "STRING"),
]


def fetch_indicator(country, indicator, attempts=3):
    """Fetch one World Bank indicator series for one country/entity code.
    Returns {year: value} for whatever years the API returns non-null values
    (2025/2026 are frequently not published yet -- that's expected, not an
    error; see build_series_with_basis).

    Uses urllib rather than requests/a shared session: this environment's
    egress proxy hangs on a *reused* keep-alive connection for a second
    HTTPS request, but is fine with a fresh connection per call (confirmed
    against both curl and urllib) -- so each call here gets its own. The
    proxy is also occasionally slow (~30s) on an otherwise-fine request, so
    this retries a couple of times before giving up."""
    query = urllib.parse.urlencode(
        {"format": "json", "date": f"{YEAR_START}:{YEAR_END}", "per_page": 1000}
    )
    url = f"{WORLD_BANK_API.format(country=country, indicator=indicator)}?{query}"

    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(url, timeout=45) as resp:
                payload = json.loads(resp.read())
            break
        except Exception as e:  # noqa: BLE001 -- retry any transient network error
            last_error = e
            if attempt == attempts:
                raise RuntimeError(
                    f"Failed to fetch {country}/{indicator} after {attempts} attempts"
                ) from last_error
            time.sleep(3 * attempt)

    if not isinstance(payload, list) or len(payload) < 2 or payload[1] is None:
        raise RuntimeError(f"Unexpected World Bank response for {country}/{indicator}: {payload}")

    out = {}
    for row in payload[1]:
        if row["value"] is not None:
            out[int(row["date"])] = float(row["value"])
    return out


def build_series_with_basis(actual_series, label):
    """Fill YEAR_START..YEAR_END from an {year: value} dict of *actual*
    published values, carrying the most recent actual value forward into
    any year the API hasn't published yet. Returns [(year, value, basis)].

    Raises if a year at or before PRIOR_VERIFIED_COMPLETE_YEAR would need
    carrying forward -- that range was previously confirmed gap-free, so a
    gap reappearing there is a real data problem, not an expected
    not-yet-published future year."""
    rows = []
    last_actual_value = None
    for year in range(YEAR_START, YEAR_END + 1):
        if year in actual_series:
            last_actual_value = actual_series[year]
            rows.append((year, last_actual_value, "actual"))
        else:
            if last_actual_value is None:
                raise RuntimeError(f"{label}: no actual value at or before {year} to carry forward")
            if year <= PRIOR_VERIFIED_COMPLETE_YEAR:
                raise RuntimeError(
                    f"{label}: year {year} is missing but <= {PRIOR_VERIFIED_COMPLETE_YEAR}, "
                    "which was previously verified complete -- this is an unexpected gap, "
                    "not an unpublished future year"
                )
            rows.append((year, last_actual_value, "carried_forward"))
    return rows


def fetch_fx_rows():
    rows = []
    for currency, country in CURRENCY_TO_WB_COUNTRY.items():
        actual_series = fetch_indicator(country, "PA.NUS.FCRF")
        for year, value, basis in build_series_with_basis(actual_series, f"{currency} FX"):
            rows.append({"currency": currency, "year": year, "lcu_per_usd": value, "value_basis": basis})
        time.sleep(0.2)  # be polite to the API

    # USD is the base currency: 1 USD per USD in every year, by definition
    # (not fetched -- there is no meaningful PA.NUS.FCRF series for USD/USD).
    for year in range(YEAR_START, YEAR_END + 1):
        rows.append({"currency": "USD", "year": year, "lcu_per_usd": 1.0, "value_basis": "actual"})

    return rows


def fetch_cpi_rows():
    actual_series = fetch_indicator("USA", "FP.CPI.TOTL")
    rows = []
    for year, value, basis in build_series_with_basis(actual_series, "US CPI"):
        rows.append({"year": year, "cpi_index": value, "value_basis": basis})
    return rows


def load_rows(client, table_name, schema, rows):
    table_id = f"{PROJECT}.{DATASET}.{table_name}"
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )
    job = client.load_table_from_json(rows, table_id, job_config=job_config)
    job.result()

    bq_rows = list(client.query(f"SELECT COUNT(*) AS n FROM `{table_id}`").result())[0]["n"]
    print(f"{table_id}: loaded {len(rows)} rows, bq_rows={bq_rows} match={len(rows) == bq_rows}")
    return bq_rows


def main():
    client = bigquery.Client(project=PROJECT)

    dataset_ref = bigquery.Dataset(f"{PROJECT}.{DATASET}")
    dataset_ref.location = LOCATION
    client.create_dataset(dataset_ref, exists_ok=True)
    print(f"Dataset ready: {PROJECT}.{DATASET} ({LOCATION})")

    fx_rows = fetch_fx_rows()
    load_rows(client, "fx_rates", FX_RATES_SCHEMA, fx_rows)

    cpi_rows = fetch_cpi_rows()
    load_rows(client, "us_cpi", US_CPI_SCHEMA, cpi_rows)


if __name__ == "__main__":
    main()
