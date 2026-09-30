"""Independent raw-only audit for the Issue #2922 setup-only result."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def audit(root: Path, *, rows_override=None, manifest_override=None,
          runner_sources_override=None, package_override=None,
          no_gui_result_override=None, ready_result_override=None,
          fixture_result_override=None) -> list[str]:
    errors: list[str] = []
    package = package_override or root / "research/integration/golden_ipc_source_closure_2922_v1"
    evidence = root / "evidence/ready-gate-01"
    rows = rows_override if rows_override is not None else [
        json.loads(line) for line in (package / "events.jsonl").read_text().splitlines()]
    kinds = [row.get("event") for row in rows]
    if kinds != ["ready", "observation", "command", "independent_evaluation"]:
        errors.append("event sequence/cardinality mismatch")
    ready = rows[0] if rows else {}
    goal = ready.get("goal", {}) if isinstance(ready.get("goal"), dict) else {}
    if ready.get("app") != "chromium" or not str(goal.get("url", "")).startswith("http://127.0.0.1:"):
        errors.append("ready identity or private endpoint mismatch")
    if goal.get("setup_readiness_captures") != 0:
        errors.append("unexpected setup-readiness capture count")
    observation = rows[1] if len(rows) > 1 else {}
    if observation.get("exact") is not True or observation.get("semantic_completion") != "unknown":
        errors.append("initial observation not exact/unknown")
    windows = observation.get("context", [])
    if not any("about:blank" in str(item) for item in windows):
        errors.append("startup observation is not the frozen about:blank state")
    command = rows[2].get("command", {}) if len(rows) > 2 else {}
    if command != {"op": "finish"}:
        errors.append("non-finish command or task submission present")
    if any(str(row.get("event", "")).startswith("input_") or row.get("event") == "action_admission" for row in rows):
        errors.append("input/action event present")
    evaluation = rows[3] if len(rows) > 3 else {}
    if evaluation.get("success") is not False or "FileNotFoundError" not in str(evaluation.get("actual")):
        errors.append("zero-action evaluation disposition changed")

    no_gui_result = no_gui_result_override if no_gui_result_override is not None else json.loads(
        (package / "NO_GUI_IMPORT_RESULT.json").read_text())
    if (no_gui_result.get("schema") != "issue2922_no_gui_import_probe_v1"
            or no_gui_result.get("disposition") != "PASS_IMPORT_ONLY"
            or no_gui_result.get("exit_code") != 0
            or no_gui_result.get("stdout_terminal_marker") != "IMPORT_OK"
            or no_gui_result.get("stderr") != ""
            or no_gui_result.get("xvfb_invoked") is not False
            or no_gui_result.get("chromium_invoked") is not False
            or no_gui_result.get("task_effect") != "not tested"):
        errors.append("no-GUI import-only result contract mismatch")

    ready_result = ready_result_override if ready_result_override is not None else json.loads(
        (package / "READY_GATE_03_RESULT.json").read_text())
    ready_package = package / "ready_gate_03"
    ready_rows = [json.loads(line) for line in (ready_package / "events.jsonl").read_text().splitlines()]
    if [row.get("event") for row in ready_rows] != [
            "ready", "observation", "command", "independent_evaluation"]:
        errors.append("direct-Xvfb event sequence/cardinality mismatch")
    ready_event = ready_rows[0] if ready_rows else {}
    ready_goal = ready_event.get("goal", {}) if isinstance(ready_event.get("goal"), dict) else {}
    if (ready_event.get("app") != "chromium"
            or not str(ready_goal.get("url", "")).startswith("http://127.0.0.1:")
            or ready_goal.get("setup_readiness_captures") != 0):
        errors.append("direct-Xvfb ready identity mismatch")
    ready_observation = ready_rows[1] if len(ready_rows) > 1 else {}
    if (ready_observation.get("exact") is not True
            or ready_observation.get("semantic_completion") != "unknown"
            or not any("about:blank" in str(item)
                       for item in ready_observation.get("context", []))):
        errors.append("direct-Xvfb initial observation mismatch")
    if (len(ready_rows) < 4
            or ready_rows[2].get("command") != {"op": "finish"}
            or ready_rows[3].get("success") is not False
            or "FileNotFoundError" not in str(ready_rows[3].get("actual"))):
        errors.append("direct-Xvfb finish-only evaluation mismatch")
    if (ready_result.get("schema") != "issue2922_direct_xvfb_ready_probe_v1"
            or ready_result.get("disposition") != "PASS_PRETASK_READY_ONLY"
            or ready_result.get("manual_ready_signal_interventions") != 0
            or ready_result.get("session_ready_events") != 1
            or ready_result.get("container_exit_code") != 0
            or ready_result.get("task_effect") != "not tested; evaluator reports missing output"
            or ready_result.get("predecessor_setup_error", {}).get("session_started") is not False):
        errors.append("direct-Xvfb result contract mismatch")
    for filename, expected_sha in ready_result.get("artifact_sha256", {}).items():
        artifact = (ready_package / filename).resolve()
        if not artifact.is_file() or hashlib.sha256(artifact.read_bytes()).hexdigest() != expected_sha:
            errors.append(f"direct-Xvfb artifact digest mismatch: {filename}")

    fixture_result = fixture_result_override if fixture_result_override is not None else json.loads(
        (package / "FIXTURE_GET_HOST_RESULT.json").read_text())
    if (fixture_result.get("schema") != "issue2922_fixture_get_host_component_v1"
            or fixture_result.get("disposition") != "PASS_GET_HANDLER_NO_OUTPUT_MUTATION"
            or fixture_result.get("containerized") is not False
            or fixture_result.get("request_method") != "GET"
            or fixture_result.get("http_status") != 200
            or fixture_result.get("output_path_exists_before") is not False
            or fixture_result.get("output_path_exists_after") is not False
            or fixture_result.get("post_requests") != 0
            or fixture_result.get("integrated_session_invoked") is not False
            or fixture_result.get("task_effect") != "not tested"):
        errors.append("host GET component result scope mismatch")
    fixture_source = package / "source_snapshot/research/observation_gating/gui_suite.py"
    if hashlib.sha256(fixture_source.read_bytes()).hexdigest() != fixture_result.get("source_sha256"):
        errors.append("host GET component source digest mismatch")

    manifest = manifest_override if manifest_override is not None else json.loads(
        (package / "SOURCE_MANIFEST.json").read_text())
    runner_sources = runner_sources_override if runner_sources_override is not None else json.loads(
        (package / "sources.json").read_text())
    normalized_manifest_paths = {path.removeprefix("research/") for path in manifest.get("files", {})}
    if normalized_manifest_paths != set(runner_sources):
        errors.append("source manifest denominator mismatch")
    for rel, expected in manifest.get("files", {}).items():
        source = package / "source_snapshot" / Path(rel)
        try:
            data = source.read_bytes()
        except OSError:
            errors.append(f"source missing: {rel}")
            continue
        if hashlib.sha256(data).hexdigest() != expected.get("sha256"):
            errors.append(f"source sha256 mismatch: {rel}")
        if git_blob_sha(data) != expected.get("git_blob"):
            errors.append(f"source git blob mismatch: {rel}")
        if runner_sources.get(rel.removeprefix("research/")) != expected.get("sha256"):
            errors.append(f"runner source receipt mismatch: {rel}")

    image = package / "001.png"
    if not image.is_file() or hashlib.sha256(image.read_bytes()).hexdigest() != (
            "0ad03d3f0636a714b6a75868d8a7d0e1d2aaff09c437e7552a46f2bf316c8bbe"):
        errors.append("initial screenshot missing or hash mismatch")
    return errors


if __name__ == "__main__":
    package = Path(__file__).resolve().parent
    problems = audit(package, package_override=package)
    source_count = len(json.loads((package / "SOURCE_MANIFEST.json").read_text())["files"])
    print(json.dumps({"startup_hold_event_rows": 4, "direct_xvfb_event_rows": 4,
                      "source_files": source_count, "errors": problems,
                      "rung_dispositions": ["HOLD_XVFB_READY_SIGNAL_INTERVENTION",
                                            "PASS_IMPORT_ONLY", "PASS_PRETASK_READY_ONLY",
                                            "PASS_GET_HANDLER_NO_OUTPUT_MUTATION_HOST_COMPONENT_ONLY"],
                      "audit_disposition": "PASS" if not problems else "FAIL_AUDIT"},
                     sort_keys=True))
    raise SystemExit(bool(problems))
