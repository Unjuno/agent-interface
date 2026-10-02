from __future__ import annotations

import json
import hashlib
import tempfile
import unittest
from pathlib import Path

from audit import EXPECTED_EVENTS, audit
from candidate import EXPECTED_EVENTS as CANDIDATE_EVENTS
from trace_writer import write_jsonl, write_legacy_control


class JsonlWriterContractTests(unittest.TestCase):
    def test_event_fixture_has_embedded_newline_and_terminal_order(self) -> None:
        self.assertEqual(CANDIDATE_EVENTS, EXPECTED_EVENTS)
        self.assertEqual([row["event"] for row in EXPECTED_EVENTS], ["probe", "terminal"])
        self.assertIn("\n", EXPECTED_EVENTS[0]["text"])

    def test_fixed_writer_emits_strict_one_event_per_line(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "trace.jsonl"
            write_jsonl(path, EXPECTED_EVENTS)
            lines = path.read_bytes().splitlines()
            self.assertEqual(len(lines), 2)
            self.assertEqual([json.loads(line) for line in lines], EXPECTED_EVENTS)

    def test_historical_delimiter_control_fails_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "control.txt"
            write_legacy_control(path, EXPECTED_EVENTS)
            self.assertEqual(len(path.read_bytes().splitlines()), 1)
            with self.assertRaises(json.JSONDecodeError):
                json.loads(path.read_text(encoding="utf-8").splitlines()[0])

    def test_independent_audit_accepts_fixed_and_rejects_control(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "candidate.json").write_text(json.dumps({
                "child_exit_code": 0,
                "events": EXPECTED_EVENTS,
                "artifacts": {},
            }), encoding="utf-8")
            write_jsonl(root / "session-events.jsonl", EXPECTED_EVENTS)
            write_legacy_control(root / "legacy-control.txt", EXPECTED_EVENTS)
            receipt = json.loads((root / "candidate.json").read_text(encoding="utf-8"))
            for key, filename in (("fixed", "session-events.jsonl"), ("legacy_control", "legacy-control.txt")):
                raw = (root / filename).read_bytes()
                receipt["artifacts"][key] = {
                    "byte_count": len(raw),
                    "sha256": __import__("hashlib").sha256(raw).hexdigest(),
                    "physical_line_count": len(raw.splitlines()),
                }
            (root / "candidate.json").write_text(json.dumps(receipt), encoding="utf-8")
            (root / "candidate.json").write_text(json.dumps({
                **receipt,
                "freeze_sha256": hashlib.sha256((Path(__file__).parent / "FREEZE.json").read_bytes()).hexdigest(),
            }), encoding="utf-8")
            self.assertEqual(
                audit(root, Path(__file__).parent)["decision"], "PASS_WRITER_CONTRACT_SCOPED"
            )


if __name__ == "__main__":
    unittest.main()
