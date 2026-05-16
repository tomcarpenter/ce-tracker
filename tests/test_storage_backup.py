import tempfile
import unittest
from datetime import date
from pathlib import Path

from utils.storage import Storage


class StorageBackupTests(unittest.TestCase):
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
            self.assertTrue(
                (
                    backup_root
                    / "events"
                    / "ce_2026-01-02_Test_Course"
                    / "ce_2026-01-02_Test_Course.txt"
                ).exists()
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


if __name__ == "__main__":
    unittest.main()
