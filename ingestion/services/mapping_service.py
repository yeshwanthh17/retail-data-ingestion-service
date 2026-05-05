from typing import List, Optional, Set, Tuple

from ingestion.models import PermanentJourneyPlan, Store, User
from ingestion.services.base import BaseIngestionProcessor, IngestionType, MAPPING_FIELD_ALIASES


class MappingIngestionProcessor(BaseIngestionProcessor):
    def ingest(self, upload) -> dict:
        errors: List[dict] = []
        processed_rows = 0
        successful_rows = 0
        username_to_id = {username: user_id for user_id, username in User.objects.values_list("id", "username")}
        known_user_ids = set(username_to_id.values())
        store_code_to_id = {store_id: db_id for db_id, store_id in Store.objects.values_list("id", "store_id")}
        existing_mappings = set(PermanentJourneyPlan.objects.values_list("user_id", "store_id", "date"))
        seen_mappings: Set[Tuple[int, int, Optional[object]]] = set()
        pending: List[PermanentJourneyPlan] = []

        for row_number, row in self._enumerate_rows(upload):
            processed_rows += 1
            row_errors: List[dict] = []
            username = self._optional_string(row, "username", MAPPING_FIELD_ALIASES, 150, row_number, row_errors)
            user_id = self._parse_optional_int(row, row_number, "user_id", MAPPING_FIELD_ALIASES, row_errors)
            store_code = self._required_string(row, row_number, "store_id", MAPPING_FIELD_ALIASES, 255, row_errors)
            plan_date = self._parse_date(row, row_number, "date", MAPPING_FIELD_ALIASES, row_errors, default=None)
            is_active = self._parse_bool(row, row_number, "is_active", MAPPING_FIELD_ALIASES, row_errors, default=True)

            resolved_user_id = user_id
            if username:
                resolved_user_id = username_to_id.get(username)
                if resolved_user_id is None:
                    row_errors.append(self._error(row_number, "username", "Unknown username reference.", username))
            elif user_id is None:
                row_errors.append(self._error(row_number, "username", "Either username or user_id is required."))
            elif user_id not in known_user_ids:
                row_errors.append(self._error(row_number, "user_id", "Unknown user_id reference.", str(user_id)))

            resolved_store_id = store_code_to_id.get(store_code)
            if resolved_store_id is None and store_code:
                row_errors.append(self._error(row_number, "store_id", "Unknown store_id reference.", store_code))

            if resolved_user_id is not None and resolved_store_id is not None:
                dedupe_key = (resolved_user_id, resolved_store_id, plan_date)
                if dedupe_key in existing_mappings or dedupe_key in seen_mappings:
                    row_errors.append(self._error(row_number, "store_id", "Duplicate mapping for user_id, store_id, and date.", store_code))
                else:
                    seen_mappings.add(dedupe_key)

            if row_errors:
                errors.extend(row_errors)
                continue

            pending.append(
                PermanentJourneyPlan(
                    user_id=resolved_user_id,
                    store_id=resolved_store_id,
                    date=plan_date,
                    is_active=is_active,
                )
            )
            if len(pending) >= self.batch_size:
                PermanentJourneyPlan.objects.bulk_create(pending, batch_size=self.batch_size)
                successful_rows += len(pending)
                pending = []

        if pending:
            PermanentJourneyPlan.objects.bulk_create(pending, batch_size=self.batch_size)
            successful_rows += len(pending)

        return self._build_summary(
            IngestionType.MAPPINGS,
            upload.name,
            processed_rows,
            successful_rows,
            errors,
            {"batch_size": self.batch_size, "strategy": "reference_validation_and_bulk_create"},
        )
