from __future__ import annotations

import json
import unittest

from audit import NAMES, parse_trace
from candidate import ALLOCATION, MAIN_SHA, RUNNER_BLOB, T4_BLOB


class T5ConstructionTests(unittest.TestCase):
    def test_allocation_and_source_identities_are_pinned(self) -> None:
        self.assertEqual(ALLOCATION, "MAP01-TERMINAL-WAIT-BOUNDARY-3211-T5-CONTAINER-20261002-01")
        self.assertEqual(len(MAIN_SHA), 40)
        self.assertEqual(len(T4_BLOB), 40)
        self.assertEqual(len(RUNNER_BLOB), 40)

    def test_exact_four_predeclared_case_names(self) -> None:
        self.assertEqual(NAMES, {"within_bound", "wrong_id", "absent", "late_exact"})

    def test_parser_handles_literal_backslash_n_sidecar_separator(self) -> None:
        raw = b'{"event":"ready"}\\n{"event":"terminal","id":"x"}\\n'
        self.assertEqual(parse_trace(raw), [{"event": "ready"}, {"event": "terminal", "id": "x"}])

    def test_parser_rejects_corrupt_trace(self) -> None:
        with self.assertRaises((ValueError, json.JSONDecodeError)):
            parse_trace(b'{"event":')


if __name__ == "__main__":
    unittest.main()
