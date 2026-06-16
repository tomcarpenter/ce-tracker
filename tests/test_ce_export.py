import unittest
import zipfile
from io import BytesIO
import tempfile
from pathlib import Path

import pandas as pd

from utils.ce_export import build_ce_zip, ce_basename, has_attachment, record_details_text


class CeExportTests(unittest.TestCase):
    def test_ce_basename_uses_date_and_title(self):
        record = pd.Series({"date": "2026-01-02", "title": "PMH-C Course / Basics"})

        self.assertEqual(ce_basename(record), "ce_2026-01-02_PMH-C_Course_Basics")

    def test_zip_includes_details_file_in_event_folder(self):
        records = pd.DataFrame(
            [
                {
                    "id": "1",
                    "date": "2026-01-02",
                    "title": "PMH-C Course / Basics",
                    "hours": 2,
                    "category": "PMH-C",
                    "notes": "Course note",
                    "certificate_path": "",
                    "certificate_hash": "",
                    "created_at": "",
                    "updated_at": "",
                }
            ]
        )

        zip_data, record_count, file_count = build_ce_zip(records, folder_per_record=True)
        names = zipfile.ZipFile(BytesIO(zip_data)).namelist()

        self.assertEqual(record_count, 1)
        self.assertEqual(file_count, 0)
        self.assertEqual(
            names,
            [
                "ce_2026-01-02_PMH-C_Course_Basics/"
                "ce_2026-01-02_PMH-C_Course_Basics.txt"
            ],
        )

    def test_record_details_include_trainer_and_organization(self):
        details = record_details_text(
            pd.Series(
                {
                    "date": "2026-01-02",
                    "title": "PMH-C Course / Basics",
                    "trainer_name": "Alex Morgan",
                    "organization": "Clinical Training Center",
                    "hours": 2,
                    "category": "PMH-C",
                }
            )
        )

        self.assertIn("Trainer name: Alex Morgan", details)
        self.assertIn("Organization: Clinical Training Center", details)

    def test_zip_includes_certificate_file_when_present(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cert_path = Path(tmpdir) / "certificate.pdf"
            cert_path.write_bytes(b"%PDF-1.4 fake")

            records = pd.DataFrame(
                [
                    {
                        "id": "1",
                        "date": "2026-01-02",
                        "title": "PMH-C Course / Basics",
                        "hours": 2,
                        "category": "PMH-C",
                        "notes": "",
                        "certificate_path": str(cert_path),
                        "certificate_hash": "hash",
                        "created_at": "",
                        "updated_at": "",
                    }
                ]
            )

            zip_data, record_count, file_count = build_ce_zip(records, folder_per_record=True)
            names = zipfile.ZipFile(BytesIO(zip_data)).namelist()

            self.assertTrue(has_attachment(str(cert_path)))
            self.assertEqual(record_count, 1)
            self.assertEqual(file_count, 1)
            self.assertIn(
                "ce_2026-01-02_PMH-C_Course_Basics/"
                "ce_2026-01-02_PMH-C_Course_Basics.pdf",
                names,
            )


if __name__ == "__main__":
    unittest.main()
