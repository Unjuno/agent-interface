from __future__ import annotations
import argparse,json,sys
from collections import defaultdict
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
def normalize(p,d):
    z={"op":d["op"]}
    if "reason" in d:z["reason"]=d["reason"]
    if "target" in d:
        ids=[c["id"] for c in p["candidates"]]
        z["target_slot"]=ids.index(d["target"]) if d["target"] in ids else "UNBOUND"
    if "payload_ref" in d:z["payload_arg"]="PAYLOAD_PRESENT" if d["payload_ref"] is not None else "NULL"
    return tuple((k,z[k]) for k in sorted(z))
def main(path):
    rows=generate(SEED,12);r=json.load(open(path));errors=[];out={x["row_id"]:x for x in r["outputs"]}
    exact=pos=neg=falseexec=missing=0;groups=defaultdict(list)
    for row in rows:
        p=json.loads(json.dumps(row["candidate_input"]));f=row["oracle_facts"];p["target_admissibility"]=adm(f)
        p["payload_ref"]=f["payload_ref"] if f["operation"]=="TYPE_TEXT" and f["payload_available"] else None
        sig=(tuple(sorted(p["allowed_operations"])),bool(p["payload_ref_present"]),p["target_admissibility"],p["payload_ref"] is not None,tuple((c["role"],tuple(sorted(c["ops"]))) for c in p["candidates"]))
        groups[sig].append((row,p))
        rec=out.get(row["row_id"])
        if rec is None:errors.append("missing_row");continue
        prop=rec["proposal"];member=disp_key(prop) in {disp_key(x) for x in row["acceptable"]}
        exact+=int(member)
        if row["semantic_negative"]:
            neg+=int(member);falseexec+=int(prop["op"] in ("CLICK","TYPE_TEXT","SCROLL"))
        else:pos+=int(member)
        if row["role"]=="TYPE_PAYLOAD" and p["payload_ref"] is None:missing+=1
    conflicts=0
    for items in groups.values():
        common=None
        for row,p in items:
            s={normalize(p,d) for d in row["acceptable"]}
            common=s if common is None else common&s
        conflicts+=int(not bool(common))
    if corpus_digest(rows)!=EXPECTED:errors.append("corpus")
    metrics=(exact,pos,neg,falseexec,conflicts,missing)
    if metrics!=(96,48,48,0,0,0):errors.append(["metrics",metrics])
    if r["decision"]!="HOLD_NO_LEARNED_RESIDUAL_AFTER_ARGUMENT_COMPLETION":errors.append("decision")
    if r["primary_invocations"]!=1 or r["reruns"]!=0:errors.append("identity")
    print(json.dumps({"pass":not errors,"errors":errors,"metrics":metrics},sort_keys=True));raise SystemExit(bool(errors))
if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("result");a=ap.parse_args();main(a.result)
