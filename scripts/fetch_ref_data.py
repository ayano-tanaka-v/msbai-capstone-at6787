"""Fetch currency FX and US CPI reference data from the World Bank API and
load it into BigQuery, exactly as-is (no joins to the naming-rights fees).

Part 1 (Load) only, for the `ref` dataset -- see CLAUDE.md sections 1 and 3
for how these tables get joined to the fees later; none of that happens here.

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
YEAR_END = 2024

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
]

US_CPI_SCHEMA = [
    bigquery.SchemaField("year", "INT64"),
    bigquery.SchemaField("cpi_index", "FLOAT64"),
]


def fetch_indicator(country, indicator):
    """Fetch one World Bank indicator series for one country/entity code.
    Returns {year: value} for whatever years the API returns non-null values.

    Uses urllib rather than requests/a shared session: this environment's
    egress proxy hangs on a *reused* keep-alive connection for a second
    HTTPS request, but is fine with a fresh connection per call (confirmed
    against both curl and urllib) -- so each call here gets its own."""
    query = urllib.parse.urlencode(
        {"format": "json", "date": f"{YEAR_START}:{YEAR_END}", "per_page": 1000}
    )
    url = f"{WORLD_BANK_API.format(country=country, indicator=indicator)}?{query}"
    with urllib.request.urlopen(url, timeout=30) as resp:
        payload = json.loads(resp.read())
    if not isinstance(payload, list) or len(payload) < 2 or payload[1] is None:
        raise RuntimeError(f"Unexpected World Bank response for {country}/{indicator}: {payload}")

    out = {}
    for row in payload[1]:
        if row["value"] is not None:
            out[int(row["date"])] = float(row["value"])
    return out


def fetch_fx_rows():
    rows = []
    for currency, country in CURRENCY_TO_WB_COUNTRY.items():
        series = fetch_indicator(country, "PA.NUS.FCRF")
        missing = [y for y in range(YEAR_START, YEAR_END + 1) if y not in series]
        if missing:
            raise RuntimeError(f"{currency} ({country}) missing years: {missing}")
        for year in range(YEAR_START, YEAR_END + 1):
            rows.append({"currency": currency, "year": year, "lcu_per_usd": series[year]})
        time.sleep(0.2)  # be polite to the API

    # USD is the base currency: 1 USD per USD in every year, by definition
    # (not fetched -- there is no meaningful PA.NUS.FCRF series for USD/USD).
    for year in range(YEAR_START, YEAR_END + 1):
        rows.append({"currency": "USD", "year": year, "lcu_per_usd": 1.0})

    return rows


def fetch_cpi_rows():
    series = fetch_indicator("USA", "FP.CPI.TOTL")
    rows = []
    for year in range(YEAR_START, YEAR_END + 1):
        if year in series:
            rows.append({"year": year, "cpi_index": series[year]})
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
