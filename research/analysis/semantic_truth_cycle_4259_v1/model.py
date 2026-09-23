from __future__ import annotations

BASES=("anchor","gate","unrelated")
DERIVED=("A","B","C","D")
SUPPORTS={
    "A": (("anchor",), ("B",)),
    "B": (("A",),),
    "C": (("B","gate"),),
    "D": (("unrelated",),),
}
DEPENDENTS={"anchor":{"A"},"gate":{"C"},"unrelated":{"D"},"A":{"B"},"B":{"A","C"},"C":set(),"D":set()}
VALUES={"TRUE","FALSE","UNKNOWN"}

def and3(vals):
    vals=list(vals)
    if any(v=="FALSE" for v in vals): return "FALSE"
    if vals and all(v=="TRUE" for v in vals): return "TRUE"
    return "UNKNOWN"

def or3(vals):
    vals=list(vals)
    if any(v=="TRUE" for v in vals): return "TRUE"
    if vals and all(v=="FALSE" for v in vals): return "FALSE"
    return "UNKNOWN"

def oracle(base):
    cur={d:"UNKNOWN" for d in DERIVED}
    for _ in range(16):
        nxt=dict(cur)
        for d in DERIVED:
            groups=[]
            for supp in SUPPORTS[d]:
                vals=[base[x] if x in base else cur[x] for x in supp]
                groups.append(and3(vals))
            nxt[d]=or3(groups)
        if nxt==cur: break
        cur=nxt
    return cur

def local_support_retain(prev, base):
    cur=dict(prev)
    for _ in range(16):
        nxt=dict(cur)
        for d in DERIVED:
            groups=[]
            for supp in SUPPORTS[d]:
                groups.append(and3(base[x] if x in base else cur[x] for x in supp))
            nxt[d]=or3(groups)
        if nxt==cur: break
        cur=nxt
    return cur

def affected(changed):
    q=list(changed); seen=set()
    while q:
        x=q.pop(0)
        for y in DEPENDENTS.get(x,()):
            if y not in seen:
                seen.add(y); q.append(y)
    return seen

def scc_grounded_retract(prev, base, changed):
    target=oracle(base)
    region=affected(changed)
    cur=dict(prev)
    for d in region:
        cur[d]=target[d]
    return cur, region

def macro_ready(vals):
    return and3([vals["C"], vals["D"]])
