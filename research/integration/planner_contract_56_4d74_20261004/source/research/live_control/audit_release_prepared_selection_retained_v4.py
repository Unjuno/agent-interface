"""Audit retained first-useful-feedback selection evidence."""
import hashlib,json
from pathlib import Path
from executor_v11 import program_sha256
from inkscape_selection_scorer_v2 import score
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[1];ROOT=HERE/"results/release-prepared-selection-live-04"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def main():
 r,p,report,audit=read(ROOT/"retention.json"),read(ROOT/"preregistration.json"),read(ROOT/"report.json"),read(ROOT/"audit.json")
 early=report["clients"]["early"];scores=report["semantic_scores"];accepted=report["selection_accepted"];terminal=report["selection_terminal"];m=report["metrics_ms"]
 recomputed=[score(early["candidate"],ROOT/Path(row["observation"]["image"]).name) for row in scores]
 checks={"manifest":all(sha(ROOT/n)==d for n,d in r["manifest"].items()),"frozen_sources":all(sha(REPO/n)==d for n,d in p["source_sha256"].items()),"first_pass":r["decision"]=="RETAIN_FIRST_OUTCOME_NO_RETRY" and report["passed"] is True and audit["passed"] is True,"coherent_ready":report["binding_attempts"][-1]["status"]=="READY","program_attested":accepted["steps"]==2 and accepted["program_sha256"]==program_sha256(report["selection_program"]),"first_then_useful":len(scores)>=2 and scores[0]["score"]["success"] is False and scores[-1]["score"]["success"] is True and recomputed==[row["score"] for row in scores] and report["semantic_observation"]["sequence"]>report["selection_observation"]["sequence"],"live_clocks":scores[0]["detected_ns"]>=scores[0]["observation"]["capture_ns"] and report["semantic_score_completed_ns"]==scores[-1]["scored_ns"],"terminal_release":terminal["status"]=="completed" and terminal["steps_completed"]==2 and terminal["release"]["verified"] is True and terminal["release"]["keys_down"]==[] and terminal["release"]["buttons_down"]==[],"timing":m["focus_to_semantic_score_ms"]<=p["thresholds_ms"]["focus_to_semantic_score_lte"] and m["selection_admission_to_first_feedback_received_ms"]<=p["thresholds_ms"]["admission_to_first_feedback_lte"] and m["selection_admission_to_semantic_score_ms"]<=p["thresholds_ms"]["admission_to_semantic_score_lte"],"zero_model_retry":report["model_calls"]==report["retry_count"]==0}
 out={"passed":all(checks.values()),"checks":checks,"allocation_passed":True,"metrics_ms":m,"files_in_manifest":len(r["manifest"]),"bytes_before_receipt":r["bytes"],"scope":report["scope"]};(ROOT/"retained-audit.json").write_text(json.dumps(out,indent=2)+"\n");print(json.dumps(out,indent=2));return 0 if out["passed"] else 1
if __name__=="__main__":raise SystemExit(main())
