"""Small two-group XOR presentation decoder with authority separation."""
GEN=7
SOURCE={"a":0x3c,"b":0x12,"c":0xa5,"d":0x5e}
CRITICAL={"a":False,"b":False,"c":True,"d":False}
PARITY={"p_ab":SOURCE["a"]^SOURCE["b"],"p_cd":SOURCE["c"]^SOURCE["d"]}
ALL={**SOURCE,**PARITY}
def shard(name,generation=GEN,critical=None):
    return {"id":name,"value":ALL[name],"generation":generation,"critical":CRITICAL.get(name,False) if critical is None else critical}
def make(names,order=None,generations=None,critical_override=None):
    generations=generations or {};critical_override=critical_override or {}
    arr=[shard(n,generations.get(n,GEN),critical_override.get(n)) for n in names]
    if order:
        by={x["id"]:x for x in arr};arr=[by[n] for n in order]
    for tick,item in enumerate(arr):item["arrival_tick"]=tick
    return {"generation":GEN,"source_manifest":CRITICAL.copy(),"arrival":arr}
CASES={
"complete":make(list(ALL)),
"reordered_complete":make(list(ALL),["p_cd","d","c","p_ab","b","a"]),
"single_noncritical_erasure":make(["b","c","d","p_ab","p_cd"]),
"single_critical_erasure":make(["a","b","d","p_ab","p_cd"]),
"cross_group_erasures":make(["b","d","p_ab","p_cd"]),
"same_group_double_erasure":make(["c","d","p_ab","p_cd"]),
"parity_erasure_sources_complete":make(list(SOURCE)),
"mixed_generation":make(list(ALL),generations={"c":GEN-1}),
"criticality_metadata_mismatch":make(list(ALL),critical_override={"c":False}),
}
def evaluate(case):
    arrivals=case["arrival"];ids=[x["id"] for x in arrivals]
    valid=(len(ids)==len(set(ids)) and all(x["generation"]==case["generation"] for x in arrivals) and all(x["critical"]==case["source_manifest"].get(x["id"],False) for x in arrivals if x["id"] in SOURCE))
    if not valid:return {"status":"REJECT_INVALID_PROVENANCE","presentation_complete":False,"reconstructed":[],"authority_eligible":False,"decoded":{}}
    known={x["id"]:x["value"] for x in arrivals};reconstructed=[]
    for left,right,parity in (("a","b","p_ab"),("c","d","p_cd")):
        missing=[n for n in (left,right) if n not in known]
        if len(missing)==1 and parity in known:
            lost=missing[0];present=right if lost==left else left
            known[lost]=known[present]^known[parity];reconstructed.append(lost)
    complete=all(n in known for n in SOURCE)
    exact_sources=all(n in ids for n in SOURCE)
    authority=valid and exact_sources and case["source_manifest"].get("c") and complete
    return {"status":"DECODED" if complete else "INCOMPLETE","presentation_complete":complete,"reconstructed":sorted(reconstructed),"authority_eligible":bool(authority),"decoded":{n:known[n] for n in sorted(SOURCE) if n in known}}
