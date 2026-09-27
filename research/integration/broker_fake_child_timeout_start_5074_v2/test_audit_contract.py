import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


AUDIT_PATH = Path(__file__).with_name("audit.py")
SPEC = importlib.util.spec_from_file_location("issue5074_audit", AUDIT_PATH)
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def fixture():
    names = AUDIT.EXPECTED
    rows = []
    for name in names:
        rows.append({"name": name, "process_exit": 0, "external_timeout": False,
                     "child_start_marker": False, "child_start_marker_ns": None,
                     "child_start_record": None, "marker_error": None,
                     "child_calls": [], "receipts": {}, "responses": {}, "files": {}})
    by = {row["name"]: row for row in rows}
    for name, code in (("exit-0", 0), ("exit-23", 23)):
        by[name]["process_exit"] = code
        by[name]["child_calls"] = [{"event": "child_started", "argv": ["-", "prompt:"+name]}]
        by[name]["receipts"][name+".broker.json"] = {"returncode": code, "authority_granted": False}
    t = by["timeout-after-start"]
    t.update(child_start_marker=True, child_start_marker_ns=101,
             child_start_record={"event": "child_started", "started_ns": 100},
             child_calls=[{"event": "child_started"}],
             broker_timeout_s=5,
             receipts={"timeout-after-start.broker.json": {
                 "returncode": None, "stop_reason": "HOST_BROKER_SUBPROCESS_TIMEOUT",
                 "started_ns": 50, "timeout_s": 5,
                 "authority_granted": False}},
             responses={"timeout-after-start.response.jsonl": ""})
    m = by["missing-executable"]
    m["receipts"] = {"missing-executable.broker.json": {
        "returncode": None, "stop_reason": "HOST_BROKER_EXECUTABLE_UNAVAILABLE",
        "authority_granted": False}}
    by["malformed-json"]["process_exit"] = 1
    by["idle-once"].update(external_timeout=True, process_exit=-9)
    by["sorted-once"].update(
        child_calls=[{"event": "child_started", "argv": ["-", "prompt:a"]}],
        receipts={"a.broker.json": {"returncode": 0, "authority_granted": False}},
        responses={"a.response.jsonl": "ok\n"})
    by["sorted-once"]["child_calls"][0]["stdin"] = "prompt:a\n"
    return {"schema": "broker-timeout-start-raw-v1", "cases": rows}


class AuditContractTest(unittest.TestCase):
    def test_accepts_minimal_frozen_semantic_fixture(self):
        self.assertEqual(AUDIT.inspect(fixture(), verify_files=False,
                                       verify_queued_file=False), [])

    def test_nine_in_memory_corruption_controls_are_rejected(self):
        self.assertEqual(AUDIT.corruption_controls(fixture(), verify_files=False), 9)

    def test_frozen_formal_control_count_matches_auditor(self):
        freeze = json.loads(AUDIT_PATH.with_name("FREEZE.json").read_text())
        self.assertEqual(freeze["audit_invocation"]["corruption_controls"],
                         AUDIT.CORRUPTION_CONTROL_COUNT)

    def test_file_reconciliation_rejects_divergent_hashed_payload_views(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ipc = root / "ipc"
            ipc.mkdir()
            (root / "child-calls.jsonl").write_text(
                '{"event":"child_started","stdin":"prompt:a\\n"}\n',
                encoding="utf-8")
            (ipc / "a.broker.json").write_text(
                '{"returncode":0}\n', encoding="utf-8")
            (ipc / "a.response.jsonl").write_text("ok\n", encoding="utf-8")
            row = {"name": "sorted-once",
                   "child_calls": [{"event": "child_started", "stdin": "prompt:z\\n"}],
                   "receipts": {"a.broker.json": {"returncode": 0}},
                   "responses": {"a.response.jsonl": "ok\\n"}}
            with self.assertRaisesRegex(ValueError, "child-call bytes mismatch"):
                AUDIT.reconcile_case_files(row, root)


if __name__ == "__main__":
    unittest.main()
