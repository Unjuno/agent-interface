from __future__ import annotations
import argparse,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/"upstream"))
from generator import generate,corpus_digest
from schema import disp_key
SEED=113320260918001
EXPECTED="ea4a86baf3d2efc6f79f75703ef164d2c830cd3f5634e7ad057c26315da752dd"

def adm(f):
    if f["hard_invalid"]:return "STALE"
    if not f["requires_target"]:return "NOT_REQUIRED"
    valid=[t for t in f["targets"] if t["present"] and t["compatible"]]
    if not valid:return "MISSING"
    if f["ambiguous"]:return "AMBIGUOUS"
    return "CURRENT"
def main(result_path):
    rows=generate(SEED,12);r=json.load(open(result_path));errors=[]
    if corpus_digest(rows)!=EXPECTED:errors.append("corpus")
    out={x["row_id"]:x for x in r["outputs"]}
    exact=pos=neg=falseexec=missing=0
    sigsets={}
    for row in rows:
        rec=out.get(row["row_id"])
        if rec is None:errors.append("missing_row");continue
        f=row["oracle_facts"];p=row["candidate_input"]; a=adm(f)
        payload=f["payload_ref"] if f["operation"]=="TYPE_TEXT" and f["payload_available"] else None
        if row["role"]=="TYPE_PAYLOAD" and payload is None:missing+=1
        prop=rec["proposal"]; member=disp_key(prop) in {disp_key(x) for x in row["acceptable"]}
        if member: exact+=1
        if row["semantic_negative"]:
            neg+=int(member); falseexec+=int(prop["op"] in ("CLICK","TYPE_TEXT","SCROLL"))
        else:pos+=int(member)
        sig=(tuple(sorted(p["allowed_operations"])),bool(p["payload_ref_present"]),a,payload is not None,tuple((c["role"],tuple(sorted(c["ops"]))) for c in p["candidates"]))
        sigsets.setdefault(repr(sig),[]).append({disp_key(x) for x in row["acceptable"]})
    conflicts=0
    for sets in sigsets.values():
        common=set(sets[0])
        for s in sets[1:]:common&=s
        conflicts+=not bool(common)
    expected=(96,48,48,0,0,0)
    actual=(exact,pos,neg,falseexec,conflicts,missing)
    if actual!=expected:errors.append(["metrics",actual])
    if r["decision"]!="HOLD_NO_LEARNED_RESIDUAL_AFTER_ARGUMENT_COMPLETION":errors.append("decision")
    if r["primary_invocations"]!=1 or r["reruns"]!=0:errors.append("identity")
    print(json.dumps({"pass":not errors,"errors":errors,"metrics":actual},sort_keys=True))
    raise SystemExit(bool(errors))
if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("result");a=ap.parse_args();main(a.result)
