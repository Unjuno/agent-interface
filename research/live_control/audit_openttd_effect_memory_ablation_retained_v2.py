"""Independent raw-call and retention audit; does not change the frozen v1 runner."""
import hashlib
import json
from pathlib import Path

from openttd_effect_model_v1 import parse


HERE = Path(__file__).resolve().parent
PLAN = HERE / "openttd_effect_memory_ablation_v1_prereg.json"
OUT = HERE / "results/openttd-effect-memory-ablation-01"
INPUTS = HERE / "results/openttd-action-effect-memory-inputs-01"


def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def audit_call(root, result, plan):
    raw = read(root / "plan.json"); process = read(root / "process.json")
    parsed = parse(root)
    assert raw["requested_model"] == process["requested_model"] == result["requested_model"] == plan["requested_model"]
    assert raw["requested_effort"] == process["requested_effort"] == result["requested_effort"] == plan["requested_effort"]
    assert raw["visible_images_submitted"] == process["visible_images_submitted"] == result["visible_images_submitted"]
    assert raw["prompt_sha256"] == sha(root / "prompt.txt") == result["prompt_sha256"]
    for name, key in (("openttd_effect_model_runner_v1.py", "runner_sha256"),
                      ("openttd_effect_decision_responder_v1.txt", "instructions_sha256"),
                      ("openttd_effect_decision_schema_v1.json", "schema_sha256")):
        assert raw[key] == sha(HERE / name)
    assert parsed["call_id"] == result["call_id"]
    assert parsed["decision"] == result["decision"]
    assert parsed["usage"] == result["usage"]
    assert process["exit_code"] == 0 and raw["observed_model_identity"] is None
    assert len(raw["image_sha256"]) == result["visible_images_submitted"]
    return raw


def main():
    plan, report = read(PLAN), read(OUT / "report.json")
    assert (OUT / "prereg.json").read_bytes() == PLAN.read_bytes()
    assert report["completed"] and report["formal_pass"] and report["allocation_retries"] == 0
    assert len(report["results"]) == plan["calls"]["comparison"] == 6
    raw_preflight = audit_call(OUT / "schema-preflight", report["schema_preflight"], plan)
    first = INPUTS / plan["contexts"][0]
    assert raw_preflight["image_sha256"] == [sha(first / "current.png")]
    image_costs = {}
    for row, scheduled in zip(report["results"], plan["schedule"]):
        assert row["status"] == "COMPLETED" and row["retry_count"] == 0
        assert row["name"] == scheduled["name"] and row["arm"] == scheduled["arm"]
        case = OUT / row["name"]
        assert read(case / "result.json") == row
        raw = audit_call(case / "model", row["model"], plan)
        assert row["model"]["prompt_sha256"] == row["prompt_sha256"]
        assert raw["image_sha256"] == [image["sha256"] for image in row["images"]]
        for image in row["images"]:
            assert sha(HERE / image["path"]) == image["sha256"]
        assert raw["image_sha256"][0] == sha(INPUTS / row["context"] / "current.png")
        image_costs.setdefault(row["arm"], []).append(row["model"]["usage"]["input_tokens"])
    assert report["stats"] == {
        "no_memory": {"correct": 2, "safe_next_action": 2, "input_tokens": 18736, "images": 2},
        "full_history": {"correct": 2, "safe_next_action": 2, "input_tokens": 23748, "images": 6},
        "action_crop": {"correct": 1, "safe_next_action": 1, "input_tokens": 19424, "images": 4}}
    assert report["decision"] == "DO_NOT_TRANSFER_CROP"
    assert image_costs == {"no_memory": [9368, 9368], "full_history": [11874, 11874],
                           "action_crop": [9712, 9712]}
    files = [path for path in OUT.rglob("*") if path.is_file()]
    print(json.dumps({"passed": True, "model_calls": 7, "formal_comparison_calls": 6,
                      "files": len(files), "bytes": sum(path.stat().st_size for path in files),
                      "decision": report["decision"], "observed_model_identity": None}, indent=2))


if __name__ == "__main__": main()
