import json,sys
from pathlib import Path
import oracle
def audit(raw):
    errors=[];seen=set()
    if raw.get("source_main")!="8265c1a19cbba7ab0f5316f27bdb59509269399d":errors.append("SOURCE_MAIN_MISMATCH")
    for r in raw.get("rows",[]):
        n=r.get("case_id");seen.add(n);expected=oracle.EXPECTED.get(n);got=(r.get("status"),r.get("admitted"),r.get("false_reject"))
        if got!=expected:errors.append(f"ORACLE_MISMATCH:{n}")
        if r.get("dispatched") is not False or r.get("authority_minted") is not False or r.get("external_effect") is not False:errors.append(f"EFFECT_OR_AUTHORITY:{n}")
        if r.get("argument_only_admitted") is not True:errors.append(f"BASELINE_MISSING:{n}")
        m=r.get("manifest",{});row=m.get("row")
        if row is None and r.get("status")!="EFFECT_UNKNOWN":errors.append(f"UNKNOWN_PROMOTED:{n}")
        if row is not None and r.get("admitted") and not set(row)<=set(m.get("approved",())):errors.append(f"UNDECLARED_ADMITTED:{n}")
    if seen!=set(oracle.EXPECTED):errors.append("ROW_SET_MISMATCH")
    return errors
if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: audit.py RAW.json AUDIT.json")
    src,dst=map(Path,sys.argv[1:]);errors=audit(json.loads(src.read_text(encoding="utf-8")));out={"status":"PASS_READONLY" if not errors else "FAIL_READONLY","errors":errors}
    if dst.exists():raise SystemExit("STOP_AUDIT_OUTPUT_ALREADY_EXISTS")
    dst.write_text(json.dumps(out,sort_keys=True,indent=2)+"\n",encoding="utf-8");print(json.dumps(out,sort_keys=True))
    if errors:raise SystemExit(1)
