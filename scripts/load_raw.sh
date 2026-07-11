#!/usr/bin/env bash
# Part 1 (Load) only: create the `raw` BigQuery dataset and load the raw
# naming-rights CSVs exactly as-is -- every column as STRING, no type
# conversion, no cleaning. Requires `gcloud auth login` (or ADC) for a
# principal with BigQuery Data Editor + Job User on the target project.
set -euo pipefail

PROJECT="${BQ_PROJECT:-msbai-capstone-at6787}"
DATASET="${BQ_DATASET:-raw}"
LOCATION="${BQ_LOCATION:-US}"

echo "== Create dataset =="
bq --location="${LOCATION}" mk --dataset --description "Raw naming-rights layer, loaded as-is" \
  "${PROJECT}:${DATASET}" || echo "(dataset may already exist)"

echo "== Load raw.naming_rights_raw =="
bq load --source_format=CSV --skip_leading_rows=1 --replace \
  --schema=scripts/schemas/naming_rights_raw.json \
  "${PROJECT}:${DATASET}.naming_rights_raw" \
  raw/data_input_all.csv

echo "== Load raw.data_dictionary =="
bq load --source_format=CSV --skip_leading_rows=1 --replace \
  --schema=scripts/schemas/data_dictionary.json \
  "${PROJECT}:${DATASET}.data_dictionary" \
  reference/data_dictionary.csv

echo "== Load raw.code_lists =="
bq load --source_format=CSV --skip_leading_rows=1 --replace \
  --schema=scripts/schemas/code_lists.json \
  "${PROJECT}:${DATASET}.code_lists" \
  reference/code_lists.csv

echo "== Load raw.target_cases =="
bq load --source_format=CSV --skip_leading_rows=1 --replace \
  --schema=scripts/schemas/target_cases.json \
  "${PROJECT}:${DATASET}.target_cases" \
  reference/target_cases.csv

echo "== Verify row counts =="
bq query --use_legacy_sql=false \
"SELECT 'naming_rights_raw' AS table_name, COUNT(*) AS row_count FROM \`${PROJECT}.${DATASET}.naming_rights_raw\`
 UNION ALL SELECT 'data_dictionary', COUNT(*) FROM \`${PROJECT}.${DATASET}.data_dictionary\`
 UNION ALL SELECT 'code_lists', COUNT(*) FROM \`${PROJECT}.${DATASET}.code_lists\`
 UNION ALL SELECT 'target_cases', COUNT(*) FROM \`${PROJECT}.${DATASET}.target_cases\`"
