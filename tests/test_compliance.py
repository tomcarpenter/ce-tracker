import unittest

from utils.compliance import ComplianceTracker


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


if __name__ == "__main__":
    unittest.main()
