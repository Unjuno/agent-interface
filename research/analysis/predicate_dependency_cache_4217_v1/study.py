from __future__ import annotations
import json, time
from dataclasses import dataclass
from pathlib import Path

PREDICATES = {
    "FORM_COMPLETE": ("form", "required_set"),
    "MODAL_BLOCKING": ("modal",),
    "RECOVERY_NEEDED": ("last_effect", "error"),
    "TARGET_MATCH": ("target",),
}

@dataclass(frozen=True)
class State:
    step: int
    name: str
    intent_version: int
    producer_version: int
    source_generation: int
    source_current: bool
    generations: dict
    values: dict

def evaluate(predicate: str, s: State) -> str:
    # Any unavailable declared dependency or stale source makes the semantic fact UNKNOWN.
    if not s.source_current:
        return "UNKNOWN"
    for key in PREDICATES[predicate]:
        if s.generations.get(key) is None or s.values.get(key) is None:
            return "UNKNOWN"
    if predicate == "FORM_COMPLETE":
        return "TRUE" if bool(s.values["form"]) and bool(s.values["required_set"]) else "FALSE"
    if predicate == "MODAL_BLOCKING":
        return "TRUE" if bool(s.values["modal"]) else "FALSE"
    if predicate == "RECOVERY_NEEDED":
        return "TRUE" if bool(s.values["last_effect"]) == False or bool(s.values["error"]) else "FALSE"
    if predicate == "TARGET_MATCH":
        return "TRUE" if bool(s.values["target"]) else "FALSE"
    raise KeyError(predicate)

def graph(vals: dict[str, str]) -> str:
    required=("MODAL_BLOCKING","TARGET_MATCH","FORM_COMPLETE","RECOVERY_NEEDED")
    if any(vals[p] == "UNKNOWN" for p in required): return "YIELD_UNKNOWN"
    if vals["MODAL_BLOCKING"] == "TRUE": return "YIELD_MODAL"
    if vals["TARGET_MATCH"] == "FALSE": return "YIELD_TARGET"
    if vals["FORM_COMPLETE"] == "FALSE": return "CONTINUE_FILL"
    if vals["RECOVERY_NEEDED"] == "TRUE": return "RECOVER"
    return "SUBMIT_READY"

def key(predicate: str, s: State):
    return {
      "predicate_id": predicate,
      "intent_version": s.intent_version,
      "producer_version": s.producer_version,
      "source_generation": s.source_generation,
      "source_current": s.source_current,
      "dependency_generations": {k:s.generations.get(k) for k in PREDICATES[predicate]},
    }

def trace() -> list[State]:
    G=dict(form=1,required_set=1,modal=1,last_effect=1,error=1,target=1,toolbar=1)
    V=dict(form=True,required_set=True,modal=False,last_effect=True,error=False,target=True,toolbar=0)
    rows=[]
    def add(name, *, iv=1,pv=1,sg=1,current=True,g=None,v=None):
        nonlocal G,V
        if g: G={**G,**g}
        if v: V={**V,**v}
        rows.append(State(len(rows),name,iv,pv,sg,current,dict(G),dict(V)))
    add("BASE")
    add("UNRELATED_TOOLBAR", g={"toolbar":2}, v={"toolbar":1})
    add("FORM_BECOMES_INCOMPLETE", g={"form":2}, v={"form":False})
    add("FORM_ABA_RESTORED_NEW_GEN", g={"form":3}, v={"form":True})
    add("INTENT_VERSION_CHANGE", iv=2)
    add("PRODUCER_VERSION_CHANGE", iv=2,pv=2)
    add("MODAL_DEPENDENCY_UNKNOWN", iv=2,pv=2,g={"modal":None},v={"modal":None})
    add("SOURCE_STALE", iv=2,pv=2,sg=1,current=False)
    add("SOURCE_FRESH_NEW_GENERATION", iv=2,pv=2,sg=2,current=True,g={"modal":2},v={"modal":False})
    add("LAST_EFFECT_CHANGED", iv=2,pv=2,sg=2,g={"last_effect":2},v={"last_effect":False})
    add("TARGET_CHANGED", iv=2,pv=2,sg=2,g={"target":2},v={"target":False})
    add("TARGET_ABA_RESTORED_NEW_GEN", iv=2,pv=2,sg=2,g={"target":3},v={"target":True})
    add("UNRELATED_TOOLBAR_AGAIN", iv=2,pv=2,sg=2,g={"toolbar":3},v={"toolbar":2})
    return rows

def run():
    states=trace(); cache={}; rows=[]; calls=0; hits=0; misses=0; reasons={}
    for s in states:
        full={p:evaluate(p,s) for p in PREDICATES}
        cached={}; events={}
        for p in PREDICATES:
            k=key(p,s); prior=cache.get(p)
            t0=time.perf_counter_ns()
            if prior is not None and prior["key"] == k and all(x is not None for x in k["dependency_generations"].values()) and s.source_current:
                val=prior["value"]; hit=True; reason="HIT"; hits+=1
            else:
                val=evaluate(p,s); calls+=1; hit=False; misses+=1
                if prior is None: reason="COLD"
                elif not s.source_current: reason="SOURCE_STALE"
                elif any(x is None for x in k["dependency_generations"].values()): reason="DEPENDENCY_UNKNOWN"
                elif prior["key"]["intent_version"] != k["intent_version"]: reason="INTENT_VERSION"
                elif prior["key"]["producer_version"] != k["producer_version"]: reason="PRODUCER_VERSION"
                elif prior["key"]["source_generation"] != k["source_generation"]: reason="SOURCE_GENERATION"
                else: reason="DEPENDENCY_GENERATION"
                cache[p]={"key":k,"value":val}
            t1=time.perf_counter_ns(); reasons[reason]=reasons.get(reason,0)+1
            cached[p]=val; events[p]={"hit":hit,"reason":reason,"lookup_ns":t1-t0,"cache_key":k}
        rows.append({"step":s.step,"name":s.name,"state":{"intent_version":s.intent_version,"producer_version":s.producer_version,"source_generation":s.source_generation,"source_current":s.source_current,"generations":s.generations,"values":s.values},"full":full,"cached":cached,"full_graph":graph(full),"cached_graph":graph(cached),"events":events,"authority_granted":False})
    return {"allocation":"predicate-cache-4217-20260923-01","formal_invocations":1,"reruns":0,"replacements":0,"tuning":0,"predicate_count":len(PREDICATES),"state_count":len(states),"full_recompute_calls":len(states)*len(PREDICATES),"cache_evaluator_calls":calls,"cache_hits":hits,"cache_misses":misses,"reasons":reasons,"rows":rows}

if __name__ == "__main__":
    import sys
    if len(sys.argv)!=2: raise SystemExit("usage: study.py OUTPUT")
    out=Path(sys.argv[1]); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(run(),sort_keys=True,indent=2)+"\n")
