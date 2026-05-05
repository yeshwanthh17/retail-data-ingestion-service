from __future__ import annotations

import csv
import io
from datetime import date, datetime
from enum import Enum
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple, Type

from django.conf import settings
from django.core.validators import validate_email
from django.core.exceptions import ValidationError as DjangoValidationError

from ingestion.models import City, Country, Region, State, Store, StoreBrand, StoreType, User
from ingestion.utils.normalization import canonical_key, coerce_optional_string, is_valid_phone_number, normalize_lookup_value


LOOKUP_MODELS: Dict[str, Type] = {
    "store_brand": StoreBrand,
    "store_type": StoreType,
    "city": City,
    "state": State,
    "country": Country,
    "region": Region,
}

STORE_FIELD_ALIASES: Dict[str, Sequence[str]] = {
    "store_id": ("store_id", "store code", "store_code"),
    "store_external_id": ("store_external_id", "external_id", "store external id"),
    "name": ("name", "store_name"),
    "title": ("title", "store_title"),
    "store_brand": ("store_brand", "brand", "store brand"),
    "store_type": ("store_type", "type", "store type"),
    "city": ("city",),
    "state": ("state",),
    "country": ("country",),
    "region": ("region",),
    "latitude": ("latitude", "lat"),
    "longitude": ("longitude", "lng", "lon", "long"),
    "is_active": ("is_active", "active"),
}

USER_FIELD_ALIASES: Dict[str, Sequence[str]] = {
    "username": ("username", "user_name"),
    "first_name": ("first_name", "first name"),
    "last_name": ("last_name", "last name"),
    "email": ("email", "email_id"),
    "user_type": ("user_type", "role", "user type"),
    "phone_number": ("phone_number", "phone", "mobile", "mobile_number"),
    "supervisor_username": ("supervisor_username", "supervisor", "manager_username", "reports_to"),
    "supervisor_id": ("supervisor_id", "manager_id"),
    "is_active": ("is_active", "active"),
}

MAPPING_FIELD_ALIASES: Dict[str, Sequence[str]] = {
    "username": ("username", "user_name"),
    "user_id": ("user_id",),
    "store_id": ("store_id", "store code", "store_code"),
    "date": ("date", "visit_date"),
    "is_active": ("is_active", "active"),
}

VALID_USER_TYPES = {1, 2, 3, 7}


class IngestionType(str, Enum):
    STORES = "stores"
    USERS = "users"
    MAPPINGS = "mappings"


class BaseIngestionProcessor:
    failure_policy = "partial_ingestion_skip_invalid_rows"

    def __init__(self):
        self.batch_size = settings.BATCH_SIZE

    def _build_lookup_cache(self) -> Dict[str, Dict[str, int]]:
        cache: Dict[str, Dict[str, int]] = {}
        for field_name, model in LOOKUP_MODELS.items():
            cache[field_name] = {
                canonical_key(name): lookup_id for lookup_id, name in model.objects.values_list("id", "name")
            }
        return cache

    def _get_or_create_lookup_id(self, field_name: str, value: str, lookup_cache: Dict[str, Dict[str, int]]) -> int:
        normalized_value = normalize_lookup_value(value)
        key = canonical_key(normalized_value)
        cached_id = lookup_cache[field_name].get(key)
        if cached_id is not None:
            return cached_id

        model = LOOKUP_MODELS[field_name]
        created = model.objects.create(name=normalized_value)
        lookup_cache[field_name][key] = created.id
        return created.id

    def _load_existing_store_ids(self) -> Set[str]:
        return set(Store.objects.values_list("store_id", flat=True))

    def _load_existing_usernames(self) -> Set[str]:
        return set(User.objects.values_list("username", flat=True))

    def _load_existing_user_ids(self) -> Set[int]:
        return set(User.objects.values_list("id", flat=True))

    def _enumerate_rows(self, upload) -> Iterable[Tuple[int, Dict[str, str]]]:
        upload.file.seek(0)
        text_stream = io.TextIOWrapper(upload.file, encoding="utf-8-sig", newline="")
        try:
            reader = csv.DictReader(text_stream)
            if reader.fieldnames is None:
                raise ValueError("The uploaded CSV file is empty.")
            reader.fieldnames = [field.strip().casefold() if field else "" for field in reader.fieldnames]
            for row_number, row in enumerate(reader, start=2):
                yield row_number, {str(key).strip().casefold(): (value or "") for key, value in row.items()}
        finally:
            text_stream.detach()

    def _required_email(self, row: Dict[str, str], row_number: int, errors: List[dict]) -> str:
        email = self._required_string(row, row_number, "email", USER_FIELD_ALIASES, 254, errors)
        if not email:
            return ""
        try:
            validate_email(email)
            return email
        except DjangoValidationError as exc:
            errors.append(self._error(row_number, "email", exc.messages[0], email))
            return ""

    def _required_string(self, row, row_number, field_name, aliases, max_length, errors) -> str:
        value = coerce_optional_string(self._value(row, aliases[field_name]))
        if not value:
            errors.append(self._error(row_number, field_name, "This field is required."))
            return ""
        if len(value) > max_length:
            errors.append(self._error(row_number, field_name, f"Maximum length is {max_length}.", value))
            return ""
        return value

    def _optional_string(self, row, field_name, aliases, max_length, row_number, errors) -> str:
        value = coerce_optional_string(self._value(row, aliases[field_name]))
        if value and len(value) > max_length:
            errors.append(self._error(row_number, field_name, f"Maximum length is {max_length}.", value))
            return ""
        return value

    def _parse_int(self, row, row_number, field_name, aliases, errors, default=None):
        raw_value = coerce_optional_string(self._value(row, aliases[field_name]))
        if not raw_value:
            return default
        try:
            return int(raw_value)
        except ValueError:
            errors.append(self._error(row_number, field_name, "Expected an integer.", raw_value))
            return default

    def _parse_optional_int(self, row, row_number, field_name, aliases, errors):
        raw_value = coerce_optional_string(self._value(row, aliases[field_name]))
        if not raw_value:
            return None
        try:
            return int(raw_value)
        except ValueError:
            errors.append(self._error(row_number, field_name, "Expected an integer.", raw_value))
            return None

    def _parse_float(self, row, row_number, field_name, aliases, errors, default):
        raw_value = coerce_optional_string(self._value(row, aliases[field_name]))
        if not raw_value:
            return default
        try:
            return float(raw_value)
        except ValueError:
            errors.append(self._error(row_number, field_name, "Expected a numeric value.", raw_value))
            return default

    def _parse_bool(self, row, row_number, field_name, aliases, errors, default):
        raw_value = coerce_optional_string(self._value(row, aliases[field_name]))
        if not raw_value:
            return default
        lowered = raw_value.casefold()
        if lowered in {"true", "1", "yes", "y"}:
            return True
        if lowered in {"false", "0", "no", "n"}:
            return False
        errors.append(self._error(row_number, field_name, "Expected a boolean value.", raw_value))
        return default

    def _parse_date(self, row, row_number, field_name, aliases, errors, default):
        raw_value = coerce_optional_string(self._value(row, aliases[field_name]))
        if not raw_value:
            return default
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y"):
            try:
                return datetime.strptime(raw_value, fmt).date()
            except ValueError:
                continue
        errors.append(self._error(row_number, field_name, "Expected date in YYYY-MM-DD, DD-MM-YYYY, or MM/DD/YYYY.", raw_value))
        return default

    def _build_summary(self, file_type: IngestionType, filename: str, processed_rows: int, successful_rows: int, errors: List[dict], metadata: Dict[str, object]) -> dict:
        failed_row_count = len({error["row_number"] for error in errors})
        return {
            "file_type": file_type.value,
            "filename": filename,
            "processed_rows": processed_rows,
            "successful_rows": successful_rows,
            "failed_rows": failed_row_count,
            "skipped_rows": failed_row_count,
            "failure_policy": self.failure_policy,
            "duration_seconds": 0.0,
            "errors": errors,
            "metadata": metadata,
        }

    @staticmethod
    def _value(row: Dict[str, str], aliases: Sequence[str]) -> str:
        for alias in aliases:
            if alias in row:
                return row[alias]
        return ""

    @staticmethod
    def _error(row_number: int, column: str, reason: str, value: Optional[str] = None) -> dict:
        return {"row_number": row_number, "column": column, "reason": reason, "value": value}
