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
    freeze = json.loads(AUDIT_PATH.with_name("FREEZE.json").read_text())
    receipt = {
        "allocation": freeze["allocation"], "issue": freeze["issue"],
        "base_main": freeze["base_main"], "source_commit_sha": "a" * 40,
        "broker_git_blob": freeze["source"]["broker_git_blob"],
        "broker_sha256": freeze["source"]["broker_raw_sha256"],
        "image": freeze["source"]["image_id"] + " " + freeze["source"]["platform"],
        "formal_source_sha256": freeze["source"]["sha256"],
        "resolved_repo": "/host/repo", "resolved_study": "/host/study",
        "resolved_output": "/host/formal-output",
        "resolved_audit_output": "/host/audit-output",
        "resolved_receipt": "/host/invocation-receipt.json",
        "resource_release": "/host/resource-release.json",
        "docker_inventory_before": [],
        "ownership_release": {"issue": freeze["issue"], "released": True,
                              "observed_running_containers": []},
    }
    receipt["command"], receipt["audit_command_template"] = (
        AUDIT.expected_docker_commands(receipt, freeze))
    return {"schema": "broker-timeout-start-raw-v1",
            "allocation": freeze["allocation"], "invocation_receipt": receipt,
            "cases": rows}


class AuditContractTest(unittest.TestCase):
    def test_accepts_minimal_frozen_semantic_fixture(self):
        self.assertEqual(AUDIT.inspect(fixture(), verify_files=False,
                                       verify_queued_file=False), [])

    def test_child_start_before_broker_and_after_deadline_are_rejected(self):
        for started_ns, marker_ns in ((1, 101), (5_000_000_050, 5_000_000_050)):
            candidate = fixture()
            candidate["cases"][2]["child_start_record"]["started_ns"] = started_ns
            candidate["cases"][2]["child_start_marker_ns"] = marker_ns
            with self.assertRaisesRegex(ValueError, "child start was not before broker deadline"):
                AUDIT.inspect(candidate, verify_files=False, verify_queued_file=False)
    def test_fifteen_in_memory_corruption_controls_are_rejected(self):
        self.assertEqual(AUDIT.corruption_controls(fixture(), verify_files=False), 15)

    def test_invocation_receipt_freezes_network_cpu_and_slot_ownership(self):
        value = fixture()["invocation_receipt"]
        freeze = json.loads(AUDIT_PATH.with_name("FREEZE.json").read_text())
        AUDIT.validate_invocation_receipt(value, freeze)
        self.assertIn("--network=none", value["command"])
        self.assertIn("--cpus=0.25", value["command"])
        self.assertIn("--network=none", value["audit_command_template"])
        for mutate in (
            lambda x: x["command"].__setitem__(8, "--network=host"),
            lambda x: x["command"].__setitem__(10, "--cpus=4"),
            lambda x: x["audit_command_template"].__setitem__(8, "--network=host"),
            lambda x: x["ownership_release"].update(released=False),
            lambda x: x.update(docker_inventory_before=["unowned-container"]),
        ):
            candidate = copy.deepcopy(value)
            mutate(candidate)
            with self.assertRaises(ValueError):
                AUDIT.validate_invocation_receipt(candidate, freeze)

    def test_recomputed_manifest_cannot_hide_mutated_receipt_command(self):
        freeze = json.loads(AUDIT_PATH.with_name("FREEZE.json").read_text())
        raw_receipt = copy.deepcopy(fixture()["invocation_receipt"])
        raw_receipt["command"][8] = "--network=host"
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            receipt_path = root / "invocation-receipt.json"
            raw_path = root / "raw.json"
            manifest_path = root / "manifest.json"
            receipt_path.write_text(json.dumps(raw_receipt, sort_keys=True) + "\n",
                                    encoding="utf-8")
            raw_path.write_text(json.dumps({"invocation_receipt": raw_receipt},
                                           sort_keys=True) + "\n", encoding="utf-8")
            manifest = {
                path.name: {"sha256": __import__("hashlib").sha256(path.read_bytes()).hexdigest(),
                            "bytes": path.stat().st_size}
                for path in (raw_path, receipt_path)
            }
            manifest_path.write_text(json.dumps(manifest, sort_keys=True) + "\n",
                                     encoding="utf-8")
            actual_manifest = {
                path.name: {"sha256": __import__("hashlib").sha256(path.read_bytes()).hexdigest(),
                            "bytes": path.stat().st_size}
                for path in (raw_path, receipt_path)
            }
            self.assertEqual(manifest, actual_manifest,
                             "test precondition: manifest is recomputed after mutation")
            with self.assertRaisesRegex(ValueError, "formal invocation command/resource"):
                AUDIT.validate_receipt_binding(raw_receipt,
                    json.loads(receipt_path.read_text(encoding="utf-8")), freeze,
                    manifest, actual_manifest)

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
