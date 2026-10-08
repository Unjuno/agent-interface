import json,sys
from pathlib import Path
import oracle
def audit(raw):
    errors=[];seen=set()
    if raw.get("source_main")!="bbeee4da02285281e960334f8babefc2d7070358": errors.append("SOURCE_MAIN_MISMATCH")
    for r in raw.get("rows",[]):
        k=(r.get("case_id"),r.get("policy"));seen.add(k);expected=oracle.EXPECTED.get(k[0],{}).get(k[1]);got=(r.get("action_admitted"),r.get("reclaim_allowed"))
        if got!=expected: errors.append(f"OUTCOME_MISMATCH:{k}")
        if r.get("authority_minted") is not False or r.get("external_effect") is not False: errors.append(f"AUTHORITY_OR_EFFECT:{k}")
        c=r.get("inputs",{})
        if k[1]=="EPOCH_BOUND" and r.get("reclaim_allowed") and (set(c.get("readers",()))!=set(c.get("receipt_readers",())) or c.get("registry")!=c.get("receipt_registry") or c.get("receipt_authority")!="cap-A"): errors.append(f"UNSAFE_RECLAIM:{k}")
    keys={(c,p) for c,ps in oracle.EXPECTED.items() for p in ps}
    if seen!=keys: errors.append("ROW_SET_MISMATCH")
    return errors
if __name__=="__main__":
    if len(sys.argv)!=3: raise SystemExit("usage: audit.py RAW.json AUDIT.json")
    src,dst=map(Path,sys.argv[1:]);errors=audit(json.loads(src.read_text(encoding="utf-8")));out={"status":"PASS_READONLY" if not errors else "FAIL_READONLY","errors":errors}
    if dst.exists(): raise SystemExit("STOP_AUDIT_OUTPUT_ALREADY_EXISTS")
    dst.write_text(json.dumps(out,sort_keys=True,indent=2)+"\n",encoding="utf-8");print(json.dumps(out,sort_keys=True))
    if errors: raise SystemExit(1)
