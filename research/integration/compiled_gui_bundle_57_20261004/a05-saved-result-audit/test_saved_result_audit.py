import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("saved_result_audit", HERE / "saved_result_audit.py")
MODULE = importlib.util.module_from_spec(SPEC) if SPEC else None
if SPEC and SPEC.loader:
    try:
        SPEC.loader.exec_module(MODULE)
    except FileNotFoundError:
        MODULE = None


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")


def write_journal(path, terminal_ids, request_count):
    rows = []
    for index in range(1, request_count + 1):
        terminal = None
        if index <= len(terminal_ids):
            terminal = {"id": terminal_ids[index - 1], "status": "completed",
                        "release": {"verified": True, "keys_down": [], "buttons_down": []}}
        frame = {"version": "append-checkpoint-v1", "index": index,
                 "previous": rows[-1]["sha256"] if rows else None,
                 "state": {"pending": None,
                           "last_resolution": {"request_id": f"request-{index}",
                                               **({"terminal": terminal} if terminal else {})}}}
        frame["sha256"] = hashlib.sha256(canonical(frame)).hexdigest()
        rows.append(frame)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"".join(canonical(row) + b"\n" for row in rows))


def write_history(path, token):
    row = {"schema": "integrated_efficiency_submission_v1", "task_id": "task-1",
           "layout": "A", "expected_token": token, "submitted_values": [token], "exact": True}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")


def make_case(bundle, run_name, token, caller=False):
    run = bundle / "client" / run_name
    terminal_ids = ["check-field", "enter-action", "check-submit", "submit-action"]
    image_names = ["011.png", "018.png", "024.png"]
    states = ["empty", "filled", "submitted"]
    observations = []
    for index, (sequence, state, image_name) in enumerate(zip((11, 18, 24), states, image_names)):
        image = run / "client" / "runtime" / image_name
        image.parent.mkdir(parents=True, exist_ok=True)
        image.write_bytes(f"screenshot-{run_name}-{image_name}".encode())
        image_hash = hashlib.sha256(image.read_bytes()).hexdigest()
        crop = run / "client" / f"ocr-{sequence}.png"
        crop.write_bytes(f"crop-{run_name}-{sequence}".encode())
        predicates = {"exact_token_visible": state == "filled", "target_valid": True,
                      "exact_saved_title": state == "submitted"}
        digest = hashlib.sha256((image_hash + json.dumps(predicates, sort_keys=True)).encode()).hexdigest()
        observations.append({"state": state,
            "normalized": {"sequence": sequence, "evidence_ref": f"runtime/{image_name}",
                           "evidence_digest": digest, "predicates": predicates},
            "image_sha256": image_hash,
            "raw_observation": {"image": f"/out/client/runtime/{image_name}"},
            "ocr": {"exit": 0, "stdout": token + "\n" if state == "filled" else "\n"}})

    transitions = []
    programs = [
        {"label": "compiled-check-field", "terminal": {"id": "check-field", "status": "completed",
            "release": {"verified": True, "keys_down": [], "buttons_down": []}},
            "target_checks": [{"eligible": True, "status": "VALID", "observation_sequence": 11}]},
        {"label": "compiled-check-submit", "terminal": {"id": "check-submit", "status": "completed",
            "release": {"verified": True, "keys_down": [], "buttons_down": []}},
            "target_checks": [{"eligible": True, "status": "VALID", "observation_sequence": 18}]},
    ]
    for action, action_id, image_name in zip(("enter", "submit"), (terminal_ids[1], terminal_ids[3]), ("011.png", "018.png")):
        transitions.append({"action": action, "action_id": action_id,
                            "effect_ref": f"terminal:{action_id}",
                            "evidence_ref": f"runtime/{image_name}", "release_verified": True,
                            "observation_sequence": 11 if action == "enter" else 18})
        programs.append({"label": f"compiled-{action}",
            "terminal": {"id": action_id, "status": "completed",
                         "release": {"verified": True, "keys_down": [], "buttons_down": []}},
            "pointer_admissions": [{"status": "accepted"}]})

    receipt = {"outcome": "TASK_SUCCEEDED", "completed_transitions": 2,
               "frontier_model_resumptions": 0, "transitions": transitions,
               "raw_evidence_retention": "adapter_responsibility_unverified",
               "latest_evidence_ref": "runtime/024.png"}
    evaluation = {"success": False, "record_count": 1,
                  "exact_counts": {f"task-{i}": int(i == 1) for i in range(1, 7)},
                  "unexpected": [], "duplicates": {},
                  "missing": [f"task-{i}" for i in range(2, 7)]}
    programs = [programs[0], programs[2], programs[1], programs[3]]
    result = {"status": "OBSERVED", "goal": {"task_id": "task-1", "token": token,
                  "layout": "A", "phase": "cold"}, "independent_evaluation": evaluation,
              "programs": programs, "durable_calls": 6,
              "raw_observations": observations,
              "receipt": receipt}
    if caller:
        result["graph"] = {"receipt": receipt, "raw_observations": observations}
        result["caller"] = {"outcome": "TASK_SUCCEEDED", "reason": "verified_effect",
            "task_effect": "succeeded", "delivery": "confirmed",
            "execution_progress": {"status": "completed"}, "route": "reuse",
            "comparison": {"class": "warm_reuse"}, "accounting": {"attempted_calls": 0},
            "model_call_ledger": []}
        result["setup"] = {"elapsed_ns": 1234, "durable_calls": 2,
                           "grounding": "fixed points; human setup cost unavailable"}
    write_json(run / "result.json", result)
    write_history(run / "client" / "runtime" / "submission-history.jsonl", token)
    write_journal(run / "client" / "journal.jsonl", terminal_ids, 6)


def make_bundle(bundle):
    make_case(bundle, "graph-cropocr-output", "t991060-1")
    make_case(bundle, "caller-compiled-output", "t991061-1", caller=True)
    manifest = {}
    for path in sorted(bundle.rglob("*")):
        if path.is_file() and path.name != "FILES.json":
            manifest[path.relative_to(bundle).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    write_json(bundle / "FILES.json", manifest)


class SavedResultAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.bundle = Path(self.temp.name)
        make_bundle(self.bundle)

    def tearDown(self):
        self.temp.cleanup()

    def audit(self):
        self.assertIsNotNone(MODULE, "saved_result_audit.py must provide the bundle auditor")
        return MODULE.audit_bundle(self.bundle)

    def test_valid_records_are_scoped_to_two_exact_task1_constructions(self):
        report = self.audit()

        self.assertEqual(report["integrity"], "PASS")
        self.assertEqual(report["scope"], "two fixed-layout task-1 constructions only")
        self.assertEqual(report["decision"], "HOLD_FULL_MATCHED_COMPARISON")
        self.assertIn("caller_phase_label_conflict", report["warnings"])
        self.assertIn("caller_effect_evidence_receipt_absent", report["warnings"])

    def test_wrong_post_token_is_rejected_even_when_manifest_is_refreshed(self):
        history = self.bundle / "client" / "caller-compiled-output" / "client" / "runtime" / "submission-history.jsonl"
        row = json.loads(history.read_text(encoding="utf-8"))
        row["submitted_values"] = ["wrong-token"]
        history.write_text(json.dumps(row) + "\n", encoding="utf-8")
        self.refresh_manifest()

        report = self.audit()

        self.assertIn("caller-compiled-output:post_token_mismatch", report["errors"])

    def test_journal_terminal_ids_must_join_compiled_program_terminals(self):
        journal = self.bundle / "client" / "graph-cropocr-output" / "client" / "journal.jsonl"
        rows = [json.loads(line) for line in journal.read_text(encoding="utf-8").splitlines()]
        for row in rows:
            if row["state"]["last_resolution"].get("terminal"):
                row["state"]["last_resolution"]["terminal"]["id"] = "unrelated-action"
        self.rehash_journal(journal, rows)
        self.refresh_manifest()

        report = self.audit()

        self.assertIn("graph-cropocr-output:journal_program_id_mismatch", report["errors"])

    def test_changed_image_bytes_are_rejected_against_saved_observation_digest(self):
        image = self.bundle / "client" / "caller-compiled-output" / "client" / "runtime" / "018.png"
        image.write_bytes(b"changed screenshot")
        self.refresh_manifest()

        report = self.audit()

        self.assertIn("caller-compiled-output:image_digest_mismatch", report["errors"])

    def test_full_six_success_claim_is_rejected_when_only_task1_has_a_post(self):
        result_path = self.bundle / "client" / "graph-cropocr-output" / "result.json"
        result = json.loads(result_path.read_text(encoding="utf-8"))
        result["independent_evaluation"]["success"] = True
        result["independent_evaluation"]["record_count"] = 6
        result["independent_evaluation"]["exact_counts"] = {f"task-{i}": 1 for i in range(1, 7)}
        result["independent_evaluation"]["missing"] = []
        write_json(result_path, result)
        self.refresh_manifest()

        report = self.audit()

        self.assertIn("graph-cropocr-output:full_six_status_contradicts_one_task_record", report["errors"])

    def test_stale_target_check_sequence_is_rejected(self):
        result_path = self.bundle / "client" / "caller-compiled-output" / "result.json"
        result = json.loads(result_path.read_text(encoding="utf-8"))
        result["programs"][0]["target_checks"][0]["observation_sequence"] = 10
        write_json(result_path, result)
        self.refresh_manifest()

        report = self.audit()

        self.assertIn("caller-compiled-output:target_check_sequence_mismatch", report["errors"])

    def test_windows_style_path_escape_is_rejected(self):
        result_path = self.bundle / "client" / "graph-cropocr-output" / "result.json"
        result = json.loads(result_path.read_text(encoding="utf-8"))
        result["raw_observations"][0]["normalized"]["evidence_ref"] = "runtime/..\\outside.png"
        write_json(result_path, result)
        self.refresh_manifest()

        report = self.audit()

        self.assertIn("graph-cropocr-output:unsafe_observation_reference", report["errors"])

    def test_boolean_task_count_is_not_accepted_as_integer_one(self):
        result_path = self.bundle / "client" / "graph-cropocr-output" / "result.json"
        result = json.loads(result_path.read_text(encoding="utf-8"))
        result["independent_evaluation"]["record_count"] = True
        result["independent_evaluation"]["exact_counts"]["task-1"] = True
        write_json(result_path, result)
        self.refresh_manifest()

        report = self.audit()

        self.assertIn("graph-cropocr-output:full_six_status_contradicts_one_task_record", report["errors"])

    def test_duplicate_manifest_path_is_rejected(self):
        path = "client/graph-cropocr-output/result.json"
        manifest = self.bundle / "FILES.json"
        manifest.write_text(json.dumps({path: "0" * 64})[:-1] + f',"{path}":"{"1" * 64}"}}',
                            encoding="utf-8")

        report = self.audit()

        self.assertIn("duplicate_json_key:FILES.json", report["errors"])

    def test_transition_must_reference_its_fresh_observation_sequence(self):
        result_path = self.bundle / "client" / "caller-compiled-output" / "result.json"
        result = json.loads(result_path.read_text(encoding="utf-8"))
        result["graph"]["receipt"]["transitions"][1]["observation_sequence"] = 11
        write_json(result_path, result)
        self.refresh_manifest()

        report = self.audit()

        self.assertIn("caller-compiled-output:transition_observation_sequence_mismatch", report["errors"])

    def refresh_manifest(self):
        manifest = {}
        for path in sorted(self.bundle.rglob("*")):
            if path.is_file() and path.name != "FILES.json":
                manifest[path.relative_to(self.bundle).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
        write_json(self.bundle / "FILES.json", manifest)

    @staticmethod
    def rehash_journal(path, rows):
        previous = None
        for index, row in enumerate(rows, 1):
            row["index"] = index
            row["previous"] = previous
            row["sha256"] = hashlib.sha256(canonical({k: v for k, v in row.items() if k != "sha256"})).hexdigest()
            previous = row["sha256"]
        path.write_bytes(b"".join(canonical(row) + b"\n" for row in rows))


if __name__ == "__main__":
    unittest.main()
