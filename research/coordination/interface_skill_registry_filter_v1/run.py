from __future__ import annotations
import argparse, hashlib, json, pathlib
from model import select_semantic_only, select_applicability_aware, validate_registry_entry

ROOT = pathlib.Path(__file__).resolve().parent

def sha256(path: pathlib.Path) -> str:
    h=hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--out", required=True); args=ap.parse_args()
    out=pathlib.Path(args.out)
    if out.exists(): raise SystemExit("output exists")
    out.mkdir(parents=True)
    cases=json.loads((ROOT/"cases.json").read_text())
    rows=[]
    for rep in range(4):
        for case in cases:
            for policy in ("SEMANTIC_ONLY","APPLICABILITY_AWARE"):
                result=select_semantic_only(case) if policy=="SEMANTIC_ONLY" else select_applicability_aware(case)
                rows.append({"row_id":f"{case['case_id']}::r{rep}::{policy}","rep":rep,"case_id":case["case_id"],"expected_key":case["expected_key"],"expected_status":case["expected_status"],"result":result})
    malformed = [
        {"name":"missing_version","entry":{"skill_id":"x","version":"","provenance":"p","evidence_role":"CURRENT"}},
        {"name":"missing_provenance","entry":{"skill_id":"x","version":"1","provenance":"","evidence_role":"CURRENT"}},
        {"name":"unknown_role","entry":{"skill_id":"x","version":"1","provenance":"p","evidence_role":"MAGIC"}},
        {"name":"hint_in_place_promotion","entry":{"skill_id":"x","version":"1","provenance":"p","evidence_role":"HINT","mutate_hint_in_place_to_admission":True}},
    ]
    controls=[]
    for c in malformed:
        ok, reason=validate_registry_entry(c["entry"]); controls.append({"name":c["name"],"accepted":ok,"reason":reason})
    payload={
        "task":"SKILL-REGISTRY-APPLICABILITY-FILTER-20260917-001",
        "formal_rows":len(rows),
        "rows":rows,
        "malformed_controls":controls,
        "source_sha256":{p.name:sha256(p) for p in [ROOT/"model.py",ROOT/"cases.json",ROOT/"run.py",ROOT/"audit.py",ROOT/"PLAN.md",ROOT/"prereg.json"]},
    }
    (out/"formal.json").write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"formal_rows":len(rows),"controls":len(controls)},sort_keys=True))
if __name__=="__main__": main()
