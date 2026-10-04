from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import ast

ROOT = Path(__file__).resolve().parent
ANALYZER_PATH = ROOT / "analyze.py"
AUDITOR_PATH = ROOT / "audit.py"
sys.path.insert(0, str(ROOT / "dependencies"))


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def early_release_trace() -> list[dict]:
    """12 ms ack, last down capture at 30, empty release at 40, then stale captures."""
    return [
        {"event": "command", "received_ns": 0, "command": {"op": "submit", "id": "p1", "steps": [{"op": "hold", "keys": ["KEY_W"], "duration_ms": 100}]}},
        {"event": "step_started", "id": "p1", "step": 0, "operation": "hold", "issued_ns": 10_000_000},
        {"event": "input_admission", "id": "p1", "step": 0, "key": "KEY_W", "admitted_ns": 11_000_000, "input_ack_ns": 12_000_000},
        {"event": "keys_held", "id": "p1", "step": 0, "keys": ["KEY_W"], "input_ack_ns": 12_000_000},
        {"event": "observation", "id": "p1", "step": 0, "capture_ns": 30_000_000},
        {"event": "input_released", "id": "p1", "owner_release": {"verified": True, "keys_down": [], "verified_ns": 40_000_000, "reason": "focus_changed"}},
        {"event": "observation", "id": "p1", "step": 0, "capture_ns": 80_000_000},
        {"event": "observation", "id": "p1", "step": 0, "capture_ns": 90_000_000},
        {"event": "step_completed", "id": "p1", "step": 0, "completed_ns": 100_000_000},
        {"event": "terminal", "id": "p1", "status": "completed", "steps_completed": 1},
    ]


def test_completed_hold_uses_first_verified_early_release_as_bound(tmp_path):
    frozen_v4 = load("frozen_fulltrace_v4", ROOT / "dependencies" / "analyze_map01_held_input_occupancy_fulltrace_v4.py")
    analyzer = load("early_release_candidate", ANALYZER_PATH)
    auditor = load("early_release_auditor", AUDITOR_PATH)
    old = frozen_v4.reconstruct_holds(early_release_trace())[0]
    assert (old["confirmed_any_key_held_until_ns"], old["released_by_ns"],
            old["physical_any_key_occupancy_lower_ms"],
            old["physical_any_key_occupancy_upper_ms"]) == (80_000_000, 90_000_000, 68.0, 79.0)
    run_root = tmp_path / "run"
    (run_root / "runtime").mkdir(parents=True)
    (run_root / "report.json").write_text(
        '{"decisions":[{"iteration":1,"controller_model_started_ns":0,'
        '"controller_model_ended_ns":100000000,"cover_program_ids":["p1"]}]}',
        encoding="utf-8")
    import json
    events = early_release_trace()
    (run_root / "runtime" / "events.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in events), encoding="utf-8")
    v7 = load("published_v7_for_async_release", ROOT / "dependencies" / "analyze_map01_held_input_occupancy_fulltrace_v7.py")
    v7_auditor = load("published_v7_auditor_for_async_release", ROOT / "dependencies" / "audit_map01_held_input_occupancy_fulltrace_v7.py")
    published = v7.analyze(run_root)
    published_path = tmp_path / "published-v7.json"
    published_path.write_text(json.dumps(published), encoding="utf-8")
    assert published["holds"][0]["physical_any_key_occupancy_lower_ms"] == 18.0
    assert v7_auditor.audit(run_root, published_path)["raw_reconstruction"] == "PASS"
    output = analyzer.analyze(run_root)
    row = output["holds"][0]
    assert row["released_by_ns"] == 40_000_000
    assert row["confirmed_any_key_held_until_ns"] == 12_000_000
    assert row["physical_any_key_occupancy_lower_ms"] == 0.0
    assert row["physical_any_key_occupancy_upper_ms"] == 29.0
    candidate_path = tmp_path / "candidate.json"
    candidate_path.write_text(json.dumps(output), encoding="utf-8")
    assert auditor.audit(run_root, candidate_path)["raw_reconstruction"] == "PASS"

    corrupted = json.loads(candidate_path.read_text(encoding="utf-8"))
    corrupted["holds"][0]["released_by_ns"] = 90_000_000
    candidate_path.write_text(json.dumps(corrupted), encoding="utf-8")
    try:
        auditor.audit(run_root, candidate_path)
    except AssertionError:
        pass
    else:
        raise AssertionError("independent raw auditor accepted the stale post-release bound")


def test_fails_closed_when_acknowledgement_crosses_verified_release():
    analyzer = load("early_release_candidate_late_ack", ANALYZER_PATH)
    events = early_release_trace()
    next(row for row in events if row["event"] == "input_admission")["input_ack_ns"] = 50_000_000
    try:
        analyzer.reconstruct_holds(events)
    except AssertionError as exc:
        assert "bounds" in str(exc) or "later admission/ack" in str(exc)
    else:
        raise AssertionError("candidate accepted an acknowledgement after verified empty release")


def test_completed_hold_is_corrected_even_when_a_later_step_is_cancelled(tmp_path):
    import json
    analyzer = load("early_release_candidate_later_cancel", ANALYZER_PATH)
    auditor = load("early_release_auditor_later_cancel", AUDITOR_PATH)
    v7 = load("published_v7_later_cancel", ROOT / "dependencies" / "analyze_map01_held_input_occupancy_fulltrace_v7.py")
    v7_auditor = load("published_v7_auditor_later_cancel", ROOT / "dependencies" / "audit_map01_held_input_occupancy_fulltrace_v7.py")
    events = early_release_trace()
    events[0]["command"]["steps"].append({"op": "wait", "duration_ms": 200})
    events.insert(-1, {"event": "step_started", "id": "p1", "step": 1,
                       "operation": "wait", "issued_ns": 101_000_000})
    events.insert(-1, {"event": "command", "received_ns": 102_000_000,
                       "command": {"op": "cancel", "id": "p1"}})
    events[-1] = {"event": "terminal", "id": "p1", "status": "cancelled",
                  "steps_completed": 1,
                  "interruption": {"verified": True, "reason": "cancelled",
                                   "verified_ns": 110_000_000, "keys_down": [],
                                   "buttons_down": []},
                  "release": {"verified": True, "verified_ns": 110_000_000,
                              "keys_down": [], "buttons_down": []}}
    run_root = tmp_path / "later-cancel"
    (run_root / "runtime").mkdir(parents=True)
    (run_root / "report.json").write_text(
        '{"decisions":[{"iteration":1,"controller_model_started_ns":0,'
        '"controller_model_ended_ns":100000000,"cover_program_ids":["p1"]}]}',
        encoding="utf-8")
    (run_root / "runtime" / "events.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in events), encoding="utf-8")
    published = v7.analyze(run_root)
    published_path = tmp_path / "published-v7.json"
    published_path.write_text(json.dumps(published), encoding="utf-8")
    assert published["holds"][0]["released_by_ns"] == 90_000_000
    try:
        v7_auditor.audit(run_root, published_path)
    except AssertionError:
        pass
    else:
        raise AssertionError("V7 raw auditor accepted a missed completed hold")
    output = analyzer.analyze(run_root)
    hold = output["holds"][0]
    assert hold["terminal_status"] == "cancelled"
    assert hold["released_by_ns"] == 40_000_000
    assert hold["physical_any_key_occupancy_lower_ms"] == 0.0
    assert hold["physical_any_key_occupancy_upper_ms"] == 29.0
    output_path = tmp_path / "candidate.json"
    output_path.write_text(json.dumps(output), encoding="utf-8")
    assert auditor.audit(run_root, output_path)["raw_reconstruction"] == "PASS"


def test_current_owner_records_verified_timestamp_after_release_sync():
    source = (ROOT / "dependencies" / "input_owner_v12.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    release = next(node for node in ast.walk(tree)
                   if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "release")
    release_sync = next(node for node in ast.walk(release)
                        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                        and node.func.attr == "sync")
    verified_timestamp = next(node for node in ast.walk(release)
                              if isinstance(node, ast.keyword) and node.arg == "verified_ns")
    assert release_sync.lineno < verified_timestamp.value.lineno


def test_v7_candidate_and_auditor_accept_a_later_key_admission_after_early_release(tmp_path):
    import json
    v7 = load("published_v7_candidate", ROOT / "dependencies" / "analyze_map01_held_input_occupancy_fulltrace_v7.py")
    audit_v7 = load("published_v7_auditor", ROOT / "dependencies" / "audit_map01_held_input_occupancy_fulltrace_v7.py")
    events = [
        {"event": "command", "received_ns": 1_000_000, "command": {"op": "submit", "id": "p2", "steps": [{"op": "hold", "keys": ["KEY_W", "KEY_D"], "duration_ms": 100}]}},
        {"event": "step_started", "id": "p2", "step": 0, "operation": "hold", "issued_ns": 10_000_000},
        {"event": "input_admission", "id": "p2", "step": 0, "key": "KEY_W", "admitted_ns": 11_000_000, "input_ack_ns": 12_000_000},
        {"event": "observation", "id": "p2", "step": 0, "capture_ns": 30_000_000},
        {"event": "input_released", "id": "p2", "owner_release": {"verified": True, "keys_down": [], "verified_ns": 40_000_000, "reason": "focus_changed"}},
        {"event": "input_admission", "id": "p2", "step": 0, "key": "KEY_D", "admitted_ns": 50_000_000, "input_ack_ns": 55_000_000},
        {"event": "keys_held", "id": "p2", "step": 0, "keys": ["KEY_W", "KEY_D"], "input_ack_ns": 55_000_000},
        {"event": "observation", "id": "p2", "step": 0, "capture_ns": 80_000_000},
        {"event": "observation", "id": "p2", "step": 0, "capture_ns": 90_000_000},
        {"event": "step_completed", "id": "p2", "step": 0, "completed_ns": 100_000_000},
        {"event": "terminal", "id": "p2", "status": "completed", "steps_completed": 1},
    ]
    run_root = tmp_path / "late-admission"
    (run_root / "runtime").mkdir(parents=True)
    (run_root / "report.json").write_text(
        '{"decisions":[{"iteration":1,"controller_model_started_ns":0,'
        '"controller_model_ended_ns":100000000,"cover_program_ids":["p2"]}]}', encoding="utf-8")
    (run_root / "runtime" / "events.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in events), encoding="utf-8")
    stale = v7.analyze(run_root)
    stale_path = tmp_path / "v7.json"
    stale_path.write_text(json.dumps(stale), encoding="utf-8")
    assert stale["holds"][0]["released_by_ns"] == 40_000_000
    assert stale["holds"][0]["physical_any_key_occupancy_upper_ms"] == 29.0
    assert audit_v7.audit(run_root, stale_path)["raw_reconstruction"] == "PASS"
    candidate = load("early_release_candidate_late_key", ANALYZER_PATH)
    try:
        candidate.reconstruct_holds(events)
    except AssertionError as exc:
        assert "later admission/ack" in str(exc)
    else:
        raise AssertionError("candidate accepted a second key admitted after the release cap")
