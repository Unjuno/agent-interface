"""Audit the matched Chromium scoped-target-handle pair."""
import hashlib
import json
from pathlib import Path
from urllib.parse import parse_qs

from PIL import Image

from audit_local_visual_barrier_v1 import Decoder, Frame


HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/chromium-target-handle-pair-01"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def replay(root):
    events = [json.loads(line) for line in
              (root / "runtime/events.jsonl").read_text(encoding="utf-8").splitlines()]
    observations = [row for row in events if row.get("event") == "observation"]
    decoder = Decoder("live-control")
    for index, observation in enumerate(observations, 1):
        frame = decoder.accept((root / "runtime" / f"{index:03d}.ait").read_bytes())
        with Image.open(root / "runtime" / Path(observation["image"]).name) as opened:
            image = opened.convert("RGB")
        assert frame == Frame(image.width, image.height, image.mode, image.tobytes())
    return events, len(observations)


def main():
    plan = read(ROOT / "preregistration.json")
    for name, digest in plan["sources"].items():
        assert sha(HERE / name) == digest, name
    report = read(ROOT / "report.json")
    assert report["passed"] is True
    assert [case["name"] for case in report["cases"]] == plan["execution_order"]
    cases = {case["name"]: case for case in report["cases"]}
    positive = cases["positive"]
    negative = cases["changed-target"]
    assert positive == read(ROOT / "positive/result.json")
    assert negative == read(ROOT / "changed-target/result.json")
    for case in cases.values():
        before = case["surface_move"]["before"]["geometry"]
        after = case["surface_move"]["after"]["geometry"]
        delta = [after[0] - before[0], after[1] - before[1]]
        assert delta == case["revalidation"].get("binding_translation", delta)
        assert case["fresh_after_move"]["pointer_binding"]["geometry"] == after
        assert case["minted"]["status"] == "VALID"
        action = case["click_program"][0]
        assert set(action) == {"op", "target_handle", "offset", "button", "duration_ms"}
        assert "x" not in action and "coordinate_frame" not in action
        assert case["terminal"]["release"]["verified"] is True
        assert case["bridge_exit_code"] == 0
    resolved = positive["revalidation"]
    assert resolved["status"] == "REVALIDATED" and resolved["eligible"] is True
    delta = resolved["binding_translation"]
    assert resolved["observed_box"] == [250 + delta[0], 234 + delta[1], 42, 18]
    assert resolved["point"] == [270 + delta[0], 243 + delta[1]] == [290, 251]
    assert [(row["operation"], row["payload"]) for row in positive["pointer_admissions"]] == [
        ("move", {"x": 290, "y": 251}), ("button_down", 1)]
    assert positive["terminal"]["status"] == "completed"
    assert positive["independent_evaluation"]["success"] is True
    assert positive["actual"] == {"value": ["t991005"]}
    assert parse_qs((ROOT / "positive/runtime/submitted.txt").read_text()) == positive["actual"]
    assert positive["action_to_first_useful_feedback_ms"] == 60.016298
    assert positive["action_to_semantic_completion_ms"] == 192.643368
    assert negative["revalidation"]["status"] == "MISSING"
    assert negative["revalidation"]["reason"] == "region_pixels_missing"
    assert negative["pointer_admissions"] == []
    assert negative["terminal"]["status"] == "needs_decision"
    assert negative["terminal"]["steps_completed"] == 0
    assert negative["independent_evaluation"]["success"] is False
    assert negative["actual"] == {}
    assert not (ROOT / "changed-target/runtime/submitted.txt").exists()
    positive_events, positive_frames = replay(ROOT / "positive")
    negative_events, negative_frames = replay(ROOT / "changed-target")
    action = negative["terminal"]["id"]
    action_events = [row for row in negative_events if row.get("id") == action]
    assert not [row for row in action_events if row.get("event") == "pointer_admission"]
    assert len([row for row in action_events if row.get("event") == "target_handle_refused"]) == 1
    assert len([row for row in positive_events
                if row.get("event") == "target_handle_revalidated" and
                row.get("id") == positive["terminal"]["id"]]) == 1
    audit = {"audit_passed": True, "pair_passed": True,
        "positive": {"status": resolved["status"], "binding_translation": delta,
            "resolved_point": resolved["point"],
            "pointer_admissions": len(positive["pointer_admissions"]),
            "independent_task_success": True,
            "action_to_first_useful_feedback_ms": positive["action_to_first_useful_feedback_ms"],
            "action_to_semantic_completion_ms": positive["action_to_semantic_completion_ms"],
            "click_submit_to_return_ms": positive["click_submit_to_return_ms"],
            "durable_calls": positive["durable_calls"], "exact_frames": positive_frames},
        "changed_target": {"status": negative["revalidation"]["status"],
            "pointer_admissions": 0, "terminal_status": negative["terminal"]["status"],
            "independent_task_success": False, "submitted_file_present": False,
            "click_submit_to_return_ms": negative["click_submit_to_return_ms"],
            "durable_calls": negative["durable_calls"], "exact_frames": negative_frames},
        "decision": "RETAIN_SCOPED_TARGET_HANDLE_FOR_MATCHED_CROSS-DOMAIN_REPLICATION",
        "scope": report["scope"]}
    (ROOT / "audit.json").write_text(json.dumps(audit, indent=2) + "\n",
                                      encoding="utf-8", newline="\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
