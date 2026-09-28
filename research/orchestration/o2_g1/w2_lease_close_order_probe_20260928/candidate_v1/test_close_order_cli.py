"""Host construction tests for the separate W2 close candidate/raw auditor."""
import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parent
FIXTURE = Path(os.environ["W2_TRACE_FIXTURE"])
FIXTURE_SHA256 = "6a693f06b1b4be15a8da35ec3aaf806d7fb3601091c8ef638c516069d1b4e95f"


def versioned_case(close_time=None, close_actuation="A4", overlap_down=False):
    document = json.loads(FIXTURE.read_bytes())
    target = next(c for c in document["cases"] if c["case_id"] == "release-before-terminal")
    opened = next(e for e in target["events"] if e["event_type"] == "LEASE_OPEN")
    opened["lineage"]["actuation_id"] = "A4"
    if overlap_down:
        down = next(e for e in target["events"] if e.get("event_type") == "INPUT_EDGE_BRACKET" and e["payload"]["edge"] == "down")
        down["time"] = {"lower_ns": 45, "upper_ns": 55, "censoring": "bounded"}
        down["payload"]["transition_interval_ns"] = [45, 55]
    if close_time is not None:
        close = {
            "event_id": "close-order-control",
            "event_type": "LEASE_CLOSE",
            "source_role": "executor",
            "clock": copy.deepcopy(opened["clock"]),
            "time": {"lower_ns": close_time, "upper_ns": close_time, "censoring": "exact"},
            "input_authority": "false",
            "semantic_authority": "false",
            "lineage": {"lease_id": "L4", "actuation_id": close_actuation, "parent_event_ids": []},
            "payload": {},
        }
        if close_actuation is None:
            close["lineage"].pop("actuation_id")
        target["events"].append(close)
        target["events"].sort(key=lambda e: e["time"]["lower_ns"])
    return document


class CloseOrderCliTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="w2-close-order-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def _run(self, name, close_time=None, close_actuation="A4", overlap_down=False):
        trace = self.root / f"{name}.trace-cases.json"
        trace.write_text(json.dumps(versioned_case(close_time, close_actuation, overlap_down), indent=2) + "\n", encoding="utf-8")
        out = self.root / name
        out.mkdir()
        candidate = out / "candidate.json"
        audit = out / "audit.json"
        run = subprocess.run([sys.executable, str(ROOT / "close_order_cli.py"), "--traces", str(trace), "--out", str(candidate)], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        audited = subprocess.run([sys.executable, str(ROOT / "audit_close_order_cli.py"), "--traces", str(trace), "--candidate", str(candidate), "--out", str(audit)], capture_output=True, text=True)
        return trace, candidate, audit, audited

    @staticmethod
    def _statuses(candidate, case_id="release-before-terminal"):
        report = json.loads(candidate.read_text(encoding="utf-8"))
        case = next(c for c in report["cases"] if c["case_id"] == case_id)
        return [row["status"] for row in case["decisions"]]

    def test_frozen_fixture_hash_and_no_close_control(self):
        self.assertEqual(hashlib.sha256(FIXTURE.read_bytes()).hexdigest(), FIXTURE_SHA256)
        _, candidate, audit, audited = self._run("no-close")
        self.assertEqual(audited.returncode, 0, audited.stderr)
        self.assertEqual(self._statuses(candidate), ["AUTHORIZED_MATCH"] * 2)
        self.assertEqual(json.loads(audit.read_text())["errors"], [])

    def test_edges_entirely_before_close_remain_admitted(self):
        _, candidate, _, audited = self._run("pre-close", close_time=450)
        self.assertEqual(audited.returncode, 0, audited.stderr)
        self.assertEqual(self._statuses(candidate), ["AUTHORIZED_MATCH"] * 2)

    def test_edges_after_close_fail_closed(self):
        _, candidate, _, audited = self._run("post-close", close_time=50)
        self.assertEqual(audited.returncode, 0, audited.stderr)
        self.assertEqual(self._statuses(candidate), ["REJECT_EDGE_AFTER_LEASE_CLOSE"] * 2)

    def test_interval_overlapping_close_is_held(self):
        _, candidate, _, audited = self._run("overlap", close_time=50, overlap_down=True)
        self.assertEqual(audited.returncode, 0, audited.stderr)
        self.assertEqual(self._statuses(candidate), ["HOLD_EDGE_CLOSE_ORDER_UNCERTAIN", "REJECT_EDGE_AFTER_LEASE_CLOSE"])

    def test_foreign_or_missing_close_lineage_is_held(self):
        for name, lineage in (("foreign-close", "FOREIGN-ACTUATION"), ("missing-close", None)):
            with self.subTest(name=name):
                _, candidate, _, audited = self._run(name, close_time=50, close_actuation=lineage)
                self.assertEqual(audited.returncode, 0, audited.stderr)
                self.assertEqual(self._statuses(candidate), ["HOLD_CLOSE_LINEAGE_UNRESOLVED"] * 2)

    def test_raw_auditor_rejects_tampered_candidate_report(self):
        trace, candidate, _, _ = self._run("tamper")
        report = json.loads(candidate.read_text(encoding="utf-8"))
        case = next(c for c in report["cases"] if c["case_id"] == "release-before-terminal")
        case["decisions"][0]["status"] = "REJECT_ACTUATION_MISMATCH"
        candidate.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        audit = self.root / "tamper-audit.json"
        result = subprocess.run([sys.executable, str(ROOT / "audit_close_order_cli.py"), "--traces", str(trace), "--candidate", str(candidate), "--out", str(audit)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("candidate_raw_disagreement:release-before-terminal", result.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
