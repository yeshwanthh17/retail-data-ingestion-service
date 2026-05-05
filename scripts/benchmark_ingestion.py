import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

import django
from django.core.management import call_command


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.conf import settings

from ingestion.services.base import IngestionType
from ingestion.services.ingestion import IngestionService


@dataclass
class LocalUpload:
    name: str
    file: object


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ingestion benchmark against a local CSV file.")
    parser.add_argument("file_type", choices=[item.value for item in IngestionType], help="Upload category to run.")
    parser.add_argument("file_path", help="Path to the CSV file.")
    parser.add_argument("--reset-db", action="store_true", help="Delete the local SQLite file and rebuild schema before running.")
    parser.add_argument("--max-errors", type=int, default=20, help="How many row errors to include in the printed JSON.")
    args = parser.parse_args()

    file_path = Path(args.file_path).resolve()
    if not file_path.exists():
        raise SystemExit(f"File not found: {file_path}")

    db_path = Path(settings.DATABASES["default"]["NAME"])
    if args.reset_db:
        db_path.unlink(missing_ok=True)

    call_command("migrate", run_syncdb=True, verbosity=0)

    with file_path.open("rb") as handle:
        upload = LocalUpload(file_path.name, handle)
        payload = IngestionService().ingest(upload, IngestionType(args.file_type))

    total_errors = len(payload["errors"])
    payload["errors"] = payload["errors"][: max(args.max_errors, 0)]
    payload["metadata"]["returned_error_count"] = len(payload["errors"])
    payload["metadata"]["truncated_error_count"] = max(total_errors - len(payload["errors"]), 0)
    print(json.dumps(payload, indent=2, default=str))


if __name__ == "__main__":
    main()
