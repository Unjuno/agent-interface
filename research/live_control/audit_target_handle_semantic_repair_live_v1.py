"""Independent audit of target-handle-derived resize repair."""
import hashlib,json
from pathlib import Path
from target_relative_crop_semantic_probe_v1 import reconcile_artifact,score_path
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[1]
PLAN=HERE/"target_handle_semantic_repair_live_v1_prereg.json"
def read(path):return json.loads(Path(path).read_text(encoding="utf-8"))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
    plan=read(PLAN);root=REPO/plan["output"];report=read(root/"report.json")
    events=read(root/"events.json");observations={row["sequence"]:row for row in events if row.get("event")=="observation"}
    probes=report["clients"]["positive"]["feedback"];rescored=[]
    for probe in probes:
        observation=observations[probe["sequence"]];image=root/Path(observation["image"]).name
        score=score_path(report["repaired"]["contract"],image,observation["pointer_binding"])
        rescored.append({"probe":probe,"score":score,"receipt":reconcile_artifact(score,image)})
    useful=next(row for row in rescored if row["score"]["success"])
    checks={"frozen_sources":all((REPO/name).is_file() and sha(REPO/name)==digest
                                  for name,digest in plan["source_sha256"].items()),
        "formal":report["passed"] is True and all(report["checks"].values()),
        "old_refusal":report["old_contract_score"]["reason"]=="surface_size_changed",
        "handle_repair":report["resized_resolution"]["eligible"] is True and
                        report["repaired"]["receipt"]["model_calls"]==0,
        "same_scores":all(row["probe"]["score"]==row["score"] for row in rescored),
        "semantic_success":useful["score"]["success"] is True,
        "exact_artifacts":all(row["receipt"]["matches"] for row in rescored),
        "independent_output":report["actual"]=={"value":[report["goal"]["token"]]},
        "release":report["checks"]["empty_release"] is True,
        "zero_model_retry":report["model_calls"]==report["retry_count"]==0}
    result={"passed":all(checks.values()),"checks":checks,"formal_passed":report["passed"],
            "rescored":len(rescored),"metrics_ms":report["metrics_ms"],"scope":plan["scope"]}
    (root/"audit.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2));return 0 if result["passed"] else 1
if __name__=="__main__":raise SystemExit(main())
