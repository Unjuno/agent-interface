from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from audit_formal_stop import ROOT, audit

FORMAL = ROOT / "formal/run-01"


class FormalStopAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        case = self.root / "p1-immediate"
        (case / "runtime").mkdir(parents=True)
        for relative in (
            "FORMAL_RESULT.json",
            "p1-immediate/launch.json",
            "p1-immediate/controller_events.json",
            "p1-immediate/runtime/sources.json",
            "p1-immediate/runtime/setup.txt",
        ):
            source = FORMAL / relative
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())

    def tearDown(self):
        self.temp.cleanup()

    def edit_json(self, relative: str, update):
        path = self.root / relative
        value = json.loads(path.read_text())
        update(value)
        path.write_text(json.dumps(value))

    def test_raw_stop_record_passes(self):
        report = audit(self.root)
        self.assertEqual(report["decision"], "PASS_STOP_EVIDENCE_COMPLETE")
        self.assertEqual(report["runtime_source_entries_matching"], 20)

    def test_consumed_invocation_mutation_rejects(self):
        self.edit_json("FORMAL_RESULT.json", lambda row: row.__setitem__("formal_invocations", 0))
        report = audit(self.root)
        self.assertFalse(report["checks"]["single_formal_invocation"])

    def test_arm_mutation_rejects(self):
        self.edit_json("p1-immediate/launch.json", lambda row: row.__setitem__("arm", "ONE_WINDOW_PREROLL"))
        report = audit(self.root)
        self.assertFalse(report["checks"]["typed_stop_matches_first_scheduled_case"])

    def test_controller_event_mutation_rejects(self):
        path = self.root / "p1-immediate/controller_events.json"
        path.write_text(json.dumps([{"event": "command"}]))
        report = audit(self.root)
        self.assertFalse(report["checks"]["no_controller_command_or_physical_edge"])

    def test_session_stream_mutation_rejects(self):
        path = self.root / "p1-immediate/runtime/events.jsonl"
        path.write_text("{}\n")
        report = audit(self.root)
        self.assertFalse(report["checks"]["no_ready_observation_or_scorer_stream"])

    def test_source_hash_mutation_rejects(self):
        self.edit_json(
            "p1-immediate/runtime/sources.json",
            lambda row: row.__setitem__("doom/session_map01_v12.py", "0" * 64),
        )
        report = audit(self.root)
        self.assertFalse(report["checks"]["runtime_source_identities_match_frozen_manifest"])


if __name__ == "__main__":
    unittest.main()
