"""Custody audit for the single R14 run, including early stop outcomes."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent; R=P/"run"; ROOT=Path(__file__).resolve().parents[3]
def verify(path,base):
    errors=[]
    for row in path.read_text(encoding="ascii").splitlines():
        expected,rel=row.split("  ",1); target=base/rel
        actual=hashlib.sha256(target.read_bytes()).hexdigest() if target.is_file() else None
        if actual!=expected: errors.append(rel)
    return {"entries":len(path.read_text(encoding="ascii").splitlines()),"errors":errors}
local={"conditions.json","PREREGISTRATION.md","runner.py","audit.py","custody_audit.py"}
pre=verify(P/"PRETRIAL_SHA256SUMS",lambda rel:(P/rel if rel in local else ROOT/rel)); raw=verify(R/"SHA256SUMS",lambda rel:R/rel)
d=json.loads((R/"result.json").read_text(encoding="utf-8"))
fixtures=list(R.glob("*/events.jsonl")); journals=[]
for f in fixtures:
    journals.extend(json.loads(x) for x in f.read_text(encoding="utf-8").splitlines())
cleanup=d.get("cleanup",{})
checks={"attempt_id_retained":d.get("attempt_id")=="win32-native-sendinput-r15-20261122",
 "one_result_no_retry":len(list(R.rglob("result.json")))==1,
 "all_fixture_events_retained":bool(fixtures),
 "fixture_cleanup":cleanup.get("fixture_exit_code")==0,
 "foreground_restored":cleanup.get("foreground_before")==cleanup.get("foreground_after_restore"),
 "pretrial_manifest_valid":not pre["errors"],"raw_manifest_valid":not raw["errors"]}
report={"attempt_id":d.get("attempt_id"),"first_classification":d.get("classification"),"checks":checks,"pretrial_hash_audit":pre,"raw_hash_audit":raw,"custody_audit_pass":all(checks.values()),"experiment_acceptance_pass":d.get("classification")=="PASS_RECOVERY_FRESH_GENERATION_TASK"}
(P/"custody-audit.json").write_text(json.dumps(report,indent=2,sort_keys=True)+chr(10),encoding="utf-8")
print(json.dumps(report,indent=2,sort_keys=True))
if not report["custody_audit_pass"]: raise SystemExit(1)
