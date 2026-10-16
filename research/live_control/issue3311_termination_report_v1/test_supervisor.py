"""Deterministic process-boundary tests for Issue #3311 termination reporting."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
LIVE = REPO / "research" / "live_control"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(LIVE))

import integrated_efficiency_protocol_v1 as protocol
from supervisor import REPORT_NAME, supervise


FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
PINS = {
    name: {"path": str(REPO / record["path"]), "sha256": record["sha256"]}
    for name, record in FREEZE["sources"].items()
}


def usage(input_tokens: int) -> dict:
    return {"input_tokens": input_tokens, "cached_input_tokens": 0,
            "cache_write_input_tokens": 0, "output_tokens": 0,
            "reasoning_output_tokens": 0}


def complete_trace() -> dict:
    discoveries = []
    for discovery_id in sorted(protocol.REQUIRED_DISCOVERY_IDS):
        discoveries.append({
            "id": discovery_id,
            "class": "integration_capability_gap",
            "discovered_phase": "pre_prereg",
            "symptom": "synthetic contract fixture",
            "blocking_requirement": "fixed diagnostic input",
            "repair": "none in this control",
            "regression_test": "supervisor unit control",
            "accounting_disposition": "engineering_excluded_zero_model",
            "status": "retained",
            "allocation_invalidated": False,
            "overhead": {
                "allocation_id": None, "model_calls": 0, "input_tokens": 0,
                "runtime_ns": None, "target_button_down_admissions": 0,
                "aggregation_scope": "allocation_total_nonadditive_across_shared_defects",
            },
        })
    preflight = {}
    arms = {}
    for arm in protocol.ARMS:
        preflight[arm] = {
            "call_id": "preflight-" + arm, "stage": "schema_preflight",
            "requested_model": "synthetic", "requested_effort": "none",
            "usage": usage(1), "model_visible_images": 0,
        }
        rows = []
        for index, task_id in enumerate(protocol.TASKS):
            calls = [{
                "call_id": f"{arm}-{task_id}-{call_index}",
                "stage": "anchor_model", "requested_model": "synthetic",
                "requested_effort": "none", "usage": usage(1 if arm == "persistent" else 1000),
            } for call_index in range(protocol.EXPECTED_MODEL_CALLS[arm][index])]
            repair_required = arm == "persistent" and index == 3
            rows.append({
                "arm": arm, "task_id": task_id, "layout": protocol.LAYOUTS[index],
                "route": protocol.EXPECTED_ROUTES[arm][index], "model_calls": calls,
                "planner_generations": len(calls), "model_visible_images": len(calls),
                "local_observations": 2, "durable_calls": 1,
                "pointer_admissions": 2, "old_target_pointer_admissions": 0,
                "releases_verified": True, "submission_count": 1,
                "exact_submission": True, "typed_outcome": "completed",
                "elapsed_ns": 1000, "source_to_completion_ns": 500,
                "input_feedback_ns": [100, 200],
                "repair": ({
                    "required": True, "old_reference_status": "missing",
                    "old_reference_pointer_admissions": 0, "attempted": True,
                    "succeeded": True,
                } if repair_required else {
                    "required": False, "old_reference_status": None,
                    "old_reference_pointer_admissions": 0, "attempted": False,
                    "succeeded": False,
                }),
            })
        arms[arm] = rows
    return {"schema": "integrated_efficiency_trace_v1", "arms": arms,
            "preflight_calls": preflight, "integration_discoveries": discoveries}


def process_command(code: str) -> list[str]:
    return [sys.executable, "-c", code]


class SupervisorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="issue3311-terminal-")
        self.root = Path(self.temp.name)

    def tearDown(self):
        record_root = os.environ.get("ISSUE3311_TERMINATION_ARTIFACT_DIR")
        if record_root and self.root.exists():
            destination = Path(record_root) / "cases" / self._testMethodName
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(self.root, destination)
        self.temp.cleanup()

    def supervise_at(self, name: str, command: list[str], audit: list[str] | None = None,
                     pins: dict | None = None) -> tuple[dict, Path]:
        output = self.root / name
        result = supervise(command, audit or process_command(
            "raise SystemExit(99)"), output, pins or PINS,
            allocation_id="ISSUE3311-TERMINATION-REPORT-20260928-01")
        return result, output

    def audit_terminal(self, output: Path) -> dict:
        completed = subprocess.run(
            [sys.executable, str(HERE / "audit_termination_report.py"),
             str(output / REPORT_NAME)], capture_output=True, text=True, check=False)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        return json.loads(completed.stdout)

    def test_complete_synthetic_trace_control_is_retain(self):
        result = protocol.evaluate(complete_trace())
        self.assertEqual(result["disposition"], "RETAIN")
        self.assertEqual(result["observed_break_even_task"], 1)

    def test_missing_sixth_row_exception_is_retained_as_audited_hold(self):
        output = self.root / "incomplete"
        output.mkdir()
        trace = complete_trace()
        trace["arms"]["persistent"].pop()
        (output / "incomplete-trace.json").write_text(
            json.dumps(trace), encoding="utf-8")
        script = (
            "import json,sys; "
            f"sys.path.insert(0, {str(LIVE)!r}); "
            "from pathlib import Path; "
            "from integrated_efficiency_protocol_v1 import evaluate; "
            "evaluate(json.loads(Path('incomplete-trace.json').read_text(encoding='utf-8')))"
        )
        result = supervise(process_command(script), process_command("raise SystemExit(99)"),
                           output, PINS,
                           allocation_id="ISSUE3311-TERMINATION-REPORT-20260928-01")
        self.assertEqual(result["status"], "HOLD")
        terminal = json.loads((output / REPORT_NAME).read_text(encoding="utf-8"))
        self.assertEqual(terminal["reason_code"], "HOLD_RUNNER_NONZERO_EXIT")
        self.assertEqual(terminal["disposition"], "HOLD")
        self.assertNotEqual(terminal["runner_exit_code"], 0)
        self.assertEqual(terminal["failure_type"], "ChildProcessExit")
        stderr = (output / "runner.stderr.log").read_text(encoding="utf-8")
        self.assertIn("exact six-task arm required", stderr)
        artifact_paths = {row["path"] for row in terminal["artifacts"]}
        self.assertIn("incomplete-trace.json", artifact_paths)
        self.assertIn("runner.stderr.log", artifact_paths)
        self.assertNotIn("report.json", artifact_paths)
        self.assertTrue(self.audit_terminal(output)["passed"])

    def test_source_pin_mismatch_is_stop_before_child(self):
        marker = self.root / "must-not-run"
        bad_pins = {"protocol": {"path": PINS["evaluator"]["path"],
                                  "sha256": "0" * 64}}
        script = f"from pathlib import Path; Path({str(marker)!r}).write_text('ran')"
        result, output = self.supervise_at("source-mismatch", process_command(script),
                                           pins=bad_pins)
        self.assertEqual(result["status"], "STOP")
        self.assertEqual(marker.exists(), False)
        terminal = json.loads((output / REPORT_NAME).read_text(encoding="utf-8"))
        self.assertEqual(terminal["reason_code"], "STOP_SOURCE_PIN_PREFLIGHT")
        self.assertFalse(terminal["runner_started"])
        self.assertTrue(self.audit_terminal(output)["passed"])

    def test_unlaunchable_child_is_stop_not_task_failure(self):
        result, output = self.supervise_at("launch-failure", [str(self.root / "absent.exe")])
        self.assertEqual(result["status"], "STOP")
        terminal = json.loads((output / REPORT_NAME).read_text(encoding="utf-8"))
        self.assertEqual(terminal["reason_code"], "STOP_RUNNER_LAUNCH")
        self.assertFalse(terminal["runner_started"])
        self.assertTrue(self.audit_terminal(output)["passed"])

    def test_failure_text_never_promotes_runner_exit_to_reject(self):
        script = "import sys; print('unsafe correctness failure', file=sys.stderr); raise SystemExit(2)"
        result, output = self.supervise_at("exit-nonzero", process_command(script))
        terminal = json.loads((output / REPORT_NAME).read_text(encoding="utf-8"))
        self.assertEqual(result["status"], "HOLD")
        self.assertEqual(terminal["disposition"], "HOLD")
        self.assertTrue(self.audit_terminal(output)["passed"])

    def test_zero_exit_without_report_is_hold(self):
        result, output = self.supervise_at("missing-report", process_command("pass"))
        self.assertEqual(result["status"], "HOLD")
        terminal = json.loads((output / REPORT_NAME).read_text(encoding="utf-8"))
        self.assertEqual(terminal["reason_code"], "HOLD_RUN_REPORT_MISSING")
        self.assertTrue(self.audit_terminal(output)["passed"])

    def test_valid_report_and_independent_audit_are_left_unmodified(self):
        for disposition in ("RETAIN", "HOLD", "REJECT"):
            runner = (
                "import json; from pathlib import Path; "
                "Path('report.json').write_text(json.dumps({'schema':'integrated_efficiency_live_report_v1',"
                f"'evaluation':{{'disposition':{disposition!r}}}}}))"
            )
            auditor = (
                "import json; from pathlib import Path; "
                f"Path('audit.json').write_text(json.dumps({{'passed':True,'disposition':{disposition!r},'errors':[]}}))"
            )
            result, output = self.supervise_at("success-" + disposition,
                                               process_command(runner),
                                               process_command(auditor))
            self.assertEqual(result["status"], "AUDITED")
            self.assertEqual(result["scientific_disposition"], disposition)
            self.assertFalse((output / REPORT_NAME).exists())
            self.assertEqual(json.loads((output / "report.json").read_text())["evaluation"]["disposition"],
                             disposition)

    def test_disagreeing_audit_disposition_yields_hold(self):
        runner = (
            "import json; from pathlib import Path; "
            "Path('report.json').write_text(json.dumps({'schema':'integrated_efficiency_live_report_v1',"
            "'evaluation':{'disposition':'RETAIN'}}))"
        )
        auditor = (
            "import json; from pathlib import Path; "
            "Path('audit.json').write_text(json.dumps({'passed':True,'disposition':'REJECT','errors':[]}))"
        )
        result, output = self.supervise_at("audit-mismatch", process_command(runner),
                                           process_command(auditor))
        self.assertEqual(result["status"], "HOLD")
        terminal = json.loads((output / REPORT_NAME).read_text(encoding="utf-8"))
        self.assertEqual(terminal["reason_code"], "HOLD_AUDIT_DISPOSITION_OR_REPORT_INVALID")
        self.assertTrue(self.audit_terminal(output)["passed"])

    def test_existing_report_is_never_overwritten(self):
        output = self.root / "existing"
        output.mkdir()
        path = output / REPORT_NAME
        original = b"preserve this prior record\n"
        path.write_bytes(original)
        with self.assertRaises(FileExistsError):
            supervise(process_command("pass"), process_command("pass"), output, PINS,
                      allocation_id="ISSUE3311-TERMINATION-REPORT-20260928-01")
        self.assertEqual(path.read_bytes(), original)

    def test_existing_complete_output_is_preserved_and_not_reused(self):
        output = self.root / "stale-output"
        output.mkdir()
        old_report = output / "report.json"
        original = b"old result must remain byte-identical\n"
        old_report.write_bytes(original)
        marker = output / "must-not-run"
        script = f"from pathlib import Path; Path({str(marker)!r}).write_text('ran')"
        result = supervise(process_command(script), process_command("pass"), output, PINS,
                           allocation_id="ISSUE3311-TERMINATION-REPORT-20260928-01")
        self.assertEqual(result["status"], "STOP")
        self.assertFalse(marker.exists())
        self.assertEqual(old_report.read_bytes(), original)
        terminal = json.loads((output / REPORT_NAME).read_text(encoding="utf-8"))
        self.assertEqual(terminal["reason_code"], "STOP_OUTPUT_PATH_ALREADY_PRESENT")
        self.assertTrue(self.audit_terminal(output)["passed"])

    def test_raw_audit_rejects_artifact_mutation(self):
        result, output = self.supervise_at("tamper", process_command("raise SystemExit(1)"))
        self.assertEqual(result["status"], "HOLD")
        (output / "runner.stderr.log").write_text("tampered\n", encoding="utf-8")
        completed = subprocess.run(
            [sys.executable, str(HERE / "audit_termination_report.py"),
             str(output / REPORT_NAME)], capture_output=True, text=True, check=False)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("artifact digest mismatch", completed.stdout)

    def test_raw_audit_rejects_path_traversal(self):
        result, output = self.supervise_at("path", process_command("raise SystemExit(1)"))
        self.assertEqual(result["status"], "HOLD")
        report_path = output / REPORT_NAME
        terminal = json.loads(report_path.read_text(encoding="utf-8"))
        terminal["artifacts"].append({"path": "../outside", "size_bytes": 0,
                                      "sha256": "0" * 64})
        report_path.write_text(json.dumps(terminal), encoding="utf-8")
        completed = subprocess.run(
            [sys.executable, str(HERE / "audit_termination_report.py"), str(report_path)],
            capture_output=True, text=True, check=False)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("artifact path must be unique and relative", completed.stdout)

    def test_base_runner_evaluates_before_writing_final_report(self):
        import ast

        source = (LIVE / "run_integrated_efficiency_live_v1.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        main = next(node for node in tree.body
                    if isinstance(node, ast.FunctionDef) and node.name == "main")
        evaluate_line = next(node.lineno for node in main.body
                             if isinstance(node, ast.Assign)
                             and isinstance(node.value, ast.Call)
                             and isinstance(node.value.func, ast.Name)
                             and node.value.func.id == "evaluate")
        report_dump_line = next(node.lineno for node in ast.walk(main)
                                if isinstance(node, ast.Call)
                                and isinstance(node.func, ast.Name)
                                and node.func.id == "dump"
                                and node.args and isinstance(node.args[0], ast.BinOp)
                                and isinstance(node.args[0].right, ast.Constant)
                                and node.args[0].right.value == "report.json")
        self.assertGreater(report_dump_line, evaluate_line)


if __name__ == "__main__":
    unittest.main(verbosity=2)
