"""Audit the frozen real-Chromium visual-memory ablation."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/action-grounded-memory-ablation-live-01"
PLAN = HERE / "action_grounded_memory_ablation_live_v1_prereg.json"


def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    plan, retained, report = read(PLAN), read(OUT / "prereg.json"), read(OUT / "report.json")
    assert plan == retained
    for name, digest in plan["source_sha256"].items(): assert sha(HERE / name) == digest
    for key in ("full_frame_path", "action_crop_path"):
        assert sha(HERE / plan["memory"][key]) == plan["memory"][key.replace("path", "sha256")]
    preflight = report["schema_preflight"]
    if preflight.get("status") == "FAILED":
        raw_plan = read(OUT / "schema-preflight" / "plan.json")
        assert raw_plan["requested_model"] == plan["requested_model"]
        assert raw_plan["requested_effort"] == plan["requested_effort"]
        assert raw_plan["visible_images_submitted"] == 1
        assert report["completed"] is False and report["results"] == []
        assert report["formal_pass"] is False and report["decision"] == "INCOMPLETE_RETAIN_FIRST_OUTCOME"
        print(json.dumps({"passed": True, "completed": False, "formal_pass": False,
                          "decision": report["decision"]}, indent=2)); return
    assert preflight["requested_model"] == plan["requested_model"]
    assert preflight["requested_effort"] == plan["requested_effort"]
    assert preflight["visible_images_submitted"] == 1
    results = report["results"]
    assert [row["name"] for row in results] == [row["name"] for row in plan["schedule"][:len(results)]]
    for row, scheduled in zip(results, plan["schedule"]):
        assert (row["scenario"], row["arm"], row["retry_count"]) == (
            scheduled["scenario"], scheduled["arm"], 0)
        if row["status"] != "COMPLETED": continue
        expected_images = 1 if row["arm"] == "no_memory" else 2
        assert row["model"]["requested_model"] == plan["requested_model"]
        assert row["model"]["requested_effort"] == plan["requested_effort"]
        assert row["model"]["visible_images_submitted"] == expected_images
        assert len(row["images"]) == expected_images
        assert row["images"][0]["sha256"] == row["current_image_sha256"]
        assert row["prompt_sha256"] == results[0]["prompt_sha256"]
        assert len(row["oracle_records"]) <= 1
        assert row["correct"] == (len(row["oracle_records"]) == 1 and row["oracle_records"][0]["exact"] is True)
        assert row["wrong_target_action"] == (len(row["oracle_records"]) == 1 and row["oracle_records"][0]["kind"] == "decoy")
        assert row["release_ok"] is True
        if row["action"] is not None:
            release = row["action"]["terminal"]["release"]
            assert release["verified"] is True and release["keys_down"] == [] and release["buttons_down"] == []
    if report["completed"]:
        assert len(results) == plan["calls"]["comparison"]
        assert all(row["status"] == "COMPLETED" for row in results)
        for scenario in plan["scenarios"]:
            assert len({row["current_image_sha256"] for row in results if row["scenario"] == scenario}) == 1
        stats = {arm: {"correct": sum(row["correct"] for row in results if row["arm"] == arm),
                       "wrong": sum(row["wrong_target_action"] for row in results if row["arm"] == arm),
                       "input_tokens": sum(row["model"]["usage"]["input_tokens"] for row in results if row["arm"] == arm),
                       "images": sum(row["model"]["visible_images_submitted"] for row in results if row["arm"] == arm)}
                 for arm in plan["arms"]}
        assert report["stats"] == stats
        crop = stats["action_crop"]
        expected = ("CROP_ELIGIBLE_FOR_TRANSFER" if report["formal_pass"] and crop["correct"] == 3
            and crop["wrong"] == 0 and crop["correct"] >= stats["full_frame"]["correct"]
            and crop["correct"] >= stats["no_memory"]["correct"]
            and crop["input_tokens"] < stats["full_frame"]["input_tokens"]
            else "DO_NOT_TRANSFER_CROP")
        assert report["decision"] == expected
    else:
        assert report["formal_pass"] is False and report["decision"] == "INCOMPLETE_RETAIN_FIRST_OUTCOME"
    print(json.dumps({"passed": True, "completed": report["completed"],
                      "formal_pass": report["formal_pass"], "decision": report["decision"]}, indent=2))


if __name__ == "__main__": main()
