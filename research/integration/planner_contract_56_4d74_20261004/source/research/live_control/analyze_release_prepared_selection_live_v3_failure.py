"""Classify v3 evidence-check failure without rerunning live input."""
import hashlib,json
from pathlib import Path
from executor_v11 import program_sha256
from inkscape_red_target_planner_v1 import prepare,validate
from inkscape_selection_scorer_v2 import score
from pointer_binding_readiness_v1 import evaluate
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[1]
ROOT=REPO/"results-local/live_control/release-prepared-selection-live-03";PREREG=HERE/"release_prepared_selection_live_v3_prereg.json"
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())
def main():
 p,report,events=read(PREREG),read(ROOT/"report.json"),read(ROOT/"events.json")
 candidate=prepare(ROOT/"001.png",p["planner_roi"]);program=[candidate["action"],{"op":"observe"}]
 admission=next(r for r in events if r.get("id")=="prepared-pre-admission-0")
 rows=[r for r in events if r.get("id")=="prepared-red-selection-03"]
 accepted=next(r for r in rows if r.get("event")=="accepted");feedbacks=[r for r in rows if r.get("event")=="observation"];terminal=next(r for r in rows if r.get("event")=="terminal")
 scores=[score(candidate,ROOT/Path(row["image"]).name) for row in feedbacks]
 failure={"allocation_passed":False,"failure_class":"program_evidence_shape_and_first_feedback_semantics",
  "frozen_sources_match":all(sha(REPO/n)==d for n,d in p["source_sha256"].items()),
  "runner_error":{"type":"TypeError","detail":"'int' object is not subscriptable"},"report_incomplete":"passed" not in report,
  "binding_readiness":evaluate(admission,admission["runtime_emit_ns"]),
  "fresh_validation":validate(candidate,ROOT/Path(admission["image"]).name),
  "program":{"steps":program,"sha256":program_sha256(program),"accepted":accepted},
  "semantic_scores_posthoc":scores,
  "execution":{"pointer_admissions":len([r for r in rows if r.get("event")=="pointer_admission"]),"observations":len([r for r in rows if r.get("event")=="observation"]),"terminal":terminal},
  "limits":"live semantic-score completion clock and full report were not serialized; posthoc mechanics do not pass the allocation",
  "next_condition":"bind exact program by canonical SHA/count; retain first feedback separately and continue bounded observations until first semantic success or terminal; preserve v3; distinct v4",
  "retry_count":0,"model_calls":0}
 (ROOT/"failure.json").write_text(json.dumps(failure,indent=2)+"\n");print(json.dumps(failure,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
