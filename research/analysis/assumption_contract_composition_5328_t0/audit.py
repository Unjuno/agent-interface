import json,sys
from pathlib import Path
import oracle
def audit(raw):
    errors=[];seen=set()
    if raw.get("source_main")!="a1d0d0290b8619902d34b13d9e536c4bde063f74":errors.append("SOURCE_MAIN_MISMATCH")
    for r in raw.get("rows",[]):
        n=r.get("case_id");seen.add(n);expected=oracle.EXPECTED.get(n);got=(r.get("flat_local_pass"),r.get("composed_status"))
        if got!=expected:errors.append(f"ORACLE_MISMATCH:{n}")
        if r.get("authority_minted") is not False or r.get("external_effect") is not False:errors.append(f"AUTHORITY_OR_EFFECT:{n}")
        if r.get("composed_status")=="PASS" and (not r["flat_local_pass"] or not r["inputs"]["compatible"] or not r["inputs"]["versions_current"] or any(a!="DISCHARGED" for a in r["inputs"]["assumptions"])):errors.append(f"UNJUSTIFIED_PASS:{n}")
    if seen!=set(oracle.EXPECTED):errors.append("ROW_SET_MISMATCH")
    false_positive=sum(1 for r in raw.get("rows",[]) if r.get("flat_local_pass") and r.get("composed_status")!="PASS")
    if false_positive!=5:errors.append("LOCAL_ONLY_MISMATCH_COUNT")
    return errors
if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: audit.py RAW.json AUDIT.json")
    src,dst=map(Path,sys.argv[1:]);errors=audit(json.loads(src.read_text(encoding="utf-8")));out={"status":"PASS_READONLY" if not errors else "FAIL_READONLY","errors":errors}
    if dst.exists():raise SystemExit("STOP_AUDIT_OUTPUT_ALREADY_EXISTS")
    dst.write_text(json.dumps(out,sort_keys=True,indent=2)+"\n",encoding="utf-8");print(json.dumps(out,sort_keys=True))
    if errors:raise SystemExit(1)
