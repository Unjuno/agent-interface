from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]; HERE=Path(__file__).resolve().parent; OUT=HERE/"evidence/offline-replay-v1"
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    prereg=json.loads((OUT/"preregistration.json").read_text()); result=json.loads((OUT/"offline-result.json").read_text()); container=json.loads((OUT/"container-result.json").read_text())
    hashes={rel:sha(ROOT/rel) for rel in prereg["source_hashes"]}
    checks={"frozen_sources_unchanged":hashes==prereg["source_hashes"],"outer_container_returned_zero":container.get("returncode")==0,
      "container_network_none_and_repo_read_only":container.get("network")=="none" and container.get("read_only_repo") is True,
      "independent_offline_result_all_checks_pass":result.get("status")=="PASS_OFFLINE_RECONCILIATION" and all(result.get("checks",{}).values()),
      "predecessor_formal_fail_preserved":result.get("formal_outcome")=="FAIL_TASK1_SCOPED" and result.get("predecessor_formal_outcome")=="FAIL_TASK1_SCOPED",
      "no_task_or_model_claim":result.get("task_started") is False and result.get("model_calls")==0 and result.get("gui_actions")==0 and result.get("ipc_calls")==0}
    evidence={str(p.relative_to(OUT)):sha(p) for p in sorted(OUT.rglob("*")) if p.is_file() and p.name not in {"independent-audit.json","SHA256SUMS"}}
    audit={"issue":3798,"parent_issue":2849,"status":"PASS_OFFLINE_RECONCILIATION_AUDIT" if all(checks.values()) else "STOP_OFFLINE_RECONCILIATION_AUDIT","checks":checks,"source_hashes":hashes,"evidence_file_hashes_before_audit":evidence,"auditor_sha256":sha(HERE/"audit_v1.py"),"formal_outcome":"FAIL_TASK1_SCOPED","scope":"offline accounting reconciliation only"}
    (OUT/"independent-audit.json").write_text(json.dumps(audit,indent=2,sort_keys=True)+"\n")
    files=sorted(p for p in OUT.rglob("*") if p.is_file() and p.name!="SHA256SUMS")
    (OUT/"SHA256SUMS").write_text("".join(f"{sha(p)}  {p.relative_to(OUT)}\n" for p in files))
    return 0 if audit["status"]=="PASS_OFFLINE_RECONCILIATION_AUDIT" else 1
if __name__=="__main__": raise SystemExit(main())
