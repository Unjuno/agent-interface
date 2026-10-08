from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]; HERE=Path(__file__).resolve().parent; OUT=HERE/"evidence/preflight-v1"
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    pre=json.loads((OUT/"preregistration.json").read_text()); container=json.loads((OUT/"container-result.json").read_text()); result=json.loads((OUT/"preflight-result.json").read_text())
    hashes={rel:sha(ROOT/rel) for rel in pre["source_hashes"]}
    checks={"frozen_sources_match":hashes==pre["source_hashes"],"container_returned_zero":container.get("returncode")==0,
      "network_none_repo_read_only":container.get("network")=="none" and container.get("repository_read_only") is True,
      "all_preflight_checks_pass":result.get("status")=="PASS_FORMAL_WRAPPER_PREFLIGHT" and all(result.get("checks",{}).values()),
      "no_task_or_model_activity":container.get("model_calls")==0 and container.get("task_started") is False and container.get("gui_actions")==0 and container.get("ipc_calls")==0,
      "v29_formal_fail_preserved":result.get("formal_predecessor_outcome")=="FAIL_TASK1_SCOPED"}
    audit={"status":"PASS_FORMAL_WRAPPER_PREFLIGHT_AUDIT" if all(checks.values()) else "STOP_FORMAL_WRAPPER_PREFLIGHT_AUDIT","checks":checks,"source_hashes":hashes,"auditor_sha256":sha(HERE/"preflight_audit_v30.py"),"scope":"no-task preflight only"}
    (OUT/"independent-audit.json").write_text(json.dumps(audit,indent=2,sort_keys=True)+"\n")
    files=sorted(p for p in OUT.rglob("*") if p.is_file() and p.name!="SHA256SUMS")
    (OUT/"SHA256SUMS").write_text("".join(f"{sha(p)}  {p.relative_to(OUT)}\n" for p in files))
    return 0 if audit["status"]=="PASS_FORMAL_WRAPPER_PREFLIGHT_AUDIT" else 1
if __name__=="__main__": raise SystemExit(main())
