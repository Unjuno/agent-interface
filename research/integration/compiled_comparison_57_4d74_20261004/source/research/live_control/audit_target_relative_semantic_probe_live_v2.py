"""Independent audit of repaired translated success and resize refusal."""
import hashlib
import json
from pathlib import Path

from target_relative_crop_semantic_probe_v1 import reconcile_artifact, score_path


HERE = Path(__file__).resolve().parent; REPO = HERE.parents[1]
PLAN = HERE/"target_relative_semantic_probe_live_v2_prereg.json"
def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    plan=read(PLAN); root=REPO/plan["output"]; report=read(root/"report.json")
    events=read(root/"events.json"); observations={row["sequence"]:row for row in events
        if row.get("event")=="observation"}
    probes=report["clients"]["positive"]["feedback"]+report["clients"]["resize"]["feedback"]
    rescored=[]
    for probe in probes:
        observation=observations[probe["sequence"]]; image=root/Path(observation["image"]).name
        score=score_path(report["contract"],image,observation["pointer_binding"])
        rescored.append({"probe":probe,"score":score,"receipt":reconcile_artifact(score,image)})
    useful=next(row for row in rescored if row["score"]["success"])
    resize=rescored[-1]
    checks={"frozen_sources":all((REPO/name).is_file() and sha(REPO/name)==digest
                                  for name,digest in plan["source_sha256"].items()),
        "formal_result":report["passed"] is True and all(report["checks"].values()),
        "fresh_moved_binding":report["checks"]["fresh_moved_binding"] is True,
        "same_scores":all(row["probe"]["score"]==row["score"] for row in rescored),
        "translated_success":useful["score"]["binding_status"]=="CURRENT_TRANSLATED" and
            useful["score"]["translation"]==plan["move_delta"],
        "resize_refusal":resize["score"]["reason"]=="surface_size_changed" and
            resize["score"]["observed_crop_sha256"] is None,
        "fixed_control":report["fixed_control"]["success"] is False,
        "exact_artifacts":all(row["receipt"]["matches"] for row in rescored),
        "independent_output":report["actual"]=={"value":[report["goal"]["token"]]},
        "release":report["checks"]["empty_release"] is True,
        "zero_model_retry":report["model_calls"]==report["retry_count"]==0}
    result={"passed":all(checks.values()),"checks":checks,"formal_passed":report["passed"],
            "rescored":len(rescored),"metrics_ms":report["metrics_ms"],"scope":plan["scope"]}
    (root/"audit.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2)); return 0 if result["passed"] else 1


if __name__=="__main__": raise SystemExit(main())
