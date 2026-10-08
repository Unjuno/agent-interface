"""Audit retained neutral-fault binding-readiness failure."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[1];ROOT=HERE/"results/release-prepared-selection-live-02"
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())
def main():
    retention,failure=read(ROOT/"retention.json"),read(ROOT/"failure.json")
    plan,report,events=read(ROOT/"preregistration.json"),read(ROOT/"report.json"),read(ROOT/"events.json")
    selection=[row for row in events if row.get("id")=="prepared-red-selection-02"]
    terminal=next(row for row in selection if row.get("event")=="terminal")
    checks={
      "manifest":all(sha(ROOT/name)==digest for name,digest in retention["manifest"].items()),
      "frozen_sources":all(sha(REPO/name)==digest for name,digest in plan["source_sha256"].items()),
      "first_failure":retention["decision"]=="RETAIN_FIRST_FAILURE_NO_RETRY" and failure["allocation_passed"] is False,
      "neutral_visual_precondition":failure["neutral_precondition"]["outside_target"] is True and failure["neutral_precondition"]["fresh_target_validation"]["status"]=="VALID_CURRENT" and failure["neutral_precondition"]["pre_selection_score"]["success"] is False,
      "binding_incoherent":failure["binding_fault"]["pointer_binding"] is None and failure["binding_fault"]["before"]["surface"] is None and failure["binding_fault"]["after"]["surface"] is not None,
      "safe_before_input_refusal":len([r for r in selection if r.get("event")=="accepted"])==1 and not any(r.get("event")=="pointer_admission" for r in selection) and terminal["status"]=="needs_decision" and terminal["steps_completed"]==0 and terminal["release"]["verified"] is True,
      "incomplete_report_no_audit":"passed" not in report and not (ROOT/"audit.json").exists(),
      "zero_retry_model":failure["retry_count"]==failure["model_calls"]==0}
    audit={"passed":all(checks.values()),"checks":checks,"allocation_passed":False,
      "failure_class":failure["failure_class"],"files_in_manifest":len(retention["manifest"]),
      "bytes_before_receipt":retention["bytes"],"next_condition":failure["next_condition"]}
    (ROOT/"retained-audit.json").write_text(json.dumps(audit,indent=2)+"\n")
    print(json.dumps(audit,indent=2));return 0 if audit["passed"] else 1
if __name__=="__main__":raise SystemExit(main())
