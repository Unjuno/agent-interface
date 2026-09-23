"""Acceptance-scoped verifier for the immutable GTK raw bundle."""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path
CASES=("USEFUL_EFFECT","UNAVAILABLE_BEFORE_INPUT","GUARDED_REFUSAL","ACCEPTED_NO_EFFECT","PARTIAL_COLLATERAL","STALE_REPAIR","AMBIGUOUS_DELIVERY","TERMINAL_CLEANUP_FAILURE")
def verify(summary, manifest, bundle_root):
    errors=[]
    rows=summary.get("rows",[])
    if [r.get("formal_receipt",{}).get("case") for r in rows] != list(CASES): errors.append("fixed_order")
    if summary.get("scorer_matches") is not True: errors.append("scorer")
    if summary.get("formal_receipt_order_ok") is not True: errors.append("receipt_order")
    listed={item["path"]:item["sha256"] for item in manifest.get("files",[])}
    for name in ("useful","unavailable","guarded","no_effect","partial","stale_repair","ambiguous","cleanup_failure"):
        event=f"{name}/events.jsonl"
        if event not in listed: errors.append(f"raw_event_manifest:{name}"); continue
        p=bundle_root/event
        if not p.is_file(): errors.append(f"raw_event_missing:{name}"); continue
        if hashlib.sha256(p.read_bytes()).hexdigest()!=listed[event]: errors.append(f"raw_event_hash:{name}")
    for row in rows:
        if not isinstance(row.get("formal_receipt",{}).get("input_ledger"),list): errors.append(f"input_ledger:{row.get('case')}")
        if not isinstance(row.get("formal_receipt",{}).get("cleanup"),dict): errors.append(f"cleanup:{row.get('case')}")
    return {"decision":"PASS_FORMAL_2606_ACCEPTANCE" if not errors else "STOP_MISSING_RAW_RECEIPT_BUNDLE","errors":errors,"scope":"acceptance-scoped immutable raw-bundle verification"}
def main():
    if len(sys.argv)!=4: raise SystemExit("usage: verify_acceptance_v2.py SUMMARY MANIFEST BUNDLE_ROOT")
    s=json.loads(Path(sys.argv[1]).read_text()); m=json.loads(Path(sys.argv[2]).read_text())
    result=verify(s,m,Path(sys.argv[3])); print(json.dumps(result,indent=2,sort_keys=True)); return 0 if result["decision"].startswith("PASS") else 2
if __name__=="__main__": raise SystemExit(main())
