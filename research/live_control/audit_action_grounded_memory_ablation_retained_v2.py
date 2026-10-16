"""Retained audit that preserves and scopes the v1 prereg display omission."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/action-grounded-memory-ablation-live-01"
PLAN = HERE / "action_grounded_memory_ablation_live_v1_prereg.json"
USAGE = ("input_tokens", "cached_input_tokens", "cache_write_input_tokens",
         "output_tokens", "reasoning_output_tokens")


def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def events(path): return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines()]


def audit_call(root, expected_images, expected_prompt=None):
    raw_plan, process, rows = read(root / "plan.json"), read(root / "process.json"), events(root / "events.jsonl")
    assert raw_plan["requested_model"] == process["requested_model"] == "gpt-5.6-luna"
    assert raw_plan["requested_effort"] == process["requested_effort"] == "low"
    assert raw_plan["visible_images_submitted"] == process["visible_images_submitted"] == expected_images
    assert len(raw_plan["image_sha256"]) == expected_images and process["exit_code"] == 0
    if expected_prompt is not None: assert raw_plan["prompt_sha256"] == expected_prompt
    turns = [row for row in rows if row.get("type") == "turn.completed"]
    messages = [row for row in rows if row.get("type") == "item.completed" and row.get("item", {}).get("type") == "agent_message"]
    threads = [row for row in rows if row.get("type") == "thread.started"]
    assert len(turns) == len(messages) == len(threads) == 1
    assert all(type(turns[0]["usage"].get(key)) is int and turns[0]["usage"][key] >= 0 for key in USAGE)
    return raw_plan, turns[0]["usage"], threads[0]["thread_id"]


def main():
    plan, retained, report, diagnosis = read(PLAN), read(OUT / "prereg.json"), read(OUT / "report.json"), read(OUT / "audit-diagnosis.json")
    assert plan == retained and "requested_model" not in plan
    assert diagnosis["original_audit_error"] == "KeyError: requested_model"
    assert diagnosis["raw_requested_models"] == ["gpt-5.6-luna"]
    assert diagnosis["raw_requested_efforts"] == ["low"] and diagnosis["formal_output_rewritten"] is False
    for name, digest in plan["source_sha256"].items(): assert sha(HERE / name) == digest
    for key in ("full_frame_path", "action_crop_path"):
        assert sha(HERE / plan["memory"][key]) == plan["memory"][key.replace("path", "sha256")]
    pre_plan, pre_usage, pre_id = audit_call(OUT / "schema-preflight", 1)
    assert report["schema_preflight"]["usage"] == pre_usage
    assert report["schema_preflight"]["call_id"] == pre_id
    assert report["completed"] is True and report["formal_pass"] is True
    assert len(report["results"]) == plan["calls"]["comparison"] == 9
    assert report["allocation_retries"] == plan["retries"] == 0
    prompt_hash = report["results"][0]["prompt_sha256"]
    call_ids, combined_records = {pre_id}, []
    for result, scheduled in zip(report["results"], plan["schedule"]):
        assert (result["name"], result["scenario"], result["arm"], result["retry_count"]) == (
            scheduled["name"], scheduled["scenario"], scheduled["arm"], 0)
        expected_images = 1 if result["arm"] == "no_memory" else 2
        raw_plan, usage, call_id = audit_call(OUT / result["name"] / "model", expected_images, prompt_hash)
        assert call_id not in call_ids; call_ids.add(call_id)
        assert result["model"]["call_id"] == call_id and result["model"]["usage"] == usage
        assert result["model"]["visible_images_submitted"] == expected_images
        assert raw_plan["image_sha256"] == [entry["sha256"] for entry in result["images"]]
        current_path = OUT / result["name"] / Path(result["current_observation"]["image"]).name
        assert sha(current_path) == result["current_image_sha256"] == result["images"][0]["sha256"]
        assert result["model"]["decision"]["x"] == result["action"]["program"][0]["x"]
        assert result["model"]["decision"]["y"] == result["action"]["program"][0]["y"]
        assert result["correct"] is True and result["wrong_target_action"] is False and result["no_effect"] is False
        assert len(result["oracle_records"]) == 1 and result["oracle_records"][0]["exact"] is True
        combined_records.extend(result["oracle_records"])
        assert result["release_ok"] is True
        for action in result["actions"]:
            release = action["terminal"]["release"]
            assert release["verified"] is True and release["keys_down"] == [] and release["buttons_down"] == []
    assert report["all_records"] == combined_records and len(call_ids) == plan["calls"]["total"]
    for scenario in plan["scenarios"]:
        assert len({row["current_image_sha256"] for row in report["results"] if row["scenario"] == scenario}) == 1
    stats = {arm: {"correct": sum(row["correct"] for row in report["results"] if row["arm"] == arm),
                   "wrong": sum(row["wrong_target_action"] for row in report["results"] if row["arm"] == arm),
                   "input_tokens": sum(row["model"]["usage"]["input_tokens"] for row in report["results"] if row["arm"] == arm),
                   "images": sum(row["model"]["visible_images_submitted"] for row in report["results"] if row["arm"] == arm)}
             for arm in plan["arms"]}
    assert report["stats"] == stats
    assert stats == {"no_memory": {"correct": 3, "wrong": 0, "input_tokens": 28035, "images": 3},
                     "full_frame": {"correct": 3, "wrong": 0, "input_tokens": 31791, "images": 6},
                     "action_crop": {"correct": 3, "wrong": 0, "input_tokens": 28188, "images": 6}}
    assert report["decision"] == "CROP_ELIGIBLE_FOR_TRANSFER"
    print(json.dumps({"passed": True, "calls": len(call_ids), "tasks": 9,
        "stats": stats, "decision": report["decision"],
        "audit_scope": "v1 model display omission retained; source-fixed Luna-low verified from all raw plans"}, indent=2))


if __name__ == "__main__": main()
