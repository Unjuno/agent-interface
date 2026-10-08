"""Audit retained v3 evidence-shape and semantic-boundary failure."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[1];ROOT=HERE/"results/release-prepared-selection-live-03"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def main():
 r,f,p,report,events=read(ROOT/"retention.json"),read(ROOT/"failure.json"),read(ROOT/"preregistration.json"),read(ROOT/"report.json"),read(ROOT/"events.json")
 rows=[x for x in events if x.get("id")=="prepared-red-selection-03"];a=next(x for x in rows if x.get("event")=="accepted");t=next(x for x in rows if x.get("event")=="terminal")
 checks={"manifest":all(sha(ROOT/n)==d for n,d in r["manifest"].items()),"frozen_sources":all(sha(REPO/n)==d for n,d in p["source_sha256"].items()),"first_failure":r["decision"]=="RETAIN_FIRST_FAILURE_NO_RETRY" and f["allocation_passed"] is False,"report_incomplete":"passed" not in report and not (ROOT/"audit.json").exists(),"accepted_shape_defect":a["steps"]==2 and isinstance(a["steps"],int) and a["program_sha256"]==f["program"]["sha256"],"mechanics_completed":f["binding_readiness"]["status"]=="READY" and f["execution"]["pointer_admissions"]==2 and f["execution"]["observations"]==2 and t["status"]=="completed" and t["steps_completed"]==2 and t["release"]["verified"] is True,"first_vs_useful_feedback":f["semantic_scores_posthoc"][0]["success"] is False and f["semantic_scores_posthoc"][1]["success"] is True,"live_score_clock_missing":"live semantic-score completion clock" in f["limits"],"zero_retry_model":f["retry_count"]==f["model_calls"]==0}
 out={"passed":all(checks.values()),"checks":checks,"allocation_passed":False,"failure_class":f["failure_class"],"files_in_manifest":len(r["manifest"]),"bytes_before_receipt":r["bytes"],"next_condition":f["next_condition"]};(ROOT/"retained-audit.json").write_text(json.dumps(out,indent=2)+"\n");print(json.dumps(out,indent=2));return 0 if out["passed"] else 1
if __name__=="__main__":raise SystemExit(main())
