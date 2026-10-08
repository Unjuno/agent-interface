"""Audit the preregistered archived OpenTTD effect-memory ablation."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
PLAN = HERE / "openttd_effect_memory_ablation_v1_prereg.json"
OUT = HERE / "results/openttd-effect-memory-ablation-01"
INPUTS = HERE / "results/openttd-action-effect-memory-inputs-01"


def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    plan, retained, report = read(PLAN), read(OUT / "prereg.json"), read(OUT / "report.json")
    assert plan == retained and sha(INPUTS / "manifest.json") == plan["input_manifest_sha256"]
    for name, digest in plan["source_sha256"].items(): assert sha(HERE / name) == digest
    preflight = report["schema_preflight"]
    if preflight.get("status") == "FAILED":
        raw = read(OUT / "schema-preflight/plan.json")
        assert raw["requested_model"] == plan["requested_model"]
        assert raw["requested_effort"] == plan["requested_effort"]
        assert report["completed"] is False and report["results"] == []
        assert report["decision"] == "INCOMPLETE_RETAIN_FIRST_OUTCOME"
        print(json.dumps({"passed": True, "completed": False, "decision": report["decision"]}, indent=2)); return
    assert preflight["requested_model"] == plan["requested_model"]
    assert preflight["requested_effort"] == plan["requested_effort"]
    assert preflight["visible_images_submitted"] == 1
    results = report["results"]
    assert [r["name"] for r in results] == [r["name"] for r in plan["schedule"][:len(results)]]
    prompt_hashes = {}
    for row, scheduled in zip(results, plan["schedule"]):
        assert (row["context"], row["arm"], row["retry_count"]) == (
            scheduled["context"], scheduled["arm"], 0)
        if row["status"] != "COMPLETED": continue
        receipt = read(INPUTS / row["context"] / "receipt.json")
        expected_images = {"no_memory": 1, "action_crop": 2, "full_history": 3}[row["arm"]]
        assert row["ground_truth"] == receipt["independent_ground_truth"] == "observed"
        assert row["model"]["requested_model"] == plan["requested_model"]
        assert row["model"]["requested_effort"] == plan["requested_effort"]
        assert row["model"]["visible_images_submitted"] == expected_images == len(row["images"])
        raw_plan = read(OUT / row["name"] / "model/plan.json")
        assert raw_plan["image_sha256"] == [image["sha256"] for image in row["images"]]
        assert row["correct"] == (row["model"]["decision"]["status"] == "observed")
        assert row["safe_next_action"] == (row["model"]["decision"]["next_action"] == "advance_without_repeat")
        prompt_hashes.setdefault(row["context"], set()).add(row["prompt_sha256"])
    assert all(len(values) == 1 for values in prompt_hashes.values())
    if report["completed"]:
        assert len(results) == 6 and all(row["status"] == "COMPLETED" for row in results)
        stats = {arm: {"correct": sum(r["correct"] for r in results if r["arm"] == arm),
                       "safe_next_action": sum(r["safe_next_action"] for r in results if r["arm"] == arm),
                       "input_tokens": sum(r["model"]["usage"]["input_tokens"] for r in results if r["arm"] == arm),
                       "images": sum(r["model"]["visible_images_submitted"] for r in results if r["arm"] == arm)}
                 for arm in plan["arms"]}
        assert report["stats"] == stats and report["formal_pass"] is True
        crop, full, none = stats["action_crop"], stats["full_history"], stats["no_memory"]
        eligible = (crop["correct"] == 2 and crop["safe_next_action"] == 2
                    and crop["correct"] >= full["correct"] and crop["correct"] >= none["correct"]
                    and crop["input_tokens"] < full["input_tokens"])
        expected = ("CROP_REPLACES_FULL_HISTORY_ONLY;_NO_DEFAULT_MEMORY_CHANGE" if eligible and none["correct"] == 2
                    else "CROP_ELIGIBLE_FOR_FRESH_HISTORY_NEEDED_TRANSFER" if eligible
                    else "DO_NOT_TRANSFER_CROP")
        assert report["decision"] == expected
    else:
        assert report["formal_pass"] is False and report["decision"] == "INCOMPLETE_RETAIN_FIRST_OUTCOME"
    print(json.dumps({"passed": True, "completed": report["completed"],
                      "formal_pass": report["formal_pass"], "decision": report["decision"]}, indent=2))


if __name__ == "__main__": main()
