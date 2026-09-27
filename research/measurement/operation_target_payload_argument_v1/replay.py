from __future__ import annotations
import argparse,collections,hashlib,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/"upstream"))
from generator import generate,corpus_digest
from schema import disp_key

SEED=113320260918001
EXPECTED="ea4a86baf3d2efc6f79f75703ef164d2c830cd3f5634e7ad057c26315da752dd"
FULL_OPS={"CLICK","TYPE_TEXT","SCROLL"}

def target_admissibility(f):
    if f["hard_invalid"]: return "STALE"
    if not f["requires_target"]: return "NOT_REQUIRED"
    valid=[t for t in f["targets"] if t["present"] and t["compatible"]]
    if not valid: return "MISSING"
    if f["ambiguous"]: return "AMBIGUOUS"
    return "CURRENT"

def augment(row):
    p=json.loads(json.dumps(row["candidate_input"]))
    p["target_admissibility"]=target_admissibility(row["oracle_facts"])
    f=row["oracle_facts"]
    p["payload_ref"]=f["payload_ref"] if f["operation"]=="TYPE_TEXT" and f["payload_available"] else None
    return p

def structural_signature(p):
    c=[]
    for cand in p["candidates"]:
        c.append((cand["role"],tuple(sorted(cand["ops"]))))
    return (
        tuple(sorted(p["allowed_operations"])),
        bool(p["payload_ref_present"]),
        p["target_admissibility"],
        p["payload_ref"] is not None,
        tuple(c),
    )

def rule(p):
    adm=p["target_admissibility"]
    if adm=="STALE": return {"op":"YIELD","reason":"STALE_STATE"}
    if adm=="AMBIGUOUS": return {"op":"YIELD","reason":"AMBIGUOUS_TARGET"}
    if adm=="MISSING": return {"op":"YIELD","reason":"MISSING_TARGET"}
    if adm=="NOT_REQUIRED":
        if set(p["allowed_operations"]) != FULL_OPS:
            return {"op":"YIELD","reason":"UNSUPPORTED_OPERATION"}
        return {"op":"NO_LOCAL_ACTION","reason":"ALREADY_SATISFIED"}
    if adm!="CURRENT": return {"op":"YIELD","reason":"UNSUPPORTED_OR_MALFORMED"}
    fields=[c for c in p["candidates"] if c["role"]=="field" and "TYPE_TEXT" in c["ops"]]
    if fields:
        if p["payload_ref"] is None: return {"op":"YIELD","reason":"PAYLOAD_MISSING"}
        return {"op":"TYPE_TEXT","target":fields[0]["id"],"payload_ref":p["payload_ref"]}
    scrolls=[c for c in p["candidates"] if c["role"]=="scroll_region" and "SCROLL" in c["ops"]]
    if scrolls: return {"op":"SCROLL","target":scrolls[0]["id"]}
    buttons=[c for c in p["candidates"] if c["role"]=="button" and "CLICK" in c["ops"]]
    if buttons: return {"op":"CLICK","target":buttons[0]["id"]}
    return {"op":"YIELD","reason":"UNSUPPORTED_OR_MALFORMED"}

def main(out):
    rows=generate(SEED,12)
    if corpus_digest(rows)!=EXPECTED: raise SystemExit("FAIL_INTEGRITY corpus digest")
    groups=collections.defaultdict(list); outputs=[]; pos=neg=exact=poscovered=negexact=falseexec=missing=0
    for row in rows:
        p=augment(row); sig=structural_signature(p); groups[sig].append(row)
        proposal=rule(p); acceptable=row["acceptable"]; member=disp_key(proposal) in {disp_key(x) for x in acceptable}
        ispos=not row["semantic_negative"]
        if ispos: pos+=1; poscovered+=int(member)
        else:
            neg+=1; negexact+=int(member)
            falseexec+=int(proposal["op"] in ("CLICK","TYPE_TEXT","SCROLL"))
        if row["role"]=="TYPE_PAYLOAD" and p["payload_ref"] is None: missing+=1
        exact+=int(member)
        outputs.append({"row_id":row["row_id"],"proposal":proposal,"member":member,"signature":repr(sig)})
    conflicts=0
    for sig, rs in groups.items():
        common=None
        for row in rs:
            s={disp_key(x) for x in row["acceptable"]}
            common=s if common is None else common&s
        if not common: conflicts+=1
    errors=[]
    if (len(rows),pos,neg)!=(96,48,48): errors.append("counts")
    if falseexec: errors.append("false_exec")
    if conflicts: errors.append("conflicts")
    if missing: errors.append("missing_argument")
    if exact!=96 or poscovered!=48 or negexact!=48: errors.append("not_full_closure")
    decision="HOLD_NO_LEARNED_RESIDUAL_AFTER_ARGUMENT_COMPLETION" if not errors else ("FAIL_UNSAFE_RULE" if falseexec else "HOLD_REPRESENTATION_NOT_SUFFICIENT")
    result={
        "task":"OPERATION-TARGET-PAYLOAD-ARGUMENT-COMPLETENESS-20260918-001",
        "primary_invocations":1,"reruns":0,"rows":96,"positives":pos,"semantic_negatives":neg,
        "exact_membership":exact,"positive_coverage":poscovered,"semantic_negative_exact":negexact,
        "false_executable_negatives":falseexec,"incompatible_structural_signatures":conflicts,
        "missing_required_arguments":missing,"decision":decision,"errors":errors,
        "corpus_semantic_digest":EXPECTED,"model_calls":0,"gui_actions":0,"task_input_actions":0,
        "outputs":outputs,
    }
    Path(out).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k!="outputs"},sort_keys=True))
if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--out",required=True);a=ap.parse_args();main(a.out)
