"""Audit the frozen shared-caller live semantic-repair integration."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/adaptive-semantic-repair-live-01"
PLAN = HERE / "adaptive_semantic_repair_live_v1_prereg.json"


def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    plan, report = read(PLAN), read(OUT / "report.json")
    for name, digest in plan["source_sha256"].items():
        assert sha(HERE.parent.parent / name) == digest
    assert report["passed"] is True
    assert [row["mode"] for row in report["results"]] == plan["order"]
    assert len(report["results"]) == 2
    for row in report["results"]:
        assert row["status"] == "COMPLETED" and row["passed"] is True
        assert row["retry_count"] == 0 and all(row["checks"].values())
        assert row["actual"] == {"value": [row["goal"]["token"]]}
        assert row["old_contract_score"]["success"] is False
        assert row["adaptive"]["outcome"] == "TASK_SUCCEEDED"
        attempts = row["adaptive"]["attempt_ledger"]
        calls = row["adaptive"]["model_call_ledger"]
        accounting = row["adaptive"]["accounting"]
        assert accounting["attempted_calls"] == len(attempts)
        assert accounting["completed_calls"] == len(calls)
        assert accounting["visible_image_coverage"] == len(attempts)
        assert accounting["model_wait_coverage"] == len(attempts)
        assert len(row["model_outcomes"]) == plan["expected_model_calls"][row["mode"]]
        assert row["metrics"]["total_model_calls"] == plan["expected_model_calls"][row["mode"]]
        assert row["metrics"]["model_visible_images"] == plan["expected_model_calls"][row["mode"]]
        assert all(action["terminal"]["release"]["verified"] is True and
                   action["terminal"]["release"]["keys_down"] == [] and
                   action["terminal"]["release"]["buttons_down"] == []
                   for action in row["actions"])
    local, model = report["results"]
    assert local["mutation_kind"] == "window_resize"
    assert local["adaptive"]["repair_path"] == "local"
    assert local["adaptive"]["accounting"]["attempted_calls"] == 0
    assert local["adaptive"]["repair_trace"][-1] == {
        "stage": "local_repair", "status": "repaired"}
    assert model["mutation_kind"] == "button_hover"
    assert model["adaptive"]["repair_path"] == "model_reacquisition"
    assert model["adaptive"]["accounting"]["attempted_calls"] == 1
    assert model["adaptive"]["repair_trace"][1]["status"] in {
        "missing", "ambiguous", "association_changed"}
    assert model["adaptive"]["repair_trace"][-1] == {
        "stage": "post_model_revalidate", "status": "current_patch_match"}
    post = model["adaptive"]["selected_target"]
    assert post["source_sequence"] > model["mutation_observation"]["sequence"]
    print(json.dumps({"passed": True, "cases": 2,
                      "decision": "RETAIN_SHARED_CALLER_LIVE_INTEGRATION"}, indent=2))


if __name__ == "__main__": main()
