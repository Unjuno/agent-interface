"""Audit the preregistered OpenTTD pre-opened-toolbar fixed-Astra episode."""
import base64
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops

import audit_openttd_matched_v2 as shared

HERE = Path(__file__).resolve().parent
BASE = HERE / "results/timing-envelope-openttd-matched-04"
CLOSED = HERE / "results/timing-envelope-openttd-matched-03/fixed-astra/runtime/001.png"
shared.BASE = BASE


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    prereg = read(BASE / "preregistration.json")
    amendment = read(BASE / "preregistration-amendment.json")
    assert prereg["status"] == "PREREGISTERED_BEFORE_EXECUTION"
    assert prereg["execution_order"] == ["fixed-astra-preopened-road-toolbar"]
    assert amendment["status"] == "AMENDED_BEFORE_EXECUTION"
    assert amendment["scope"].startswith("implementation-only")
    assert amendment["amendment_script_sha256"] == sha(HERE / "amend_openttd_initial_state_v4.py")
    assert (BASE / "preregistration.json").stat().st_mtime_ns < (BASE / "preregistration-amendment.json").stat().st_mtime_ns
    assert (BASE / "preregistration-amendment.json").stat().st_mtime_ns < (BASE / "fixed-astra/model-1/process.json").stat().st_mtime_ns
    task_source = HERE.parent / "openttd_task/interactive_v7.py"
    assert prereg["sources"]["openttd_task/interactive_v7.py"] == amendment["original_source_sha256"]
    frozen = HERE / "frozen_sources" / amendment["original_source_sha256"] / "interactive_v7.py.b64"
    assert hashlib.sha256(base64.b64decode(frozen.read_text().strip())).hexdigest() == amendment["original_source_sha256"]
    assert sha(task_source) == amendment["corrected_source_sha256"]
    for name, digest in prereg["sources"].items():
        if name == "openttd_task/interactive_v7.py":
            continue
        path = HERE.parent / name if name.startswith("openttd_task/") else HERE / name
        shared.source_with_hash(path, digest)

    arm = shared.audit_arm("fixed-astra")
    assert arm["hard_success"] is True
    assert arm["model_turns"][-1]["kind"] == "verify"

    root = BASE / "fixed-astra"
    runtime = root / "runtime"
    initial = read(runtime / "initial-evaluation.json")
    assert initial["setup_click_root"] == [820, 51]
    assert initial["setup_started_ns"] < initial["setup_finished_ns"]
    assert initial["success"] is False
    assert initial["checks"] == {
        "target_owned_roads": False,
        "bidirectional_connections": False,
        "forbidden_row_clear": True,
        "surrounding_road_owner_unchanged": True,
    }
    assert initial["changed_surrounding_tiles"] == []
    before = {
        tile["id"]: (tile["road"], tile["owner"])
        for tile in initial["baseline"]["guard"]
    }
    after = {
        tile["id"]: (tile["road"], tile["owner"])
        for tile in initial["observation"]["guard"]
    }
    assert before == after
    events = [json.loads(line) for line in (runtime / "events.jsonl").read_text().splitlines()]
    ready = events[0]
    assert ready["event"] == "ready"
    assert ready["initial_ui_state"].startswith("road construction toolbar pre-opened")
    assert not any(row["event"] in ("pointer_admission", "input_admission") for row in events[:2])

    with Image.open(runtime / "001.png") as opened:
        current = opened.convert("RGB")
    with Image.open(CLOSED) as opened:
        closed = opened.convert("RGB")
    assert current.size == closed.size == (1280, 800)
    toolbar_box = (690, 60, 1000, 110)
    difference = ImageChops.difference(current.crop(toolbar_box), closed.crop(toolbar_box))
    changed_toolbar_pixels = sum(pixel != (0, 0, 0) for pixel in difference.getdata())
    assert changed_toolbar_pixels > 10000
    closed = read(HERE / "results/timing-envelope-openttd-matched-03/audit.json")["fixed_astra"]
    assert closed["hard_success"] is True
    assert closed["save_sha256"] == arm["save_sha256"]
    assert closed["task"] == arm["task"]
    assert closed["initial_geometry"] == arm["initial_geometry"]
    comparison_keys = [
        "initial_observation_to_semantic_completion_ms",
        "model_wait_total_ms",
        "proposal_to_useful_feedback_total_ms",
        "input_tokens_total",
        "runtime_exact_frames",
        "contact_sheets",
        "durable_calls",
    ]
    contextual_comparison = {
        key: {
            "closed_toolbar": closed[key],
            "preopened_toolbar": arm[key],
            "delta": arm[key] - closed[key],
        }
        for key in comparison_keys
    }
    contextual_comparison["model_turns"] = {
        "closed_toolbar": len(closed["model_turns"]),
        "preopened_toolbar": len(arm["model_turns"]),
        "delta": len(arm["model_turns"]) - len(closed["model_turns"]),
    }

    report = {
        "audit_passed": True,
        "preregistered": True,
        "pre_execution_amendment": True,
        "changed_factor": {
            "initial_ui_state": ready["initial_ui_state"],
            "setup_click_root": initial["setup_click_root"],
            "initial_engine_checks": initial["checks"],
            "changed_toolbar_pixels_vs_closed_control_crop": changed_toolbar_pixels,
            "comparison_crop": list(toolbar_box),
            "closed_control_image_sha256": sha(CLOSED),
        },
        "fixed_astra_preopened_toolbar": arm,
        "contextual_unpaired_comparison": contextual_comparison,
        "scope": (
            "one changed-initial-UI episode on the same canonical task; no general route, "
            "causal speedup, latency distribution, or human comparison"
        ),
        "audit_sha256": sha(Path(__file__)),
        "shared_audit_dependency_sha256": sha(HERE / "audit_openttd_matched_v2.py"),
    }
    (BASE / "audit.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
