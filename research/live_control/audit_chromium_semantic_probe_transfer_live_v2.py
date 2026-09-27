"""Independent audit for the repaired one-run Chromium semantic-probe transfer."""
import hashlib
import json
from pathlib import Path
import sys

from exact_crop_semantic_probe_v1 import reconcile_artifact, score_path
from executor_v11 import program_sha256


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
PREREG = HERE/"chromium_semantic_probe_transfer_live_v2_prereg.json"


def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    plan = read(PREREG); root = REPO/plan["output"]; report = read(root/"report.json")
    feedback = report["clients"]["negative"]["feedback"] + report["clients"]["positive"]["feedback"]
    observations = [row for row in read(root/"events.json") if row.get("event") == "observation"]
    by_sequence = {row["sequence"]: row for row in observations}
    rescored = []
    for probe in feedback:
        observation = by_sequence[probe["sequence"]]
        image = root/Path(observation["image"]).name
        score = score_path(plan["probe_contract"], image)
        receipt = reconcile_artifact(score, image)
        rescored.append({"probe": probe, "score": score, "receipt": receipt})
    negative = report["clients"]["negative"]["feedback"]
    positive = report["clients"]["positive"]["feedback"]
    useful = next((row for row in positive if row["score"]["success"]), None)
    actions = [report[name] for name in
               ("negative_action", "navigate", "fill", "positive_action")]
    checks = {
        "frozen_sources": all((REPO/name).is_file() and sha(REPO/name) == digest
                              for name, digest in plan["source_sha256"].items()),
        "first_outcome": report["allocation_id"] == plan["allocation_id"] and
                         report["retry_count"] == 0,
        "program_attestation": all(row["accepted"]["program_sha256"] ==
                                   program_sha256(row["program"]) for row in actions),
        "negative_exact_reject": len(negative) == 1 and
            negative[0]["score"]["success"] is False and
            rescored[0]["score"]["success"] is False,
        "positive_exact_accept": useful is not None and
            any(row["score"]["success"] is True for row in rescored[1:]),
        "same_scores": all(row["probe"]["score"] == row["score"] for row in rescored),
        "exact_artifacts": all(row["receipt"]["matches"] is True for row in rescored),
        "pre_artifact_order": all(row["probe"]["probe_completed_ns"] <
            next(item for item in report["reconciliations"]
                 if item["sequence"] == row["probe"]["sequence"])["image_ready_ns"]
            for row in rescored),
        "independent_output": report["actual"] == {"value": [report["goal"]["token"]]},
        "empty_release": all(row["terminal"]["release"]["verified"] is True and
            row["terminal"]["release"]["keys_down"] == [] and
            row["terminal"]["release"]["buttons_down"] == [] for row in actions),
        "zero_model": report["model_calls"] == 0,
        "formal_result_preserved": report["passed"] == all(report["checks"].values()),
    }
    result = {"passed": all(checks.values()), "checks": checks,
              "formal_passed": report["passed"], "rescored_probes": len(rescored),
              "metrics_ms": report["metrics_ms"], "scope": plan["scope"]}
    (root/"audit.json").write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__": raise SystemExit(main())
