"""Candidate current-single-map and typed graph estimators (stdlib only)."""
import itertools, json, sys

def paths(edges, start, end, epoch, unit, context):
    if start == end: return [[]]
    out=[]
    def walk(node, used, chain):
        if node == end: out.append(chain); return
        for i,e in enumerate(edges):
            if i not in used and e["src"] == node and e["epoch"] == epoch and e["unit"] == unit and e["context"] == context:
                walk(e["dst"], used|{i}, chain+[e])
    walk(start,set(),[])
    return out

def apply(p,t): return [t["sx"]*p[0]+t["tx"],t["sy"]*p[1]+t["ty"]]

def assignments(edges):
    opts={e["id"]:e["options"] for e in edges}
    for vs in itertools.product(*(opts[k] for k in sorted(opts))): yield dict(zip(sorted(opts),vs))

def compose(path, assignment):
    t={"sx":1,"sy":1,"tx":0,"ty":0}
    for e in path:
        n=assignment[e["id"]]
        t={"sx":n["sx"]*t["sx"],"sy":n["sy"]*t["sy"],"tx":n["sx"]*t["tx"]+n["tx"],"ty":n["sy"]*t["ty"]+n["ty"]}
    return t

def evaluate(c):
    if c.get("non_affine") or c.get("binding_epoch",c["epoch"])!=c["epoch"] or c["action"].get("target_identity")!=c["target"].get("identity"):
        return {"case_id":c["case_id"],"graph":"UNKNOWN","baseline":"UNKNOWN","reason":"invalid_binding_or_model"}
    tp=paths(c["edges"],c["target"]["frame"],"input",c["epoch"],c["unit"],c["context"])
    ap=paths(c["edges"],c["action"]["frame"],"input",c["epoch"],c["unit"],c["context"])
    if len(tp)!=1 or len(ap)!=1: return {"case_id":c["case_id"],"graph":"UNKNOWN","baseline":"UNKNOWN","reason":"missing_or_ambiguous_path"}
    worlds=[]
    for a in assignments(c["edges"]):
        tt,at=compose(tp[0],a),compose(ap[0],a); b=c["target"]["box"]
        p0,p1=apply([b[0],b[1]],tt),apply([b[2],b[3]],tt); p=apply(c["action"]["point"],at)
        boxes=[[min(p0[0],p1[0]),min(p0[1],p1[1]),max(p0[0],p1[0]),max(p0[1],p1[1])]]
        for fb in c.get("forbidden",[]):
            q0,q1=apply([fb[0],fb[1]],tt),apply([fb[2],fb[3]],tt)
            boxes.append([min(q0[0],q1[0]),min(q0[1],q1[1]),max(q0[0],q1[0]),max(q0[1],q1[1])])
        worlds.append({"boxes":boxes,"point":p})
    graph="ADMIT" if all(w["boxes"][0][0]<=w["point"][0]<=w["boxes"][0][2] and w["boxes"][0][1]<=w["point"][1]<=w["boxes"][0][3] and not any(b[0]<=w["point"][0]<=b[2] and b[1]<=w["point"][1]<=b[3] for b in w["boxes"][1:]) for w in worlds) else "UNKNOWN"
    baseline="UNKNOWN"
    if c.get("baseline") is not None and c["target"]["frame"]==c["action"]["frame"]:
        t=c["baseline"]; b=c["target"]["box"]
        p=apply(c["action"]["point"],t); q0,q1=apply([b[0],b[1]],t),apply([b[2],b[3]],t)
        baseline="ADMIT" if min(q0[0],q1[0])<=p[0]<=max(q0[0],q1[0]) and min(q0[1],q1[1])<=p[1]<=max(q0[1],q1[1]) else "UNKNOWN"
    return {"case_id":c["case_id"],"graph":graph,"baseline":baseline,"worlds":worlds}

def main():
    cases=[json.loads(s) for s in open(sys.argv[1]) if s.strip()]
    with open(sys.argv[2],"w") as f:
        for c in cases: f.write(json.dumps(evaluate(c),sort_keys=True)+"\n")
if __name__=="__main__": main()
