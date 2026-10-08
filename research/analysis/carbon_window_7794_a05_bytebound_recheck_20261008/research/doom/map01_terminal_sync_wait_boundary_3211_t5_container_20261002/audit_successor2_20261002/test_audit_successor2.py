import unittest
from pathlib import Path
import shutil
import tempfile
import json

from audit_successor2 import audit, parse_events


ROOT = Path(__file__).parent
BUNDLE = ROOT / "input" / "research" / "doom" / "map01_terminal_sync_wait_boundary_3211_t5_container_20261002"
RECEIPT = BUNDLE / "results" / "container-01"


class ParseEventsTests(unittest.TestCase):
    def test_parses_literal_backslash_n_delimited_json_objects(self):
        raw = b'{"event":"ready"}\\n{"event":"terminal","id":"x"}\\n'
        self.assertEqual(
            parse_events(raw),
            [{"event": "ready"}, {"event": "terminal", "id": "x"}],
        )

    def test_rejects_malformed_delimited_record(self):
        with self.assertRaises(ValueError):
            parse_events(b'{"event":"ready"}\\nnot-json\\n')

    def test_rejects_physical_newline_framing_not_in_frozen_contract(self):
        with self.assertRaises(ValueError):
            parse_events(b'{"event":"ready"}\n{"event":"terminal"}\n')


class RetainedTraceAuditTests(unittest.TestCase):
    def test_reconstructs_all_four_frozen_cases_without_running_candidate(self):
        result = audit(BUNDLE, RECEIPT)
        self.assertEqual(result["decision"], "PASS_AUDIT_SUCCESSOR2_SCOPED")
        self.assertEqual(result["package_manifest_entries_verified"], 13)
        self.assertEqual(result["candidate_invocations"], 0)
        self.assertEqual(result["case_count"], 4)

    def test_rejects_sidecar_mutation(self):
        with tempfile.TemporaryDirectory() as temp:
            candidate_copy = Path(temp) / "candidate"
            shutil.copytree(RECEIPT, candidate_copy)
            trace = candidate_copy / "absent" / "session-events.jsonl"
            trace.write_bytes(trace.read_bytes() + b"tamper")
            with self.assertRaisesRegex(ValueError, "trace digest/byte-count mismatch"):
                audit(BUNDLE, candidate_copy)


if __name__ == "__main__":
    unittest.main()
