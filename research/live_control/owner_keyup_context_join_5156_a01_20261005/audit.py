"""Raw-only source-pinned auditor for per-admission to owner-key-up composition."""
import copy, hashlib, json, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent; RESULT=Path(sys.argv[1])
freeze=json.loads((HERE/"FREEZE.json").read_text()); raw=json.loads(RESULT.read_text()); errors=[]
def sha(p): return hashlib.sha256((HERE/p).read_bytes()).hexdigest()
for p,h in freeze["sha256"].items():
    if sha(p)!=h: errors.append("hash mismatch: "+p)
if raw.get("runner_error") is not None: errors.append("runner error")
expected={"reverse":("trial-reverse",7,{"A":[0],"B":[1]},[("A",0),("B",1)],[("B",1),("A",0)]),
          "cycles":("trial-cycles",11,{"C":[0,1]},[("C",0),("C",1)],[("C",0),("C",1)])}

def inspect(doc):
    bad=[]
    cases=doc.get("cases",[])
    if [c.get("name") for c in cases] != ["reverse","cycles"]: return ["case order/set"]
    for c in cases:
        name=c["name"]; identifier,step,expected_positions,admission_order,release_order=expected[name]
        if c.get("identifier")!=identifier or c.get("step")!=step: bad.append(name+": case context")
        if c.get("final_down")!=[]: bad.append(name+": non-neutral keymap")
        if not any(r.get("event")=="owner_release" and r.get("verified") is True and r.get("keys_down")==[] for r in c.get("owner_records",[])):
            bad.append(name+": missing neutral owner cleanup")
        admissions=[r for r in c.get("events",[]) if r.get("event")=="input_admission"]
        releases=[r for r in c.get("events",[]) if r.get("event")=="input_release_transition"]
        owner_rows=[r for r in c.get("owner_records",[]) if r.get("event")=="owner_keyup"]
        expected_n=2 if name=="reverse" else 2
        if len(admissions)!=expected_n or len(releases)!=expected_n: bad.append(name+": admission/release cardinality")
        if len(owner_rows)!=len(releases): bad.append(name+": owner/release receipt cardinality")
        if [(r.get("key"),r.get("admission_position")) for r in admissions]!=admission_order:
            bad.append(name+": admission order/positions")
        amap={}
        for row in admissions:
            key=row.get("key"); pos=row.get("admission_position")
            if (row.get("id"),row.get("step"),row.get("owner_id"),row.get("intent_token")) != (identifier,step,c.get("owner_id"),c.get("intent_token")):
                bad.append(name+": admission identity")
            if type(pos) is not int: bad.append(name+": malformed admission position")
            amap.setdefault(key,[]).append(pos)
        for key, positions in amap.items(): positions.sort()
        for index,row in enumerate(releases):
            key=row.get("key"); owner=row.get("owner_keyup_receipt")
            if not isinstance(owner,dict): bad.append(name+": missing nested owner receipt"); continue
            expected_key, expected_pos=release_order[index] if index < len(release_order) else (None,None)
            if key!=expected_key or expected_pos not in amap.get(key,[]): bad.append(name+": wrong admission context")
            if (row.get("id"),row.get("step"),row.get("admission_position"),row.get("admission_identity_status")) != (identifier,step,expected_pos,"matched"):
                bad.append(name+": release context mismatch")
            if (owner.get("owner_id"),owner.get("intent_token"),owner.get("key"),owner.get("keycode"),owner.get("reason")) != (c.get("owner_id"),c.get("intent_token"),key,{"A":38,"B":56,"C":54}[key],"explicit_up"):
                bad.append(name+": nested owner identity/key mismatch")
            a,b=owner.get("owner_keyup_started_ns"),owner.get("owner_sync_returned_ns")
            if owner.get("xsync_completed") is not True or type(a) is not int or type(b) is not int or a>b:
                bad.append(name+": owner interval invalid")
            if not (type(row.get("release_call_started_ns")) is int and type(row.get("release_call_returned_ns")) is int
                    and row["release_call_started_ns"]<=a<=b<=row["release_call_returned_ns"]):
                bad.append(name+": caller/owner nesting")
            if row.get("release_batch_identifier")!=identifier or row.get("release_batch_step")!=step:
                bad.append(name+": release batch context")
            if row.get("physical_verification_authoritative") is not False or row.get("grants_input_authority") is not False or owner.get("grants_input_authority") is not False:
                bad.append(name+": authority overclaim")
            if row.get("owner_transition_verified") is not True: bad.append(name+": existing batch outcome changed")
        actual_pairs=[(r.get("key"),r.get("admission_position")) for r in releases]
        if actual_pairs!=release_order: bad.append(name+": release keys/positions missing or out of order")
        # Exact fake XTest/XSync order: A/B down, then the declared up sequence, then close cleanup sync.
        codes={"A":38,"B":56,"C":54}; down_keys=[r["key"] for r in admissions]
        up_keys=[r["key"] for r in releases]
        wanted=[]; ordinal=0
        for key in down_keys: wanted.extend([["input",2,codes[key]]]); ordinal+=1; wanted.append(["sync",ordinal])
        for key in up_keys: wanted.append(["input",3,codes[key]]); ordinal+=1; wanted.append(["sync",ordinal])
        ordinal+=1; wanted.append(["sync",ordinal])
        if c.get("calls")!=wanted: bad.append(name+": XTest/XSync order differs")
    return bad

base=inspect(raw); errors.extend(base)
mutations=[]
def mutate(fn):
    d=copy.deepcopy(raw); fn(d); mutations.append(d)
if raw.get("cases"):
    mutate(lambda d: d["cases"][0]["events"][-1]["owner_keyup_receipt"].update(owner_keyup_started_ns=10**30))
    mutate(lambda d: d["cases"][0]["events"][-1].update(id="wrong"))
    mutate(lambda d: d["cases"][0]["events"][-1]["owner_keyup_receipt"].update(intent_token="wrong"))
    mutate(lambda d: d["cases"][0]["events"][-1]["owner_keyup_receipt"].update(keycode=999))
    mutate(lambda d: d["cases"][0]["events"][-1].update(physical_verification_authoritative=True))
    mutate(lambda d: d["cases"][0]["events"].remove(next(r for r in d["cases"][0]["events"] if r.get("event")=="input_admission")))
rejected=sum(bool(inspect(d)) for d in mutations)
if rejected!=len(mutations): errors.append("mutation controls not all rejected")
report={"schema":"owner-keyup-context-join-audit-v1","result_sha256":hashlib.sha256(RESULT.read_bytes()).hexdigest(),
        "base_error_count":len(base),"mutation_count":len(mutations),"mutation_rejections":rejected,
        "errors":errors,"decision":"PASS_OWNER_KEYUP_CONTEXT_JOIN_SCOPED" if not errors else "FAIL"}
(RESULT.parent/"AUDIT.json").write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
print(json.dumps(report,sort_keys=True)); raise SystemExit(0 if not errors else 1)
