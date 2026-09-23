"""Audit the preregistered seed-991002 OpenTTD geometry transfer."""
import hashlib
import json
from pathlib import Path

import audit_openttd_finish_v3 as finish_v3
import audit_openttd_matched_v2 as shared

HERE = Path(__file__).resolve().parent
BASE = HERE / "results/timing-envelope-openttd-matched-05"
finish_v3.BASE = BASE
finish_v3.shared.BASE = BASE
shared.BASE = BASE

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    prereg = read(BASE / "preregistration.json")
    assert prereg["status"] == "PREREGISTERED_BEFORE_EXECUTION"
    assert prereg["execution_order"] == ["negative-control", "fixed-astra"]
    assert prereg["task_allocation"]["target_tiles"] == [465, 466, 467]
    assert prereg["task_allocation"]["forbidden_tiles"] == [529, 530, 531]
    for name, digest in prereg["sources"].items():
        path = HERE.parent / name if name.startswith("openttd_task/") else HERE / name
        shared.source_with_hash(path, digest)

    negative = finish_v3.audit_negative()
    positive = shared.audit_arm("fixed-astra")
    assert negative["model_calls"] == 0
    assert negative["durable_input_calls"] == 0
    assert negative["independent_checks"] == {
        "target_owned_roads": False,
        "bidirectional_connections": False,
        "forbidden_row_clear": True,
        "surrounding_road_owner_unchanged": True,
    }
    assert positive["hard_success"] is True
    assert negative["save_sha256"] == positive["save_sha256"]
    assert positive["save_sha256"] == prereg["task_allocation"]["save_sha256"]
    assert negative["task"] == positive["task"]

    evaluation = read(BASE / "fixed-astra/runtime/evaluation.json")
    contract = evaluation["contract"]
    assert contract["target"] == prereg["task_allocation"]["target_tiles"]
    assert contract["forbidden"] == prereg["task_allocation"]["forbidden_tiles"]
    assert evaluation["success"] is True
    assert all(evaluation["checks"].values())
    assert evaluation["changed_surrounding_tiles"] == []

    fixture = read(HERE.parent / "openttd_task/results/geometry-01/audit.json")
    assert fixture["audit_passed"] is True
    assert fixture["save_sha256"] == positive["save_sha256"]
    assert fixture["contract"]["target"] == contract["target"]

    typed = [
        read(BASE / f"fixed-astra/typed-{turn}.json")
        for turn in range(1, len(positive["model_turns"]) + 1)
    ]
    drags = [step for proposal in typed for step in proposal.get("steps", []) if step.get("op") == "pointer_drag"]
    assert len(drags) == 1
    prior_drag = read(HERE / "results/timing-envelope-openttd-matched-03/fixed-astra/typed-4.json")["steps"][1]
    assert drags[0]["points"] != prior_drag["points"]

    prior = read(HERE / "results/timing-envelope-openttd-matched-03/audit.json")["fixed_astra"]
    assert prior["hard_success"] is True
    assert prior["save_sha256"] != positive["save_sha256"]
    assert prior["task"] == positive["task"]
    metrics = [
        "initial_observation_to_semantic_completion_ms",
        "model_wait_total_ms",
        "proposal_to_useful_feedback_total_ms",
        "input_tokens_total",
        "runtime_exact_frames",
        "contact_sheets",
        "durable_calls",
    ]
    comparison = {
        key: {
            "prior_geometry": prior[key],
            "new_geometry": positive[key],
            "delta": positive[key] - prior[key],
        }
        for key in metrics
    }
    comparison["model_turns"] = {
        "prior_geometry": len(prior["model_turns"]),
        "new_geometry": len(positive["model_turns"]),
        "delta": len(positive["model_turns"]) - len(prior["model_turns"]),
    }

    report = {
        "audit_passed": True,
        "preregistered": True,
        "negative_control": negative,
        "fixed_astra_new_geometry": positive,
        "geometry_transfer": {
            "seed": 991002,
            "contract": contract,
            "old_target_tiles": [678, 679, 680],
            "model_drag": drags[0],
            "prior_model_drag": prior_drag,
            "different_save": True,
            "different_target_tiles": True,
            "different_drag_points": True,
        },
        "contextual_unpaired_comparison": comparison,
        "scope": "one new save/map/target-screen-position episode; no general route, latency distribution, human comparison or speedup claim",
        "audit_sha256": sha(Path(__file__)),
        "shared_audit_dependency_sha256": sha(HERE / "audit_openttd_matched_v2.py"),
    }
    (BASE / "audit.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

