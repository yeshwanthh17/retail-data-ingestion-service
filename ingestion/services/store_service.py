from typing import Dict, List, Optional

from ingestion.models import Store
from ingestion.services.base import BaseIngestionProcessor, IngestionType, LOOKUP_MODELS, STORE_FIELD_ALIASES


class StoreIngestionProcessor(BaseIngestionProcessor):
    def ingest(self, upload) -> dict:
        errors: List[dict] = []
        processed_rows = 0
        successful_rows = 0
        seen_store_ids = self._load_existing_store_ids()
        lookup_cache = self._build_lookup_cache()
        pending: List[Store] = []

        for row_number, row in self._enumerate_rows(upload):
            processed_rows += 1
            row_errors: List[dict] = []
            store_id = self._required_string(row, row_number, "store_id", STORE_FIELD_ALIASES, 255, row_errors)
            store_external_id = self._optional_string(row, "store_external_id", STORE_FIELD_ALIASES, 255, row_number, row_errors)
            name = self._required_string(row, row_number, "name", STORE_FIELD_ALIASES, 255, row_errors)
            title = self._required_string(row, row_number, "title", STORE_FIELD_ALIASES, 255, row_errors)
            latitude = self._parse_float(row, row_number, "latitude", STORE_FIELD_ALIASES, row_errors, default=0.0)
            longitude = self._parse_float(row, row_number, "longitude", STORE_FIELD_ALIASES, row_errors, default=0.0)
            is_active = self._parse_bool(row, row_number, "is_active", STORE_FIELD_ALIASES, row_errors, default=True)

            if store_id and store_id in seen_store_ids:
                row_errors.append(self._error(row_number, "store_id", "Duplicate store_id in file or database.", store_id))

            lookup_values: Dict[str, str] = {}
            for field_name in LOOKUP_MODELS:
                lookup_values[field_name] = self._optional_string(row, field_name, STORE_FIELD_ALIASES, 255, row_number, row_errors)

            if row_errors:
                errors.extend(row_errors)
                continue

            lookup_ids: Dict[str, Optional[int]] = {}
            for field_name, raw_lookup in lookup_values.items():
                lookup_ids[field_name] = self._get_or_create_lookup_id(field_name, raw_lookup, lookup_cache) if raw_lookup else None

            seen_store_ids.add(store_id)
            pending.append(
                Store(
                    store_id=store_id,
                    store_external_id=store_external_id,
                    name=name,
                    title=title,
                    store_brand_id=lookup_ids["store_brand"],
                    store_type_id=lookup_ids["store_type"],
                    city_id=lookup_ids["city"],
                    state_id=lookup_ids["state"],
                    country_id=lookup_ids["country"],
                    region_id=lookup_ids["region"],
                    latitude=latitude,
                    longitude=longitude,
                    is_active=is_active,
                )
            )

            if len(pending) >= self.batch_size:
                Store.objects.bulk_create(pending, batch_size=self.batch_size)
                successful_rows += len(pending)
                pending = []

        if pending:
            Store.objects.bulk_create(pending, batch_size=self.batch_size)
            successful_rows += len(pending)

        return self._build_summary(
            IngestionType.STORES,
            upload.name,
            processed_rows,
            successful_rows,
            errors,
            {"batch_size": self.batch_size, "strategy": "streaming_validation_and_bulk_create"},
        )
