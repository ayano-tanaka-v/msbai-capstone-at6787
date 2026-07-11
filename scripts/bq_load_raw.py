"""Load the raw naming-rights CSVs into BigQuery, exactly as-is.

Part 1 (Load) only: every column is loaded as STRING with no type
conversion, no cleaning, no joins. See CLAUDE.md sections 1-3 for what
happens in later (clean/normalize) steps -- none of that happens here.

Usage:
    python3 scripts/bq_load_raw.py

Requires application-default credentials for a principal with BigQuery
Data Editor + Job User on the target project, e.g.:
    gcloud auth application-default login
    pip install google-cloud-bigquery

Env vars:
    BQ_PROJECT   GCP project id (default: msbai-capstone-at6787)
    BQ_DATASET   dataset name   (default: raw)
    BQ_LOCATION  dataset location (default: US)
"""
import csv
import os
import re

from google.cloud import bigquery

PROJECT = os.environ.get("BQ_PROJECT", "msbai-capstone-at6787")
DATASET = os.environ.get("BQ_DATASET", "raw")
LOCATION = os.environ.get("BQ_LOCATION", "US")

# (source csv, target table name)
TABLES = [
    ("raw/data_input_all.csv", "naming_rights_raw"),
    ("reference/data_dictionary.csv", "data_dictionary"),
    ("reference/code_lists.csv", "code_lists"),
    ("reference/target_cases.csv", "target_cases"),
]


def sanitize(name):
    """BigQuery column names can't contain spaces or slashes; original
    header text is preserved verbatim in the CSV's first row and in
    reference/data_dictionary.csv, so no meaning is lost."""
    s = re.sub(r"[^0-9a-zA-Z_]+", "_", name.strip())
    s = re.sub(r"_+", "_", s).strip("_")
    if re.match(r"^[0-9]", s):
        s = "_" + s
    return s


def load_table(client, csv_path, table_name):
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        header = next(csv.reader(f))

    schema = [bigquery.SchemaField(sanitize(h), "STRING") for h in header]
    table_id = f"{PROJECT}.{DATASET}.{table_name}"

    job_config = bigquery.LoadJobConfig(
        schema=schema,
        skip_leading_rows=1,
        source_format=bigquery.SourceFormat.CSV,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        autodetect=False,
    )

    with open(csv_path, "rb") as f:
        job = client.load_table_from_file(f, table_id, job_config=job_config)
    job.result()

    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        csv_rows = sum(1 for _ in csv.reader(f)) - 1  # minus header

    bq_rows = list(client.query(f"SELECT COUNT(*) AS n FROM `{table_id}`").result())[0]["n"]

    print(f"{table_id}: csv_rows={csv_rows} bq_rows={bq_rows} match={csv_rows == bq_rows}")
    return csv_rows, bq_rows


def main():
    client = bigquery.Client(project=PROJECT)

    dataset_ref = bigquery.Dataset(f"{PROJECT}.{DATASET}")
    dataset_ref.location = LOCATION
    client.create_dataset(dataset_ref, exists_ok=True)
    print(f"Dataset ready: {PROJECT}.{DATASET} ({LOCATION})")

    results = []
    for csv_path, table_name in TABLES:
        results.append((table_name,) + load_table(client, csv_path, table_name))

    print("\nSummary:")
    for table_name, csv_rows, bq_rows in results:
        status = "OK" if csv_rows == bq_rows else "MISMATCH"
        print(f"  {table_name}: {csv_rows} -> {bq_rows} [{status}]")


if __name__ == "__main__":
    main()
