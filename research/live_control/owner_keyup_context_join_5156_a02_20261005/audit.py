"""Raw-only source-pinned auditor for per-admission to owner-key-up composition."""
import copy, hashlib, json, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent; RESULT=Path(sys.argv[1])
freeze=json.loads((HERE/"FREEZE.json").read_text()); raw=json.loads(RESULT.read_text()); errors=[]
def sha(p): return hashlib.sha256((HERE/p).read_bytes()).hexdigest()
for p,h in freeze["sha256"].items():
    if sha(p)!=h: errors.append("hash mismatch: "+p)
if raw.get("runner_error") is not None: errors.append("runner error")
specs={
 "single":{"id":"trial-single","step":3,"admissions":[("A",0)],"releases":[("A",0)],"ops":[("down","A"),("up","A")]},
 "reverse":{"id":"trial-reverse","step":7,"admissions":[("A",0),("B",1)],"releases":[("B",1),("A",0)],"ops":[("down","A"),("down","B"),("up","B"),("up","A")]},
 "cycles":{"id":"trial-cycles","step":11,"admissions":[("C",0),("C",1)],"releases":[("C",0),("C",1)],"ops":[("down","C"),("up","C"),("down","C"),("up","C")]},
}

def inspect(doc):
    bad=[]; cases=doc.get("cases",[])
    if [c.get("name") for c in cases] != ["single","reverse","cycles"]: return ["case set/order"]
    for c in cases:
        name=c["name"]; s=specs[name]; ident,step=s["id"],s["step"]
        if c.get("identifier")!=ident or c.get("step")!=step: bad.append(name+": case context")
        if c.get("final_down")!=[]: bad.append(name+": non-neutral keymap")
        if not any(r.get("event")=="owner_release" and r.get("verified") is True and r.get("keys_down")==[] and r.get("buttons_down")==[] for r in c.get("owner_records",[])):
            bad.append(name+": missing verified neutral cleanup")
        admissions=[r for r in c.get("events",[]) if r.get("event")=="input_admission"]
        releases=[r for r in c.get("events",[]) if r.get("event")=="input_release_transition"]
        owner_rows=[r for r in c.get("owner_records",[]) if r.get("event")=="owner_keyup"]
        if len(admissions)!=len(s["admissions"]) or len(releases)!=len(s["releases"]) or len(owner_rows)!=len(releases):
            bad.append(name+": admission/release/owner receipt cardinality")
        if [(r.get("key"),r.get("admission_position")) for r in admissions]!=s["admissions"]:
            bad.append(name+": admission order/position")
        for row in admissions:
            if (row.get("id"),row.get("step"),row.get("owner_id"),row.get("intent_token"))!=(ident,step,c.get("owner_id"),c.get("intent_token")):
                bad.append(name+": admission identity")
        actual_releases=[(r.get("key"),r.get("admission_position")) for r in releases]
        if actual_releases!=s["releases"]: bad.append(name+": release order/context")
        codes={"A":38,"B":56,"C":54}
        for index,row in enumerate(releases):
            if index>=len(s["releases"]): bad.append(name+": extra release row"); continue
            owner=row.get("owner_keyup_receipt")
            if not isinstance(owner,dict): bad.append(name+": missing nested owner receipt"); continue
            key,pos=s["releases"][index]
            if (row.get("id"),row.get("step"),row.get("admission_position"),row.get("admission_identity_status"))!=(ident,step,pos,"matched"):
                bad.append(name+": release identity context")
            if row.get("release_batch_identifier")!=ident or row.get("release_batch_step")!=step:
                bad.append(name+": release batch context")
            owner_record_id=owner_rows[index].get("receipt_id") if index<len(owner_rows) else None
            if (owner.get("receipt_id"),owner.get("owner_id"),owner.get("intent_token"),owner.get("key"),owner.get("keycode"),owner.get("reason"))!=(owner_record_id,c.get("owner_id"),c.get("intent_token"),key,codes[key],"explicit_up"):
                bad.append(name+": nested owner receipt identity/key")
            a,b=owner.get("owner_keyup_started_ns"),owner.get("owner_sync_returned_ns")
            if owner.get("xsync_completed") is not True or type(a) is not int or type(b) is not int or a>b:
                bad.append(name+": invalid owner interval")
            if not(type(row.get("release_call_started_ns")) is int and type(row.get("release_call_returned_ns")) is int
                   and row["release_call_started_ns"]<=a<=b<=row["release_call_returned_ns"]):
                bad.append(name+": caller/owner interval nesting")
            if row.get("owner_transition_verified") is not True: bad.append(name+": batch outcome changed")
            if row.get("physical_verification_authoritative") is not False or row.get("grants_input_authority") is not False:
                bad.append(name+": release authority overclaim")
            if owner.get("physical_verification_authoritative") is not False or owner.get("grants_input_authority") is not False:
                bad.append(name+": owner authority overclaim")
        # Reconstruct interleaved XTest operations per case; every key request has its existing sync.
        wanted=[]; ordinal=0
        for operation,key in s["ops"]:
            wanted.append(["input",2 if operation=="down" else 3,codes[key]])
            ordinal+=1; wanted.append(["sync",ordinal])
        ordinal+=1; wanted.append(["sync",ordinal]) # close lifecycle's empty cleanup
        if c.get("calls")!=wanted: bad.append(name+": XTest/XSync order differs")
    return bad

base=inspect(raw); errors.extend(base); mutations=[]
def mutate(fn):
    d=copy.deepcopy(raw); fn(d); mutations.append(d)
if raw.get("cases"):
    mutate(lambda d:d["cases"][0]["events"][-1]["owner_keyup_receipt"].update(owner_keyup_started_ns=10**30))
    mutate(lambda d:d["cases"][0]["events"][-1].update(id="wrong"))
    mutate(lambda d:d["cases"][0]["events"][-1]["owner_keyup_receipt"].update(intent_token="wrong"))
    mutate(lambda d:d["cases"][0]["events"][-1]["owner_keyup_receipt"].update(keycode=999))
    mutate(lambda d:d["cases"][0]["events"][-1].update(physical_verification_authoritative=True))
    mutate(lambda d:d["cases"][0]["events"].remove(next(r for r in d["cases"][0]["events"] if r.get("event")=="input_admission")))
    mutate(lambda d:d["cases"][1]["events"][-1].update(owner_keyup_receipt=None))
    mutate(lambda d:d["cases"][2]["events"].append(copy.deepcopy(d["cases"][2]["events"][-1])))
rejected=sum(bool(inspect(d)) for d in mutations)
if rejected!=len(mutations): errors.append("mutation controls not all rejected")
report={"schema":"owner-keyup-context-join-audit-v1","result_sha256":hashlib.sha256(RESULT.read_bytes()).hexdigest(),
        "base_error_count":len(base),"mutation_count":len(mutations),"mutation_rejections":rejected,
        "errors":errors,"decision":"PASS_OWNER_KEYUP_CONTEXT_JOIN_SCOPED" if not errors else "FAIL"}
(RESULT.parent/"AUDIT.json").write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
print(json.dumps(report,sort_keys=True)); raise SystemExit(0 if not errors else 1)
