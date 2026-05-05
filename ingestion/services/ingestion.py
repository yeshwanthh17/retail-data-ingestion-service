import time

from ingestion.services.base import IngestionType
from ingestion.services.mapping_service import MappingIngestionProcessor
from ingestion.services.store_service import StoreIngestionProcessor
from ingestion.services.user_service import UserIngestionProcessor


class IngestionService:
    def ingest(self, upload, ingestion_type: IngestionType) -> dict:
        started_at = time.perf_counter()
        if ingestion_type == IngestionType.STORES:
            summary = StoreIngestionProcessor().ingest(upload)
        elif ingestion_type == IngestionType.USERS:
            summary = UserIngestionProcessor().ingest(upload)
        elif ingestion_type == IngestionType.MAPPINGS:
            summary = MappingIngestionProcessor().ingest(upload)
        else:
            raise ValueError(f"Unsupported ingestion type: {ingestion_type}")
        summary["duration_seconds"] = round(time.perf_counter() - started_at, 3)
        return summary
