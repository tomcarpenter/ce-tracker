import unittest
from datetime import datetime

import pandas as pd

from utils.compliance import ComplianceTracker


class FakeStorage:
    def __init__(self, records):
        self.records = pd.DataFrame(records)

    def load_parquet(self):
        return self.records


class ComplianceTests(unittest.TestCase):
    def setUp(self):
        self.tracker = ComplianceTracker(storage=None)

    def test_requirements_match_current_rules(self):
        self.assertEqual(self.tracker.cycles["LMHC"]["hours"], 32)
        self.assertEqual(self.tracker.cycles["Ethics"]["hours"], 6)
        self.assertEqual(self.tracker.cycles["Roles"]["hours"], 2)
        self.assertEqual(self.tracker.cycles["Suicide"]["hours"], 6)
        self.assertEqual(self.tracker.cycles["Equity"]["hours"], 2)
        self.assertEqual(self.tracker.cycles["PMH-C"]["hours"], 12)

    def test_requirements_can_be_configured(self):
        tracker = ComplianceTracker(storage=None, requirements={"PMH-C": 20, "Equity": 3})

        self.assertEqual(tracker.cycles["PMH-C"]["hours"], 20)
        self.assertEqual(tracker.cycles["Equity"]["hours"], 3)

    def test_roles_and_suicide_can_overlap(self):
        valid, message = self.tracker.validate_entry(
            {
                "title": "Course",
                "date": "2026-01-02",
                "hours": 1,
                "is_roles": 1,
                "is_suicide": 1,
            }
        )

        self.assertTrue(valid, message)

    def test_roles_and_ethics_cannot_overlap(self):
        valid, message = self.tracker.validate_entry(
            {
                "title": "Course",
                "date": "2026-01-02",
                "hours": 1,
                "is_roles": 1,
                "is_ethics": 1,
            }
        )

        self.assertFalse(valid)
        self.assertIn("Ethics and Roles", message)

    def test_requires_at_least_one_category(self):
        valid, message = self.tracker.validate_entry(
            {"title": "Course", "date": "2026-01-02", "hours": 1}
        )

        self.assertFalse(valid)
        self.assertIn("at least one", message)

    def test_cycle_status_only_counts_records_in_selected_window(self):
        tracker = ComplianceTracker(
            FakeStorage(
                [
                    {"date": "2024-06-01", "hours": 10, "is_pmhc": 1},
                    {"date": "2025-06-01", "hours": 4, "is_pmhc": 1},
                ]
            )
        )

        status = tracker.get_cycle_status(
            "PMH-C",
            datetime(2023, 1, 1),
            reference_date=datetime(2026, 5, 16),
        )

        self.assertEqual(status["cycle_start"], datetime(2025, 1, 1))
        self.assertEqual(status["cycle_end"], datetime(2026, 12, 31))
        self.assertEqual(status["collected_hours"], 4)

    def test_cycle_offset_can_show_prior_window(self):
        tracker = ComplianceTracker(
            FakeStorage(
                [
                    {"date": "2024-06-01", "hours": 10, "is_pmhc": 1},
                    {"date": "2025-06-01", "hours": 4, "is_pmhc": 1},
                ]
            )
        )

        status = tracker.get_cycle_status(
            "PMH-C",
            datetime(2023, 1, 1),
            cycle_offset=-1,
            reference_date=datetime(2026, 5, 16),
        )

        self.assertEqual(status["cycle_start"], datetime(2023, 1, 1))
        self.assertEqual(status["cycle_end"], datetime(2024, 12, 31))
        self.assertEqual(status["collected_hours"], 10)


if __name__ == "__main__":
    unittest.main()
