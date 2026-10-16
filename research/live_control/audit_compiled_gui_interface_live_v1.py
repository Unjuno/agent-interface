"""Post-hoc audit of the preserved first compiled-interface live failure."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/compiled-gui-interface-live-01"
FIELDS = ("input_tokens", "cached_input_tokens", "cache_write_input_tokens",
          "output_tokens", "reasoning_output_tokens")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    plan = read(ROOT / "preregistration.json")
    assert plan["status"] == "preregistered_before_schema_preflight_and_fresh_gui_execution"
    for name, digest in plan["sources"].items():
        assert sha(HERE / name) == digest, name
    gate = read(ROOT / "preflight/gate-report.json")
    assert gate["accepted"] is True and gate["model_calls"] == 1
    cases = [read(ROOT / "1-changed-target/result.json"),
             read(ROOT / "2-positive/result.json")]
    expected = {"changed-target", "positive"}
    assert {row["name"] for row in cases} == expected
    point_box = plan["common"]["independent_point_boxes"]

    def inside(point, box):
        return (box[0] <= point[0] < box[0] + box[2]
                and box[1] <= point[1] < box[1] + box[3])

    for row in cases:
        grounding = row["grounding_model"]["grounding"]
        assert inside(grounding["field_point"], point_box["field"])
        assert inside(grounding["submit_point"], point_box["submit"])
        assert row["adaptive"]["outcome"] == "CALLER_FAILED"
        assert row["adaptive"]["reason"] == "ValueError('unresolved reply status')"
        assert row["adaptive"]["accounting"]["attempted_calls"] == 1
        assert row["adaptive"]["accounting"]["completed_calls"] == 1
        assert row["mint"] is None and row["compiled_runtime"] is None
        assert row["action_records"] == [] and row["runtime_events"] == []
        assert row["independent_evaluation"]["success"] is False
        assert row["actual"] == {} and row["bridge_exit_code"] == 0
        events = [json.loads(line) for line in
                  (ROOT / f"{row['index']}-{row['name']}/runtime/events.jsonl").read_text(
                      encoding="utf-8").splitlines()]
        rejects = [event for event in events if event.get("event") == "rejected"]
        assert rejects[-1]["reason"] == "at most one target handle may be minted per program"
        assert not any(event.get("event") in {"target_handle_minted_from_point",
                                               "pointer_admission"} for event in events)

    usages = [gate["results"][0]["result"]["usage"]] + [
        row["grounding_model"]["usage"] for row in cases]
    totals = {field: sum(usage[field] for usage in usages) for field in FIELDS}
    assert totals == {"input_tokens": 26755, "cached_input_tokens": 0,
                      "cache_write_input_tokens": 0, "output_tokens": 526,
                      "reasoning_output_tokens": 153}
    result = {
        "passed": True,
        "formal_study_passed": False,
        "cases": 2,
        "semantic_grounding_points_correct": "2/2",
        "compiled_target_actions": 0,
        "independent_task_success": "0/2",
        "actual_model_calls": 3,
        "actual_model_usage_totals": totals,
        "failure": "two handle mint steps batched despite backend one-mint-per-program constraint",
        "runner_reporting_failure": "None compiled_runtime dereferenced after preserved case results",
        "decision": "HOLD_V1_AND_ADVANCE_SEPARATE_MINT_PROGRAM_FIX",
        "scope": "post-hoc audit of preserved fresh v1 results; no GUI or model rerun",
    }
    (ROOT / "posthoc-audit.json").write_text(json.dumps(result, indent=2) + "\n",
                                              encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
