import unittest
from code.app.validation import validate_rows


class ValidationTests(unittest.TestCase):
    def test_not_applicable_empty_steps(self):
        req = [{"case_id": "case_000"}]
        out = [{"case_id": "case_000", "deletion_status": "NOT_APPLICABLE", "steps_json": []}]
        self.assertEqual(validate_rows(out, req), [])

    def test_step_numbers_consecutive(self):
        req = [{"case_id": "case_001"}]
        out = [{"case_id": "case_001", "deletion_status": "INCOMPLETE", "steps_json": [{
            "step_no": 2, "phase": "FINDING", "system_id": "x", "resource_id": "y",
            "operation": "REPORT_REMAINING_RECORD", "state": "PRESENT", "evidence_id": "e1"}]}]
        self.assertTrue(any("consecutive" in x for x in validate_rows(out, req)))

    def test_complete_needs_evidence(self):
        req = [{"case_id": "case_001"}]
        out = [{"case_id": "case_001", "deletion_status": "COMPLETE", "steps_json": [{
            "step_no": 1, "phase": "VERIFICATION", "system_id": "x", "resource_id": "y",
            "operation": "VERIFY_RECORD_ABSENT", "state": "ABSENT", "evidence_id": ""}]}]
        self.assertTrue(any("evidence citation" in x for x in validate_rows(out, req)))


if __name__ == "__main__":
    unittest.main()
