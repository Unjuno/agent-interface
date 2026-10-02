from __future__ import annotations

import unittest

from audit import CASE_NAMES, SOURCE_BLOB, decode_object_stream
from candidate import EXPECTED_CASES, SOURCE_REL, git_blob_sha1


class WaitBoundaryConstructionTests(unittest.TestCase):
    def test_upstream_source_identity_is_pinned(self) -> None:
        self.assertEqual(len(SOURCE_BLOB), 40)
        self.assertEqual(git_blob_sha1(b""), "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391")
        self.assertTrue(str(SOURCE_REL).endswith("runner_3211_diagnostic_v2.py"))

    def test_four_cases_separate_wait_and_event_conditions(self) -> None:
        self.assertEqual(set(EXPECTED_CASES), CASE_NAMES)
        self.assertEqual(EXPECTED_CASES["within_bound"]["terminal_id"], "fallback-within")
        self.assertEqual(EXPECTED_CASES["wrong_id"]["terminal_id"], "other-terminal")
        self.assertIsNone(EXPECTED_CASES["absent"]["terminal_id"])
        self.assertEqual(EXPECTED_CASES["late_exact"]["terminal_id"], "fallback-late")

    def test_late_case_has_margin_beyond_its_timeout(self) -> None:
        row = EXPECTED_CASES["late_exact"]
        self.assertGreater(row["delay_s"], row["timeout_s"] * 3)

    def test_structural_trace_parser_recovers_literal_delimiter(self) -> None:
        raw = b'{"event":"ready"}\\n{"event":"terminal","id":"x"}\\n'
        self.assertEqual(
            decode_object_stream(raw),
            [{"event": "ready"}, {"event": "terminal", "id": "x"}],
        )


if __name__ == "__main__":
    unittest.main()
