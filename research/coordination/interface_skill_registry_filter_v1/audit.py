from __future__ import annotations
import argparse, hashlib, json, pathlib, sys

def sha256(path):
    h=hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--result",required=True); ap.add_argument("--source-dir",required=True); ap.add_argument("--out",required=True); args=ap.parse_args()
    result_path=pathlib.Path(args.result); src=pathlib.Path(args.source_dir)
    data=json.loads(result_path.read_text())
    errors=[]; gates={}
    for name, expected in data["source_sha256"].items():
        actual=sha256(src/name)
        if actual != expected: errors.append(f"SOURCE_MISMATCH:{name}")
    rows=data["rows"]
    cand=[r for r in rows if r["result"]["policy"]=="APPLICABILITY_AWARE"]
    base=[r for r in rows if r["result"]["policy"]=="SEMANTIC_ONLY"]
    gates["row_count_64"] = len(rows)==64 and len(cand)==32 and len(base)==32
    cand_ok=True; role_ok=True; identity_ok=True
    for r in cand:
        x=r["result"]
        if x["selected_key"] != r["expected_key"] or x["selected_status"] != r["expected_status"]: cand_ok=False; errors.append(f"CANDIDATE_SELECTION:{r['row_id']}")
        if x["detail_loaded"] != [x["selected_key"]]: cand_ok=False; errors.append(f"DETAIL_LOAD:{r['row_id']}")
        if not x["detail"] or x["detail"]["version"] != x["selected_version"] or x["detail"]["provenance"] != x["candidate_card"]["provenance"]: identity_ok=False; errors.append(f"IDENTITY:{r['row_id']}")
        if r["case_id"]=="hint_with_revalidation":
            rec=x["revalidation_receipt"]
            if not rec or rec["source_role"]!="HINT" or rec["output_role"]!="ADMISSION_DEPENDENCY" or rec["freshness"]!="CURRENT": role_ok=False; errors.append(f"REVALIDATION_ROLE:{r['row_id']}")
            if x["candidate_card"]["evidence_role"] != "HINT": role_ok=False; errors.append(f"HINT_MUTATED:{r['row_id']}")
        elif x["revalidation_receipt"] is not None:
            role_ok=False; errors.append(f"UNEXPECTED_REVALIDATION:{r['row_id']}")
    gates["candidate_expected_32_32"] = cand_ok
    gates["role_promotion_explicit"] = role_ok
    gates["identity_preserved"] = identity_ok
    baseline_exposes=0
    for r in base:
        x=r["result"]
        if (not x["candidate_hard_applicable"]) or x["candidate_status_if_checked"]=="REVALIDATION_REQUIRED": baseline_exposes += 1
    gates["baseline_discriminator_32_32"] = baseline_exposes==32
    prefilter_ok=True
    for r in cand:
        log=r["result"]["filter_log"]
        if r["case_id"] != "hint_with_revalidation":
            if not log or log[0]["ok"]: prefilter_ok=False; errors.append(f"NO_PREFILTER_REJECT:{r['row_id']}")
        else:
            if not log or not log[0]["ok"] or log[0]["status"]!="REVALIDATION_REQUIRED": prefilter_ok=False; errors.append(f"BAD_HINT_GATE:{r['row_id']}")
    gates["hard_filter_before_detail"] = prefilter_ok
    controls=data["malformed_controls"]
    gates["malformed_controls_4_4_reject"] = len(controls)==4 and all(not c["accepted"] for c in controls)
    decision="PASS_SKILL_APPLICABILITY_FILTER_SCOPED" if all(gates.values()) and not errors else "FAIL_SKILL_FILTER"
    out={"decision":decision,"gates":gates,"errors":errors,"result_sha256":sha256(result_path),"formal_reruns":0}
    pathlib.Path(args.out).write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,sort_keys=True))
    return 0 if decision.startswith("PASS") else 1
if __name__=="__main__": raise SystemExit(main())
