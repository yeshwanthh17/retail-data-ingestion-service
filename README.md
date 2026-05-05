# Data Ingestion Assignment

Django-based backend service for uploading, validating, and ingesting retail master data and store-user mappings into a SQL database.

## Tech stack

- Python 3.10+
- Django 5.2
- Django ORM
- SQLite by default

## Project structure

```text
config/
  settings.py
  urls.py
  wsgi.py
ingestion/
  migrations/
  services/
  utils/
  models.py
  tests.py
  urls.py
  views.py
docs/
  approach.md
scripts/
  benchmark_ingestion.py
manage.py
requirements.txt
```

## Features implemented

- Django upload endpoints for stores, users, and mappings
- Row-level validation with row number, column, reason, and invalid value
- Dynamic lookup-table creation for brand, type, city, state, country, and region
- Whitespace and case normalization before lookup creation
- Partial-ingestion failure policy with explicit error reporting
- Batch processing with `BATCH_SIZE=1000`
- Bulk inserts for large files
- Basic regression tests for critical ingestion cases

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 manage.py migrate
python3 manage.py runserver
```

Optional environment variables:

```env
SQLITE_NAME=data_ingestion.sqlite3
BATCH_SIZE=1000
DJANGO_SECRET_KEY=assignment-secret-key
```

## API endpoints

### Health check

```bash
curl http://127.0.0.1:8000/health
```

### Upload stores

```bash
curl -X POST http://127.0.0.1:8000/upload/stores \
  -F "file=@stores_master.csv"
```

### Upload users

```bash
curl -X POST http://127.0.0.1:8000/upload/users \
  -F "file=@users_master.csv"
```

### Upload mapping

```bash
curl -X POST http://127.0.0.1:8000/upload/mapping \
  -F "file=@store_user_mapping.csv"
```

Recommended upload order:

1. `stores`
2. `users`
3. `mapping`

## Response format

Example response:

```json
{
  "file_type": "stores",
  "filename": "stores_master.csv",
  "processed_rows": 100,
  "successful_rows": 94,
  "failed_rows": 6,
  "skipped_rows": 6,
  "failure_policy": "partial_ingestion_skip_invalid_rows",
  "duration_seconds": 0.268,
  "errors": [
    {
      "row_number": 7,
      "column": "store_id",
      "reason": "Duplicate store_id in file or database.",
      "value": "STR-0004"
    }
  ],
  "metadata": {
    "batch_size": 1000,
    "strategy": "streaming_validation_and_bulk_create"
  }
}
```

## Validation rules

- Required fields are enforced for store IDs, store names, store titles, usernames, emails, and mapping references.
- Field lengths follow the assignment schema.
- `email` is validated with Django validators.
- `phone_number` accepts digits, spaces, dashes, and an optional leading `+`.
- `user_type` must be one of `1`, `2`, `3`, `7`.
- Lookup values are normalized before creation:
  - trim leading and trailing whitespace
  - collapse repeated internal spaces
  - case-insensitive deduplication
- Invalid parent rows do not create lookup-table junk.
- Supervisor references are validated against existing users and valid uploaded users.
- Mapping uploads validate that referenced users and stores already exist.

## Performance

The system processes CSV files in batches (`1000` rows) using bulk inserts to efficiently handle large datasets. Invalid rows are skipped with detailed error reporting.

Benchmark command:

```bash
python3 scripts/benchmark_ingestion.py stores intern_assignment_candidate/data/stores_master_500k.csv --reset-db
```

Local benchmark captured on 2026-05-05 using the provided Django implementation:

- processed rows: `500000`
- successful rows: `492846`
- failed rows: `7154`
- duration: `150.283` seconds
- strategy: `streaming_validation_and_bulk_create`

## Tests

Run the Django test suite:

```bash
python3 manage.py test
```

## Notes

- This submission is Django-only: routing, models, validation flow, tests, and benchmark path all use Django.
- SQLite is the default database for local review.
- The failure policy is partial ingestion: valid rows are inserted, invalid rows are skipped and returned in the error report.
