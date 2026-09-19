"""Diagnose and retain the first target-relative live failure without rerun."""
import hashlib
import json
import os
from pathlib import Path


HERE=Path(__file__).resolve().parent
ROOT=HERE/"results/target-relative-semantic-probe-live-01"
PLAN=HERE/"target_relative_semantic_probe_live_v1_prereg.json"
def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    plan=read(PLAN); events=read(ROOT/"events.json"); owners=read(ROOT/"owner-events.json")
    terminal=next(row for row in events if row.get("event")=="terminal" and
                  row.get("id")=="relative-translated-submit-01")
    source=next(row for row in events if row.get("event")=="observation" and
                row.get("id")=="relative-source")
    moved=next(row for row in events if row.get("event")=="test_surface_moved")
    checks={"source_geometry":source["pointer_binding"]["geometry"]==plan["expected_source_geometry"],
        "exact_move":[moved["after"]["geometry"][i]-moved["before"]["geometry"][i]
                      for i in (0,1)]==plan["move_delta"],
        "safe_pre_input_refusal":terminal["status"]=="needs_decision" and
                                 terminal["steps_completed"]==0,
        "no_semantic_probe":not any(row.get("event")=="semantic_probe" for row in events),
        "no_submission":not (ROOT/"submitted.txt").exists(),
        "empty_release":terminal["release"]["verified"] is True and
                        terminal["release"]["keys_down"]==[] and
                        terminal["release"]["buttons_down"]==[] and
                        all(row["verified"] is True and row["keys_down"]==[] and
                            row["buttons_down"]==[] for row in owners)}
    failure={"schema":"target-relative-semantic-probe-failure-v1",
        "formal_passed":False,"checks":checks,
        "failure_class":"current_binding_not_refreshed_after_external_surface_translation",
        "diagnosis":"The contract source and surface move were valid, but the executor retained the last observed pre-move pointer binding. Its ordinary admission rejected the first translated pointer step before input or probing.",
        "preserved_invariant":"External geometry change cannot silently refresh input authority. A fresh coherent passive observation must precede a pointer program in the moved geometry.",
        "repair_boundary":"In a distinct allocation, take exactly one passive snapshot after the move and require its coherent binding to equal the moved geometry before submitting the unchanged translated pointer program.",
        "terminal":terminal,"source_observation":source,"move":moved,"retry_count":0,
        "scope":plan["scope"]}
    (ROOT/"failure.json").write_text(json.dumps(failure,indent=2)+"\n",encoding="utf-8")
    files=sorted(path for path in ROOT.rglob("*") if path.is_file() and
                 path.name not in ("retention.json","retained-audit.json"))
    receipt={"schema":"target-relative-semantic-probe-retention-v1",
        "decision":"RETAIN_FIRST_OUTCOME_NO_RETRY","formal_passed":False,
        "diagnosis_checks_passed":all(checks.values()),"failure_class":failure["failure_class"],
        "manifest":{path.relative_to(ROOT).as_posix():sha(path) for path in files},
        "files":len(files),"bytes":sum(path.stat().st_size for path in files),"retry_count":0}
    temporary=ROOT/"retention.json.tmp"; temporary.write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    os.replace(temporary,ROOT/"retention.json")
    print(json.dumps({"checks":checks,"failure_class":receipt["failure_class"],
                      "files":receipt["files"],"bytes":receipt["bytes"]},indent=2))
    return 0 if all(checks.values()) else 1


if __name__=="__main__": raise SystemExit(main())
