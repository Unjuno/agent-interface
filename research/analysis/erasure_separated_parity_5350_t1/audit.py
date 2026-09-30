import json,sys
from pathlib import Path
import oracle
def audit(raw):
    errors=[];seen=set()
    if raw.get("source_main")!="e81cbac968752791678d22a4de3f2d276497d614":errors.append("SOURCE_MAIN_MISMATCH")
    for r in raw.get("rows",[]):
        n=r.get("case_id");seen.add(n);expected=oracle.EXPECTED.get(n);got=(r.get("status"),r.get("presentation_complete"),r.get("reconstructed"),r.get("authority_eligible"))
        if got!=expected:errors.append(f"ORACLE_MISMATCH:{n}")
        if r.get("external_effect") is not False:errors.append(f"EXTERNAL_EFFECT:{n}")
        if r.get("reconstructed") and r.get("authority_eligible"):errors.append(f"RECONSTRUCTION_AUTHORITY:{n}")
        c=r.get("inputs",{});shards=c.get("arrival",[])
        if r.get("authority_eligible") and (not all(any(s["id"]==name for s in shards) for name in ("a","b","c","d")) or any(s["generation"]!=c["generation"] for s in shards)):errors.append(f"INEXACT_AUTHORITY:{n}")
    if seen!=set(oracle.EXPECTED):errors.append("ROW_SET_MISMATCH")
    return errors
if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: audit.py RAW.json AUDIT.json")
    src,dst=map(Path,sys.argv[1:]);errors=audit(json.loads(src.read_text(encoding="utf-8")));out={"status":"PASS_READONLY" if not errors else "FAIL_READONLY","errors":errors}
    if dst.exists():raise SystemExit("STOP_AUDIT_OUTPUT_ALREADY_EXISTS")
    dst.write_text(json.dumps(out,sort_keys=True,indent=2)+"\n",encoding="utf-8");print(json.dumps(out,sort_keys=True))
    if errors:raise SystemExit(1)
