"""Fetch country-level GDP and population from the World Bank API and load
it into BigQuery, exactly as-is. Part 1 (Load) only, for the `ref` dataset.

Covers only the countries actually present in the comparable set
(analysis.naming_rights_analysis_ready): United States, Canada, Japan,
Singapore -- no European country appears there (the EUR rows are all
ESTIMATE-classified, never OBSERVED, so they're outside the comparable
set entirely; see CLAUDE.md section 1).

`country` stores the same country-name string
`analysis.naming_rights_analysis_ready.country` uses (e.g. "United
States"), not the World Bank ISO code, so the join in
sql/analysis/chiba_lotte_market_join.sql is a plain equality -- the ISO
code mapping lives only inside this fetch script, the same pattern
fetch_ref_data.py uses for currency -> World Bank entity.

IMPORTANT caveat (documented here and in CLAUDE.md): this is COUNTRY-level
GDP/population -- every US venue gets the same US-national figure
regardless of whether it's in a small college town or New York City. It's
a coarse proxy for market size, not a substitute for metro-level data.
Finer-grained US metro population could be added later (CLAUDE.md section
1 already scopes this as a future, optional step); this fetch intentionally
stops at country-level for now.

Usage:
    python3 scripts/fetch_country_market_data.py

Requires: google-cloud-bigquery
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

# Fetch a small recent window and keep whichever is the latest year with
# BOTH indicators actually published for that country -- don't assume the
# current calendar year is out yet.
YEAR_START = 2020
YEAR_END = 2024

WORLD_BANK_API = "https://api.worldbank.org/v2/country/{country}/indicator/{indicator}"

# Country name (matches analysis.naming_rights_analysis_ready.country) ->
# World Bank ISO3 code. Add here if a new country appears in the
# comparable set (same "record any additions" convention as
# fetch_ref_data.py's currency mapping).
COUNTRY_NAME_TO_WB_CODE = {
    "United States": "USA",
    "Canada": "CAN",
    "Japan": "JPN",
    "Singapore": "SGP",
}

COUNTRY_MARKET_SCHEMA = [
    bigquery.SchemaField("country", "STRING"),
    bigquery.SchemaField("year", "INT64"),
    bigquery.SchemaField("gdp_usd", "FLOAT64"),
    bigquery.SchemaField("population", "INT64"),
]


def fetch_indicator(wb_code, indicator, attempts=3):
    """Fetch one World Bank indicator series for one ISO3 code.
    Returns {year: value}. Uses urllib (fresh connection per call) and
    retries -- same proxy behavior documented in fetch_ref_data.py."""
    query = urllib.parse.urlencode(
        {"format": "json", "date": f"{YEAR_START}:{YEAR_END}", "per_page": 100}
    )
    url = f"{WORLD_BANK_API.format(country=wb_code, indicator=indicator)}?{query}"

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
                    f"Failed to fetch {wb_code}/{indicator} after {attempts} attempts"
                ) from last_error
            time.sleep(3 * attempt)

    if not isinstance(payload, list) or len(payload) < 2 or payload[1] is None:
        raise RuntimeError(f"Unexpected World Bank response for {wb_code}/{indicator}: {payload}")

    return {int(row["date"]): float(row["value"]) for row in payload[1] if row["value"] is not None}


def fetch_country_market_rows():
    rows = []
    for country_name, wb_code in COUNTRY_NAME_TO_WB_CODE.items():
        gdp_series = fetch_indicator(wb_code, "NY.GDP.MKTP.CD")
        pop_series = fetch_indicator(wb_code, "SP.POP.TOTL")

        # Latest year with BOTH indicators actually published.
        common_years = set(gdp_series) & set(pop_series)
        if not common_years:
            raise RuntimeError(f"{country_name} ({wb_code}): no year has both GDP and population")
        latest_year = max(common_years)

        rows.append(
            {
                "country": country_name,
                "year": latest_year,
                "gdp_usd": gdp_series[latest_year],
                "population": int(round(pop_series[latest_year])),
            }
        )
        time.sleep(0.2)  # be polite to the API
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

    rows = fetch_country_market_rows()
    for r in rows:
        print(r)
    load_rows(client, "country_market", COUNTRY_MARKET_SCHEMA, rows)


if __name__ == "__main__":
    main()
