from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from ingestion.models import City, User
from ingestion.services.ingestion import IngestionService
from ingestion.services.base import IngestionType


class IngestionServiceTests(TestCase):
    def make_upload(self, name: str, content: bytes):
        return SimpleUploadedFile(name, content, content_type="text/csv")

    def test_invalid_store_does_not_create_lookup_rows(self):
        content = (
            b"store_id,store_external_id,name,title,store_brand,store_type,city,state,country,region,latitude,longitude\n"
            b"S1,EXT1,Store One,Main Store,Brand A,Type A,Ghost City,TS,India,South,not-a-number,78.4\n"
        )
        summary = IngestionService().ingest(self.make_upload("stores.csv", content), IngestionType.STORES)

        self.assertEqual(summary["successful_rows"], 0)
        self.assertEqual(summary["failed_rows"], 1)
        self.assertEqual(City.objects.filter(name="Ghost City").count(), 0)

    def test_invalid_supervisor_row_blocks_dependent_user(self):
        content = (
            b"username,first_name,last_name,email,user_type,phone_number,supervisor_username,is_active\n"
            b"manager,Lead,User,bad-email,1,+919999999999,,True\n"
            b"worker,John,Doe,worker@example.com,1,+919999999998,manager,True\n"
        )
        summary = IngestionService().ingest(self.make_upload("users.csv", content), IngestionType.USERS)

        self.assertEqual(summary["successful_rows"], 0)
        self.assertEqual(summary["failed_rows"], 2)
        self.assertFalse(User.objects.filter(username="worker").exists())

    def test_provided_assignment_files_ingest_without_crashing(self):
        service = IngestionService()
        files = [
            (IngestionType.STORES, Path("intern_assignment_candidate/data/stores_master.csv")),
            (IngestionType.USERS, Path("intern_assignment_candidate/data/users_master.csv")),
            (IngestionType.MAPPINGS, Path("intern_assignment_candidate/data/store_user_mapping.csv")),
        ]

        results = {}
        for ingestion_type, path in files:
            with path.open("rb") as handle:
                upload = SimpleUploadedFile(path.name, handle.read(), content_type="text/csv")
            results[ingestion_type.value] = service.ingest(upload, ingestion_type)

        self.assertEqual(results["stores"]["processed_rows"], 100)
        self.assertEqual(results["users"]["processed_rows"], 30)
        self.assertEqual(results["mappings"]["processed_rows"], 150)
