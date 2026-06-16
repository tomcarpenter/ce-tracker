import tempfile
import unittest
from datetime import date
from pathlib import Path
import json

from utils.storage import Storage


class StorageBackupTests(unittest.TestCase):
    def test_initialize_creates_empty_backup_structure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            storage = Storage(data_dir=str(root / "data"), backup_dir=str(root / "backup"))
            storage.initialize()

            backup_root = root / "backup"
            self.assertTrue((backup_root / "ce_records.parquet").exists())
            self.assertTrue((backup_root / "ce_records.csv").exists())
            self.assertTrue((backup_root / "events").is_dir())

    def test_backup_includes_settings_file_when_present(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            data_dir = root / "data"
            backup_dir = root / "backup"
            data_dir.mkdir()
            settings = {
                "lmhc_start": "2025-08-01",
                "data_backup_path": str(backup_dir),
            }
            (data_dir / "settings.json").write_text(json.dumps(settings))

            storage = Storage(data_dir=str(data_dir), backup_dir=str(backup_dir))
            storage.initialize()

            backed_up_settings = backup_dir / "settings.json"
            self.assertTrue(backed_up_settings.exists())
            self.assertEqual(json.loads(backed_up_settings.read_text()), settings)

    def test_configured_backup_dir_is_read_from_selected_data_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            data_dir = root / "custom-data"
            backup_dir = root / "custom-backup"
            data_dir.mkdir()
            (data_dir / "settings.json").write_text(
                json.dumps({"data_backup_path": str(backup_dir)})
            )

            storage = Storage(data_dir=str(data_dir))

            self.assertEqual(storage.backup_dir, backup_dir)

    def test_backup_contains_parquet_and_event_folder_after_write(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            storage = Storage(data_dir=str(root / "data"), backup_dir=str(root / "backup"))
            storage.initialize()

            storage.write_record(
                {
                    "id": "1",
                    "date": date(2026, 1, 2),
                    "title": "Test Course",
                    "is_pmhc": 1,
                    "hours": 2,
                    "notes": "hello",
                    "certificate_path": "",
                    "certificate_hash": "",
                    "created_at": "now",
                    "updated_at": "now",
                }
            )

            backup_root = root / "backup"
            self.assertTrue((backup_root / "ce_records.parquet").exists())
            self.assertTrue((backup_root / "ce_records.csv").exists())
            self.assertTrue(
                (
                    backup_root
                    / "events"
                    / "ce_2026-01-02_Test_Course"
                    / "ce_2026-01-02_Test_Course.txt"
                ).exists()
            )

    def test_certificate_manager_uses_selected_data_and_backup_dirs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            storage = Storage(data_dir=str(root / "data"), backup_dir=str(root / "backup"))
            cert_mgr = storage.certificate_manager()

            cert_uuid = cert_mgr.store_certificate(
                file_data=b"certificate",
                original_filename="course.pdf",
                file_hash="hash",
                record_id="1",
            )

            stored_name = f"{cert_uuid}.pdf"
            self.assertTrue((root / "data" / "certificates" / "root" / stored_name).exists())
            self.assertTrue((root / "data" / "certificates" / "metadata" / f"{cert_uuid}.json").exists())
            self.assertTrue((root / "backup" / "certificates" / "root" / stored_name).exists())
            self.assertTrue((root / "backup" / "certificates" / "metadata" / f"{cert_uuid}.json").exists())

            self.assertEqual(
                storage.resolve_certificate_path(stored_name),
                root / "data" / "certificates" / "root" / stored_name,
            )

    def test_write_update_and_delete_keep_backup_current(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            storage = Storage(data_dir=str(root / "data"), backup_dir=str(root / "backup"))
            storage.initialize()

            record = {
                "id": "1",
                "date": date(2026, 1, 2),
                "title": "Original Course",
                "is_pmhc": 1,
                "hours": 2,
                "notes": "hello",
                "certificate_path": "",
                "certificate_hash": "",
                "created_at": "now",
                "updated_at": "now",
            }

            self.assertTrue(storage.write_record(record))
            record["title"] = "Updated Course"
            self.assertTrue(storage.write_record(record))

            backup_root = root / "backup"
            self.assertFalse(
                (backup_root / "events" / "ce_2026-01-02_Original_Course").exists()
            )
            self.assertTrue(
                (
                    backup_root
                    / "events"
                    / "ce_2026-01-02_Updated_Course"
                    / "ce_2026-01-02_Updated_Course.txt"
                ).exists()
            )

            self.assertTrue(storage.delete_record("1"))
            self.assertEqual(len(storage.load_backup()), 0)
            self.assertEqual(len(list((backup_root / "events").iterdir())), 0)

    def test_legacy_category_is_normalized_to_flags(self):
        normalized = Storage._normalize_record(
            {"id": "1", "category": "LMHC General, PMH-C", "hours": 2}
        )

        self.assertEqual(normalized["is_lmhc_general"], 1)
        self.assertEqual(normalized["is_pmhc"], 1)
        self.assertEqual(normalized["category"], "LMHC General, PMH-C")
        self.assertEqual(normalized["trainer_name"], "")
        self.assertEqual(normalized["organization"], "")

    def test_record_normalization_preserves_trainer_and_organization(self):
        normalized = Storage._normalize_record(
            {
                "id": "1",
                "title": "Course",
                "trainer_name": "Alex Morgan",
                "organization": "Clinical Training Center",
                "is_pmhc": 1,
            }
        )

        self.assertEqual(normalized["trainer_name"], "Alex Morgan")
        self.assertEqual(normalized["organization"], "Clinical Training Center")


if __name__ == "__main__":
    unittest.main()
