"""Build Part 1 (Clean), step 1 only: type casts + OBSERVED/ESTIMATE/TARGET
classification on top of raw.naming_rights_raw.

No currency conversion, no CPI/inflation adjustment -- see
sql/clean/naming_rights_clean.sql for what this step does and does not do.

Usage:
    python3 scripts/build_clean_layer.py

Requires the same credentials as scripts/bq_load_raw.py.

Env vars:
    BQ_PROJECT   GCP project id (default: msbai-capstone-at6787)
    BQ_DATASET   dataset name   (default: clean)
    BQ_LOCATION  dataset location (default: US)
"""
import os

from google.cloud import bigquery

PROJECT = os.environ.get("BQ_PROJECT", "msbai-capstone-at6787")
DATASET = os.environ.get("BQ_DATASET", "clean")
LOCATION = os.environ.get("BQ_LOCATION", "US")

VIEWS = [
    "sql/clean/naming_rights_clean.sql",
    "sql/clean/naming_rights_comparable.sql",
]

NUMERIC_COLUMNS = [
    "Annual_Fee_Original",
    "Total_Contract_Value_Original",
    "Capacity",
    "Contract_Start_Year",
    "Contract_End_Year",
    "Contract_Length_years",
]


def main():
    client = bigquery.Client(project=PROJECT)

    dataset_ref = bigquery.Dataset(f"{PROJECT}.{DATASET}")
    dataset_ref.location = LOCATION
    client.create_dataset(dataset_ref, exists_ok=True)
    print(f"Dataset ready: {PROJECT}.{DATASET} ({LOCATION})")

    for sql_path in VIEWS:
        with open(sql_path) as f:
            sql = f.read()
        client.query(sql).result()
        print(f"Applied {sql_path}")

    print("\n=== Row classification counts ===")
    for row in client.query(f"""
        SELECT row_classification, COUNT(*) AS n
        FROM `{PROJECT}.{DATASET}.naming_rights_clean`
        GROUP BY 1 ORDER BY 2 DESC
    """).result():
        print(f"  {row['row_classification']}: {row['n']}")

    print("\n=== OBSERVED rows with non-null numeric fee / capacity ===")
    row = list(client.query(f"""
        SELECT
          COUNTIF(row_classification = 'OBSERVED') AS observed_total,
          COUNTIF(row_classification = 'OBSERVED' AND annual_fee_original_num IS NOT NULL) AS observed_with_fee,
          COUNTIF(row_classification = 'OBSERVED' AND capacity_num IS NOT NULL) AS observed_with_capacity,
          COUNTIF(row_classification = 'OBSERVED' AND annual_fee_original_num IS NOT NULL AND capacity_num IS NOT NULL) AS observed_with_both
        FROM `{PROJECT}.{DATASET}.naming_rights_clean`
    """).result())[0]
    print(f"  OBSERVED total: {row['observed_total']}")
    print(f"  OBSERVED with non-null annual fee: {row['observed_with_fee']}")
    print(f"  OBSERVED with non-null capacity: {row['observed_with_capacity']}")
    print(f"  OBSERVED with both: {row['observed_with_both']}")

    print("\n=== Count in vs count out (no silent row loss) ===")
    raw_count = list(client.query(f"SELECT COUNT(*) AS n FROM `{PROJECT}.raw.naming_rights_raw`").result())[0]["n"]
    clean_count = list(client.query(f"SELECT COUNT(*) AS n FROM `{PROJECT}.{DATASET}.naming_rights_clean`").result())[0]["n"]
    comparable_count = list(client.query(f"SELECT COUNT(*) AS n FROM `{PROJECT}.{DATASET}.naming_rights_comparable`").result())[0]["n"]
    target_count = list(client.query(f"""
        SELECT COUNT(*) AS n FROM `{PROJECT}.{DATASET}.naming_rights_clean` WHERE row_classification = 'TARGET'
    """).result())[0]["n"]
    print(f"  raw.naming_rights_raw:          {raw_count}")
    print(f"  clean.naming_rights_clean:      {clean_count} (match={clean_count == raw_count})")
    print(f"  clean.naming_rights_comparable: {comparable_count} (= clean - TARGET rows [{target_count}], match={comparable_count == clean_count - target_count})")

    print("\n=== Numeric cast failures (non-null raw string that failed SAFE_CAST) ===")
    for col in NUMERIC_COLUMNS:
        if col in ("Contract_Start_Year", "Contract_End_Year"):
            cast_sql = f"SAFE_CAST(SAFE_CAST({col} AS FLOAT64) AS INT64)"
        else:
            cast_sql = f"SAFE_CAST({col} AS FLOAT64)"
        row = list(client.query(f"""
            SELECT COUNT(*) AS non_null, COUNTIF({cast_sql} IS NULL) AS cast_fail
            FROM `{PROJECT}.raw.naming_rights_raw`
            WHERE {col} IS NOT NULL AND TRIM({col}) != ''
        """).result())[0]
        print(f"  {col}: non_null={row['non_null']} cast_fail={row['cast_fail']}")

    unclassified = list(client.query(f"""
        SELECT COUNT(*) AS n FROM `{PROJECT}.{DATASET}.naming_rights_clean` WHERE row_classification = 'UNCLASSIFIED'
    """).result())[0]["n"]
    print(f"\nUNCLASSIFIED rows (should be 0): {unclassified}")


if __name__ == "__main__":
    main()
