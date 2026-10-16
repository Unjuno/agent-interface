"""Independent audit of v2's preserved visually-flat pre-input refusal."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/compiled-gui-interface-live-02"


def read(path): return json.loads(path.read_text(encoding="utf-8"))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    plan = read(ROOT / "preregistration.json")
    for name, digest in plan["sources"].items():
        assert sha(HERE / name) == digest, name
    report = read(ROOT / "report.json")
    assert report["passed"] is False
    assert report["decision"] == "HOLD_COMPILED_INTERFACE_AND_PRESERVE_FAILURE"
    assert report["preflight"]["accepted"] is True
    assert report["preflight"]["model_calls"] == 0
    assert report["actual_performed_model_usage_totals"] == {
        "input_tokens": 18792, "cached_input_tokens": 0,
        "cache_write_input_tokens": 0, "output_tokens": 350,
        "reasoning_output_tokens": 120}
    boxes = plan["common"]["independent_point_boxes"]

    def inside(point, box):
        return box[0] <= point[0] < box[0] + box[2] and box[1] <= point[1] < box[1] + box[3]

    for case in report["cases"]:
        grounding = case["grounding_model"]["grounding"]
        assert inside(grounding["field_point"], boxes["field"])
        assert inside(grounding["submit_point"], boxes["submit"])
        assert case["adaptive"]["outcome"] == "SAFE_STOP"
        assert case["adaptive"]["reason"] == "unavailable"
        assert case["adaptive"]["accounting"]["attempted_calls"] == 1
        assert case["mint"]["minted"] == []
        assert len(case["mint"]["programs"]) == 1
        terminal = case["mint"]["programs"][0]["terminal"]
        assert terminal["status"] == "failed"
        assert terminal["error"] == "ValueError('visually flat target region refused')"
        assert terminal["release"]["verified"] is True
        assert case["compiled_runtime"] is None and case["action_records"] == []
        assert case["independent_evaluation"]["success"] is False
        assert case["actual"] == {} and case["bridge_exit_code"] == 0
        events = [json.loads(line) for line in (ROOT /
            f"{case['index']}-{case['name']}/runtime/events.jsonl").read_text(
                encoding="utf-8").splitlines()]
        assert not any(row.get("event") in {"target_handle_minted_from_point",
                                             "pointer_admission"} for row in events)
    audit = {"passed": True, "formal_study_passed": False, "cases": 2,
        "semantic_grounding_points_correct": "2/2", "compiled_target_actions": 0,
        "independent_task_success": "0/2", "fresh_model_calls": 2,
        "fresh_model_usage_totals": report["actual_performed_model_usage_totals"],
        "failure": "field point 24x14 region excludes field border and is visually flat",
        "decision": "HOLD_V2_AND_ADVANCE_TEXTURED_FIELD_REGION_FIX",
        "scope": "independent audit of frozen v2; no GUI/model rerun"}
    (ROOT / "audit.json").write_text(json.dumps(audit, indent=2) + "\n",
                                      encoding="utf-8", newline="\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__": main()
