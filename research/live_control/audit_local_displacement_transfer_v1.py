"""Audit failed and successful model-authored displacement transfers."""
import hashlib
import json
from pathlib import Path

from audit_local_displacement_x11_v1 import audit_case


HERE = Path(__file__).resolve().parent


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    first = HERE / "results/local-displacement-transfer-01"
    first_plan = read(first / "preregistration.json")
    first_failure = read(first / "failure.json")
    assert first_plan["status"] == "preregistered_before_fresh_x11_execution"
    assert first_failure["status"] == "failed_before_input"
    assert first_failure["input_issued"] is False

    second = HERE / "results/local-displacement-transfer-02"
    second_failure = read(second / "failure.json")
    assert second_failure["partial"]["postcondition"] == "target_not_reached"
    assert second_failure["partial"]["save_started"] is False
    assert second_failure["target"]["owner_release_reason"] == "focus_changed"
    assert second_failure["target"]["postcondition_reached"] is False
    target_v2_events = [json.loads(line) for line in (second / "target/events.jsonl").read_text().splitlines()]
    assert any(row.get("event") == "terminal" and row["status"] == "needs_decision"
               and row["release"]["verified"] is True for row in target_v2_events)
    assert not any(row.get("event") == "local_displacement_postcondition" for row in target_v2_events)

    root = HERE / "results/local-displacement-transfer-03"
    plan = read(root / "preregistration.json")
    for name, expected in plan["sources"].items():
        assert sha(HERE / name) == expected, name
    assert sha(HERE / plan["authored_source_relative"]) == plan["authored_source_sha256"]
    assert sha(root / "authored-postcondition.json") == plan["authored_output_sha256"]
    report = read(root / "report.json")
    assert report["passed"] is True
    assert report["decision"] == "RETAIN_MODEL_AUTHORED_FRESH_TRANSFER;_REPLICATE_BEFORE_PROMOTION"
    target = audit_case(root / "target")
    partial = audit_case(root / "partial")
    assert target["delta"] == [24, 0]
    assert target["outcome"]["reason"] == "met" and 4 in target["steps_started"]
    assert abs((target["saved_x"] - 50) * 1.18 - 24) <= 1
    assert partial["delta"] == [20, 0]
    assert partial["outcome"]["reason"] == "target_not_reached" and 4 not in partial["steps_started"]
    assert partial["saved_x"] == 50
    assert target["terminal"]["release"]["verified"] is True
    assert partial["terminal"]["release"]["verified"] is True
    source_sha = sha(root / "target/001.png")
    assert source_sha == sha(root / "partial/001.png")
    audit = {
        "audit_passed": True,
        "v1": {"failed_before_input": True, "reason": "cross-OS absolute path"},
        "v2": {"partial_passed": True, "target_focus_interrupted": True,
               "target_release_verified": True, "packaging_failure_retained": True},
        "v3": {
            "order": plan["order"], "authored_condition_unchanged": True,
            "fresh_sources_identical": True, "fresh_source_sha256": source_sha,
            "target_delta": target["delta"], "target_condition": target["outcome"]["reason"],
            "target_save_started": True, "target_saved_svg_within_one_px": True,
            "partial_delta": partial["delta"], "partial_condition": partial["outcome"]["reason"],
            "partial_save_started": False,
            "exact_frames": target["exact_frames"] + partial["exact_frames"],
            "sample_spans_ms": [target["outcome"]["sample_span_ms"],
                                partial["outcome"]["sample_span_ms"]],
            "all_terminal_releases_verified": True,
        },
        "decision": report["decision"],
        "scope": "one unchanged first Luna-authored patch on one fresh same-task target/partial pair after two retained integration failures; scripted pointer paths; no live model call, speed, token, cross-domain or promotion claim",
        "audit_sha256": sha(Path(__file__)),
    }
    (root / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
