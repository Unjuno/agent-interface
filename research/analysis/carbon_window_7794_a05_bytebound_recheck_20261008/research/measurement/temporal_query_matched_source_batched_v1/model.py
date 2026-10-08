from __future__ import annotations
import hashlib

MASTER_SEED = 149820260918002
FRAME_BUDGET = 4
BYTE_BUDGET = 512
FRAME_BYTES = 128
CLASSES = ("RECENT_DENSE","LONG_BASELINE","EVENT_CENTERED","REVERSAL_BRACKET")
FIXED_TARGETS_MS = (0,40,120,260)


def digest_for(index:int)->bytes:
    return hashlib.sha256(f"{MASTER_SEED}:{index}".encode()).digest()


def history(index:int):
    d=digest_for(index)
    scope=f"scope-{d[1]%4}"
    klass=CLASSES[d[0]%4]
    frames=[]
    # exact current + historical frames, with deterministic bounded missingness
    for age_slot in range(16):
        if age_slot and d[age_slot] < 32:
            continue
        frames.append({"id":f"{index}:{scope}:{age_slot}","scope":scope,"age_ms":age_slot*20,"bytes":FRAME_BYTES,"historical":True})
    # same retained source also contains one cross-scope decoy and one post-decision/future decoy.
    frames.append({"id":f"{index}:decoy:7","scope":f"scope-{(int(scope[-1])+1)%4}","age_ms":140,"bytes":FRAME_BYTES,"historical":True})
    frames.append({"id":f"{index}:{scope}:future","scope":scope,"age_ms":-20,"bytes":FRAME_BYTES,"historical":False})
    center_options={"EVENT_CENTERED":(80,120,160,200),"REVERSAL_BRACKET":(60,100,140,180)}
    center=None
    if klass in center_options:
        center=center_options[klass][d[16]%4]
    req={"class":klass,"center_ms":center,"scope":scope,"decision_age_ms":0}
    return frames,req


def eligible(frames,req):
    return [f for f in frames if f["scope"]==req["scope"] and f["age_ms"]>=0 and f["historical"]]


def nearest_unique(pool,targets):
    picked=[]; used=set()
    for t in targets:
        options=[f for f in pool if f["id"] not in used]
        if not options: break
        f=min(options,key=lambda x:(abs(x["age_ms"]-t),x["age_ms"],x["id"]))
        picked.append(f);used.add(f["id"])
    return picked[:FRAME_BUDGET]


def select_fixed(frames,req):
    return nearest_unique(eligible(frames,req),FIXED_TARGETS_MS)


def select_query(frames,req):
    pool=eligible(frames,req)
    k=req["class"]
    if k=="RECENT_DENSE":
        return sorted(pool,key=lambda x:(x["age_ms"],x["id"]))[:FRAME_BUDGET]
    if k=="LONG_BASELINE":
        if not pool:return []
        ages=[0,80,180,300]
        return nearest_unique(pool,ages)
    c=req["center_ms"]
    if k=="EVENT_CENTERED":
        return nearest_unique(pool,(c-20,c,c+20,0))
    if k=="REVERSAL_BRACKET":
        return nearest_unique(pool,(c-20,c+20,c-40,c+40))
    raise ValueError(k)


def validate_selection(sel,req):
    if len(sel)>FRAME_BUDGET:return "FRAME_BUDGET"
    if sum(f["bytes"] for f in sel)>BYTE_BUDGET:return "BYTE_BUDGET"
    if len({f["id"] for f in sel})!=len(sel):return "DUPLICATE_ID"
    if len({(f["scope"],f["age_ms"]) for f in sel})!=len(sel):return "DUPLICATE_TIMESTAMP"
    if any(f["scope"]!=req["scope"] for f in sel):return "CROSS_SCOPE"
    if any(f["age_ms"]<0 or not f["historical"] for f in sel):return "FUTURE_FRAME"
    return "OK"


def covered(sel,req):
    if validate_selection(sel,req)!="OK":return False
    ages=sorted(f["age_ms"] for f in sel)
    k=req["class"]
    if k=="RECENT_DENSE":
        return sum(a<=60 for a in ages)>=3
    if k=="LONG_BASELINE":
        return 0 in ages and any(a>=280 for a in ages)
    c=req["center_ms"]
    if k=="EVENT_CENTERED":
        lo=[a for a in ages if a<=c and c-a<=20]
        hi=[a for a in ages if a>=c and a-c<=20]
        return bool(lo and hi)
    if k=="REVERSAL_BRACKET":
        lo=[a for a in ages if a<c and c-a<=40]
        hi=[a for a in ages if a>c and a-c<=40]
        return bool(lo and hi)
    return False


def one(index:int):
    frames,req=history(index)
    fixed=select_fixed(frames,req); query=select_query(frames,req)
    vf=validate_selection(fixed,req); vq=validate_selection(query,req)
    return {
      "index":index,"class":req["class"],"scope":req["scope"],"center_ms":req["center_ms"],
      "fixed_ids":[f["id"] for f in fixed],"query_ids":[f["id"] for f in query],
      "fixed_valid":vf,"query_valid":vq,
      "fixed_covered":covered(fixed,req),"query_covered":covered(query,req),
      "future_selected":sum(f["age_ms"]<0 for f in fixed+query),
      "cross_scope_selected":sum(f["scope"]!=req["scope"] for f in fixed+query),
      "budget_violations":int(vf in ("FRAME_BUDGET","BYTE_BUDGET"))+int(vq in ("FRAME_BUDGET","BYTE_BUDGET")),
      "authority_grants":0,
    }
