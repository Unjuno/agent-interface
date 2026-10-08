"""Audit retention and core outcomes for adaptive semantic repair live v2."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/adaptive-semantic-repair-live-02"
PLAN = HERE / "adaptive_semantic_repair_live_v2_prereg.json"


def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    retention, report, plan = read(OUT / "retention.json"), read(OUT / "report.json"), read(PLAN)
    assert retention["decision"] == "RETAIN_PASSED_FIRST_OUTCOME_NO_RETRY"
    assert retention["file_count"] == len(retention["manifest"])
    assert retention["total_bytes"] == sum(row["bytes"] for row in retention["manifest"])
    for row in retention["manifest"]:
        path = OUT / row["path"]
        assert path.stat().st_size == row["bytes"] and sha(path) == row["sha256"]
    for name, digest in plan["source_sha256"].items():
        assert sha(HERE.parent.parent / name) == digest
    assert report["passed"] is True and len(report["results"]) == 2
    local, model = report["results"]
    assert [local["mode"], model["mode"]] == ["local", "model"]
    assert all(row["status"] == "COMPLETED" and row["passed"] is True
               and row["retry_count"] == 0 for row in (local, model))
    assert local["adaptive"]["repair_trace"] == [
        {"stage": "reuse_revalidate", "status": "association_changed"},
        {"stage": "local_repair", "status": "repaired"}]
    assert local["adaptive"]["accounting"]["attempted_calls"] == 0
    assert model["adaptive"]["repair_trace"] == [
        {"stage": "reuse_revalidate", "status": "association_changed"},
        {"stage": "local_repair", "status": "missing"},
        {"stage": "model_reacquisition", "status": "target_reference"},
        {"stage": "post_model_revalidate", "status": "current_patch_match"}]
    assert model["adaptive"]["accounting"]["attempted_calls"] == 1
    for row in (local, model):
        assert row["actual"] == {"value": [row["goal"]["token"]]}
        assert row["adaptive"]["selected_target"]["pre_action_score"]["reason"] == \
               "expected_crop_missing"
        assert all(action["terminal"]["release"]["verified"] is True and
                   action["terminal"]["release"]["keys_down"] == [] and
                   action["terminal"]["release"]["buttons_down"] == []
                   for action in row["actions"])
    audit = {"schema": "adaptive-semantic-repair-live-retained-audit-v2",
             "passed": True, "checks": 16,
             "decision": retention["decision"]}
    (OUT / "retained-audit.json").write_text(json.dumps(audit, indent=2) + "\n",
                                              encoding="utf-8", newline="\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__": main()
