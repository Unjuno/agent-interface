"""Independent verifier for the V39 measurement-session dispatch result."""
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def read_pinned(main, path, expected_blob):
    blob = subprocess.check_output(["git", "-C", str(REPO), "rev-parse", f"{main}:{path}"], text=True).strip()
    if blob != expected_blob:
        raise ValueError(f"blob mismatch: {path}")
    return subprocess.check_output(["git", "-C", str(REPO), "show", f"{main}:{path}"])


def audit_result(result):
    failures = []
    try:
        freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
        if result.get("schema") != "v39-measurement-dispatch-a01-result-v1":
            failures.append("result_schema")
        if result.get("main_commit") != freeze["main_commit"]:
            failures.append("main_commit")
        expected_modes = [
            {"mode": "default", "measurement_session": False, "session": "session_map01_v12.py",
             "report_label": "v12_default", "command_arguments_preserved": True},
            {"mode": "measurement", "measurement_session": True, "session": "session_map01_v15.py",
             "report_label": "v15_scorer_only_per_key_release", "command_arguments_preserved": True},
        ]
        if result.get("modes") != expected_modes:
            failures.append("mode_path_label_matrix")
        expected_chain = {
            "session_path": "research/doom/session_map01_v15.py",
            "release_backend_path": "research/doom/doom_owner_thread_release_batch_backend_v1.py",
            "typed_backend_path": "research/doom/doom_typed_release_backend_v2.py",
            "transition_owner_path": "research/live_control/input_transition_owner_v4.py",
            "input_owner_path": "research/live_control/input_owner_v12.py",
            "per_key_fields": ["key_release_attempts", "key_release_intervals_ns"],
        }
        if result.get("instrumentation_chain") != expected_chain:
            failures.append("instrumentation_chain")
        main = freeze["main_commit"]
        controller = read_pinned(main, "research/doom/map01_overlap_controller_v39.py", freeze["sources"]["research/doom/map01_overlap_controller_v39.py"]).decode("utf-8")
        session = read_pinned(main, expected_chain["session_path"], freeze["sources"][expected_chain["session_path"]]).decode("utf-8")
        release = read_pinned(main, expected_chain["release_backend_path"], freeze["sources"][expected_chain["release_backend_path"]]).decode("utf-8")
        typed = read_pinned(main, expected_chain["typed_backend_path"], freeze["sources"][expected_chain["typed_backend_path"]]).decode("utf-8")
        transition = read_pinned(main, expected_chain["transition_owner_path"], freeze["sources"][expected_chain["transition_owner_path"]]).decode("utf-8")
        owner = read_pinned(main, expected_chain["input_owner_path"], freeze["sources"][expected_chain["input_owner_path"]]).decode("utf-8")
        if '"--measurement-session"' not in controller or "measurement_session" not in controller:
            failures.append("measurement_flag_source")
        if "session_map01_v15.py" not in controller or "v15_scorer_only_per_key_release" not in controller:
            failures.append("measurement_dispatch_source")
        if "doom_owner_thread_release_batch_backend_v1" not in session:
            failures.append("v15_backend_source")
        if "doom_typed_release_backend_v2" not in release or "input_transition_owner_v4" not in release:
            failures.append("release_composition_source")
        if "input_owner_v12" not in transition:
            failures.append("transition_owner_source")
        if any(field not in owner for field in expected_chain["per_key_fields"]):
            failures.append("per_key_source_fields")
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, subprocess.CalledProcessError, SyntaxError):
        failures.append("frozen_source_readback")
    return {"schema": "v39-measurement-dispatch-a01-audit-v1",
            "status": "PASS_DISPATCH_CONSTRUCTION" if not failures else "FAIL_DISPATCH_CONSTRUCTION",
            "checks_total": 11, "checks_passed": 11 - len(failures), "failed_checks": failures}


if __name__ == "__main__":
    result = json.loads((HERE / "RESULT.json").read_text(encoding="utf-8"))
    print(json.dumps(audit_result(result), sort_keys=True))
