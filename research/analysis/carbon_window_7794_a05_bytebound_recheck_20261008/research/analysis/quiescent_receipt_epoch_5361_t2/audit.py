import json,sys
from pathlib import Path
import oracle
def audit(raw):
    errors=[];seen=set()
    if raw.get("source_main")!="b0190453a787102189429e4b8c32032cf60efd17":errors.append("SOURCE_MAIN_MISMATCH")
    for row in raw.get("rows",[]):
        name=row.get("case_id");seen.add(name);expected=oracle.EXPECTED.get(name);got=(row.get("action_admitted"),row.get("reclaim_allowed"))
        if got!=expected:errors.append(f"OUTCOME_MISMATCH:{name}")
        if row.get("authority_minted") is not False or row.get("external_effect") is not False:errors.append(f"AUTHORITY_OR_EFFECT:{name}")
        if row.get("reclaim_allowed"):
            c=row["inputs"];receipts=c["receipts"]
            if any(r.get("epoch")!=4 or r.get("authority")!="cap-old" for r in receipts):errors.append(f"RECEIPT_EPOCH_OR_AUTHORITY:{name}")
            if len({r.get("receipt_id") for r in receipts})!=len(receipts):errors.append(f"DUPLICATE_RECEIPT:{name}")
            if {r.get("reader") for r in receipts}!=set(c["readers"]):errors.append(f"READER_SET:{name}")
            if any(r.get("registry_generation")!=12 for r in receipts) or c.get("registry_generation")!=12:errors.append(f"REGISTRY_GENERATION:{name}")
    if seen!=set(oracle.EXPECTED):errors.append("ROW_SET_MISMATCH")
    return errors
if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: audit.py RAW.json AUDIT.json")
    src,dst=map(Path,sys.argv[1:]);errors=audit(json.loads(src.read_text(encoding="utf-8")));out={"status":"PASS_READONLY" if not errors else "FAIL_READONLY","errors":errors}
    if dst.exists():raise SystemExit("STOP_AUDIT_OUTPUT_ALREADY_EXISTS")
    dst.write_text(json.dumps(out,sort_keys=True,indent=2)+"\n",encoding="utf-8");print(json.dumps(out,sort_keys=True))
    if errors:raise SystemExit(1)
