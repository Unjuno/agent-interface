import json,sys,hashlib
from collections import deque
from functools import lru_cache

BUDGET=4
WORKERS=("A","B")
MAX_DEPTH=6

def start():
    return {"rights":{"r0":{"owner":"A","generation":0,"state":"HELD","transfer_id":None},"r1":{"owner":"A","generation":0,"state":"HELD","transfer_id":None},
                      "r2":{"owner":"B","generation":0,"state":"HELD","transfer_id":None},"r3":{"owner":"B","generation":0,"state":"HELD","transfer_id":None}},
            "worker_generation":{"A":0,"B":0},"crashed":{"A":False,"B":False},"transfers":{},"transfer_sequence":0,"consumed":[],"coordination":2,
            "mandatory_served":0,"consequential_actions":0}

def canon(s): return json.dumps(s,sort_keys=True,separators=(",",":"))

def ops(s):
    out=[]
    for w in WORKERS:
        if s["crashed"][w]: out.append({"op":"restart","worker":w})
        else:
            for rid,x in sorted(s["rights"].items()):
                if x["owner"]==w and x["generation"]==s["worker_generation"][w] and x["state"]=="HELD":
                    out.append({"op":"consume","worker":w,"right":rid,"generation":s["worker_generation"][w]})
            out.append({"op":"crash","worker":w})
        out.append({"op":"heartbeat_reclaim","worker":w})
    for rid,x in sorted(s["rights"].items()):
        if x["state"]=="HELD" and not s["crashed"][x["owner"]]:
            to={"A":"B","B":"A"}[x["owner"]]
            if not s["crashed"][to]:
                out.append({"op":"surrender","right":rid,"from":x["owner"],"to":to,"generation":x["generation"],
                            "transfer_id":f"x-{rid}-{s['transfer_sequence']}"})
    for tid,x in sorted(s["transfers"].items()):
        if not x["acknowledged"]: out.append({"op":"transfer_ack","transfer_id":tid})
        else: out.append({"op":"transfer_ack","transfer_id":tid})
    return out

def transition(old,event):
    n=json.loads(canon(old));op=event["op"];ok=True;reason="accepted"
    if op["op"]=="consume":
        r=n["rights"][op["right"]];w=op["worker"]
        if n["crashed"][w] or r["owner"]!=w or r["generation"]!=op["generation"] or n["worker_generation"][w]!=op["generation"] or r["state"]!="HELD":
            ok=False;reason="STALE_OR_UNOWNED_RIGHT"
        else:
            r["state"]="CONSUMED";n["consumed"].append({"right":op["right"],"worker":w,"generation":op["generation"]})
    elif op["op"]=="crash":
        w=op["worker"]
        if n["crashed"][w]:ok=False;reason="ALREADY_CRASHED"
        else:n["crashed"][w]=True
    elif op["op"]=="restart":
        w=op["worker"]
        if not n["crashed"][w]:ok=False;reason="NOT_CRASHED"
        else:n["crashed"][w]=False;n["worker_generation"][w]+=1
    elif op["op"]=="heartbeat_reclaim":
        ok=False;reason="FENCED_SURRENDER_REQUIRED"
    elif op["op"]=="surrender":
        r=n["rights"][op["right"]];w=op["from"]
        if r["owner"]!=w or r["generation"]!=op["generation"] or r["state"]!="HELD" or n["crashed"][w] or n["worker_generation"][w]!=op["generation"]:
            ok=False;reason="SURRENDER_NOT_FENCED"
        else:
            r["state"]="IN_TRANSFER";r["transfer_id"]=op["transfer_id"];n["transfers"][op["transfer_id"]]={"right":op["right"],"from":w,"to":op["to"],"old_generation":op["generation"],"acknowledged":False};n["coordination"]+=1;n["transfer_sequence"]+=1
    elif op["op"]=="transfer_ack":
        t=n["transfers"][op["transfer_id"]];r=n["rights"][t["right"]]
        if t["acknowledged"]:ok=False;reason="DUPLICATE_ACK_IDEMPOTENT"
        elif r["state"]!="IN_TRANSFER":ok=False;reason="TRANSFER_STATE_MISMATCH"
        else:r.update({"owner":t["to"],"generation":n["worker_generation"][t["to"]],"state":"HELD","transfer_id":None});t["acknowledged"]=True
    else:ok=False;reason="UNKNOWN_OPERATION"
    return n,ok,reason

def invariant(s):
    ids=list(s["rights"])
    if len(ids)!=BUDGET or len(set(ids))!=BUDGET:return False
    if any(r["state"] not in {"HELD","CONSUMED","IN_TRANSFER","RETURNED"} for r in s["rights"].values()):return False
    if len({x["right"] for x in s["consumed"]})!=len(s["consumed"]):return False
    if any(x["right"] not in s["rights"] or s["rights"][x["right"]]["state"]!="CONSUMED" for x in s["consumed"]):return False
    if sum(r["state"]=="CONSUMED" for r in s["rights"].values())!=len(s["consumed"]):return False
    if any(r["owner"] not in WORKERS or type(r["generation"]) is not int or r["generation"]<0 for r in s["rights"].values()):return False
    pending={tid for tid,t in s["transfers"].items() if not t["acknowledged"]}
    referenced={r["transfer_id"] for r in s["rights"].values() if r["state"]=="IN_TRANSFER"}
    if pending!=referenced:return False
    if s["coordination"]!=2+len(s["transfers"]):return False
    for rid,r in s["rights"].items():
        if r["state"]=="IN_TRANSFER" and (r["transfer_id"] not in s["transfers"] or s["transfers"][r["transfer_id"]]["right"]!=rid):return False
        if r["state"]!="IN_TRANSFER" and r["transfer_id"] is not None:return False
        if r["state"]=="HELD" and r["generation"]>s["worker_generation"][r["owner"]]:return False
        if r["state"]=="CONSUMED" and not any(x["right"]==rid and x["worker"]==r["owner"] and x["generation"]==r["generation"] for x in s["consumed"]):return False
    return True

@lru_cache(maxsize=1)
def enumerate_independently():
    first=start();seen={canon(first)};q=deque([(first,0)]);edges=[]
    while q:
        s,d=q.popleft()
        if d==MAX_DEPTH:continue
        for op in ops(s):
            n,ok,reason=transition(s,{"op":op})
            if not invariant(n):return None,None,"invariant_violation"
            edges.append({"from":canon(s),"to":canon(n),"operation":op,"accepted":ok,"reason":reason})
            k=canon(n)
            if k not in seen:seen.add(k);q.append((n,d+1))
    return seen,edges,None

def audit(result):
    errors=[]
    enum=result.get("enumeration",{})
    seen,edges,error=enumerate_independently()
    if error:errors.append(error)
    if enum.get("max_depth")!=MAX_DEPTH:errors.append("depth")
    if enum.get("states_sha256")!=hashlib.sha256(("\n".join(sorted(seen))+"\n").encode()).hexdigest():errors.append("reachable_state_digest")
    if enum.get("edges_sha256")!=hashlib.sha256(("\n".join(sorted(canon(x) for x in edges))+"\n").encode()).hexdigest():errors.append("transition_edge_digest")
    if enum.get("reachable_states")!=len(seen):errors.append("state_count")
    if enum.get("transition_edges")!=len(edges):errors.append("edge_count")
    c=result.get("controls",{})
    def independent_demand(demand):
        caps={"A":2,"B":2}
        served=sum(min(demand[w],caps[w]) for w in WORKERS)
        central=min(sum(demand.values()),BUDGET)
        return {"budget":BUDGET,"demand":demand,"allocation":caps,
                "central_per_use_roundtrips":sum(demand.values()),"escrow_setup_roundtrips":len(WORKERS),
                "escrow_optional_completed":served,"central_optional_completed":central,
                "stranded_rights":sum(caps.values())-served}
    bal=c.get("balanced",{})
    if any(bal.get(k)!=v for k,v in independent_demand({"A":2,"B":2}).items()) or bal.get("mandatory_verifier_served")!=1:errors.append("balanced_positive_control")
    skew=c.get("skew",{})
    if any(skew.get(k)!=v for k,v in independent_demand({"A":4,"B":0}).items()):errors.append("skew_availability_cost")
    crash=c.get("crash_stranded",{})
    if (crash.get("old_generation_rights_reusable") is not False or crash.get("generation_after_restart")!=1
            or any(crash.get(k)!=v for k,v in independent_demand({"A":4,"B":0}).items())):errors.append("crash_fencing")
    trans=c.get("fenced_transfer",{})
    if (trans.get("first_ack_accepted") is not True or trans.get("duplicate_ack_accepted") is not False
            or trans.get("right_identities")!=BUDGET or trans.get("second_transfer_ack") is not True
            or trans.get("delayed_old_ack_accepted") is not False or trans.get("owner_after_old_ack")!="B"
            or trans.get("transfer_ids_distinct") is not True):errors.append("duplicate_transfer_ack")
    stale=c.get("stale_restart",{})
    if stale.get("old_ticket_accepted") is not False or stale.get("current_generation")!=1:errors.append("stale_generation")
    hb=c.get("heartbeat_reclaim",{})
    if hb.get("mutant_actual_consumes")<=hb.get("global_budget") or hb.get("required")!="FENCED_SURRENDER_REQUIRED":errors.append("heartbeat_counterexample")
    mandatory=c.get("mandatory_after_optional_exhaustion",{})
    if mandatory.get("mandatory_verifier_served")!=mandatory.get("mandatory_verifier_capacity") or mandatory.get("consequential_action_allowed_before_verifier") is not False:errors.append("mandatory_lane")
    role=c.get("role_ambiguity",{})
    if (role.get("ambiguous")!="HOLD_ROLE_AMBIGUOUS" or role.get("stale_self_labeled_optional")!="MANDATORY_VERIFIER"
            or role.get("routine_self_labeled_mandatory")!="OPTIONAL_RECAPTURE"
            or role.get("contract_mandatory")!="MANDATORY_VERIFIER" or role.get("consequential_action_allowed") is not False):errors.append("role_ambiguity")
    unavailable=c.get("mandatory_unavailable",{})
    if unavailable.get("disposition")!="YIELD" or unavailable.get("consequential_action_allowed") is not False:errors.append("mandatory_unavailable")
    return {"status":"PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD_SCOPED","reachable_states":len(seen),"transition_edges":len(edges),"global_budget":BUDGET,"errors":errors}

def main(src,dst):
    result=json.load(open(src));report=audit(result);json.dump(report,open(dst,"w"),indent=2,sort_keys=True);open(dst,"a").write("\n");print(json.dumps(report,sort_keys=True));return 0 if not report["errors"] else 1
if __name__=="__main__":raise SystemExit(main(*sys.argv[1:3]))
