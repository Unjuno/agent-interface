"""Audit matched semantic repair after post-model exact refresh."""
import hashlib,json,statistics
from pathlib import Path
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[1]
PLAN=HERE/"matched_semantic_repair_live_v3_prereg.json"
def read(path):return json.loads(Path(path).read_text(encoding="utf-8"))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
    plan=read(PLAN);root=REPO/plan["output"];report=read(root/"report.json");arms=report["arms"]
    local=[a for a in arms if a["mode"]=="local"];model=[a for a in arms if a["mode"]=="model"]
    token_adv=statistics.median(a["usage"]["input_tokens"] for a in model)-statistics.median(a["usage"]["input_tokens"] for a in local)
    recovery_adv=statistics.median(a["metrics_ms"]["recovery_from_resized_capture_ms"] for a in model)-statistics.median(a["metrics_ms"]["recovery_from_resized_capture_ms"] for a in local)
    ids=[r["call_id"] for a in arms for r in a["model_records"]]
    checks={"frozen_sources":all((REPO/n).is_file() and sha(REPO/n)==d for n,d in plan["source_sha256"].items()),
        "formal":report["passed"] is True and all(report["checks"].values()),
        "completed":report["status"]=="COMPLETED" and
            all(a["status"]=="COMPLETED" and a["comparison_eligible"] for a in arms),
        "admitted_before_mutation":all(a["checks"]["initial_admission_before_mutation"]
            and a["initial_admission"]["status"]=="TASK_MUTATION_ELIGIBLE"
            and a["initial_admission"]["grants_input_authority"] is False for a in arms),
        "post_model_revalidated":all(a["checks"]["post_model_current_revalidation"]
            and a["post_model_observation"] is not None
            and a["post_model_revalidation"]["status"]=="CURRENT_PATCH_MATCH_NO_AUTHORITY"
            and a["post_model_revalidation"]["grants_input_authority"] is False
            and a["metrics_ms"]["post_model_refresh_ms"]>0
            and a["metrics_ms"]["post_model_revalidation_ms"]>0
            for a in model),
        "same_order":[a["mode"] for a in arms]==plan["order"],
        "correct":all(a["checks"]["correct"] and a["checks"]["released"] for a in arms),
        "model_accounting":len(ids)==len(set(ids))==6 and all(a["usage"]["input_tokens"]>0 for a in arms)
            and sum(o["visible_images_submitted"] for a in arms for o in a["model_outcomes"])==6,
        "calls":all(len(a["model_records"])==plan["expected_arm_model_calls"][a["mode"]] for a in arms),
        "token_metric":token_adv==report["metrics"]["input_token_advantage"],
        "recovery_metric":recovery_adv==report["metrics"]["recovery_ms_advantage"],
        "gates":token_adv>=plan["thresholds"]["minimum_input_token_advantage"] and recovery_adv>=plan["thresholds"]["minimum_recovery_ms_advantage"],
        "no_retry":all(a["retry_count"]==0 for a in arms)}
    result={"passed":all(checks.values()),"checks":checks,"input_token_advantage":token_adv,
            "recovery_ms_advantage":recovery_adv,"call_ids":len(ids),"scope":plan["scope"]}
    (root/"audit.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8");print(json.dumps(result,indent=2));return 0 if result["passed"] else 1
if __name__=="__main__":raise SystemExit(main())
