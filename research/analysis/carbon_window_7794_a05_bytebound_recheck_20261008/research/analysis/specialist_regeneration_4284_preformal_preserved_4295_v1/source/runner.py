from __future__ import annotations
import argparse, json, pathlib

BASE_SUPPORT={"A":"TRUE","B":"FALSE","C":"UNKNOWN","D":"TRUE"}
V2_SUPPORT={"A":"FALSE","B":"FALSE","C":"UNKNOWN","D":"TRUE"}
NOVEL={"E":"UNKNOWN"}
SCHEDULES=[
    "STABLE_BASE","SUPPORT_VERSION_CHANGE","PRODUCER_GENERATION_CHANGE","NOVEL_INPUT",
    "REQUIRED_UNKNOWN","INCOMPLETE_SUPPORT","CORRUPT_REGENERATION","RECOVER_COMPLETE_NEW_VERSION"
]
POLICIES=["ALWAYS_GENERAL","VERSIONED_SHADOW_SWITCH","REGENERATE_AND_ATTEST"]

def graph(v): return {"TRUE":"ADVANCE","FALSE":"STOP","UNKNOWN":"YIELD"}[v]

def manifest(ver, complete=True, corrupt=False):
    m=dict(BASE_SUPPORT if ver==1 else V2_SUPPORT)
    if not complete: m.pop("D",None)
    if corrupt: m["A"]="FALSE" if m.get("A")!="FALSE" else "TRUE"
    return m

def truth(ver,key):
    return (BASE_SUPPORT if ver==1 else V2_SUPPORT).get(key,NOVEL.get(key,"UNKNOWN"))

def schedule_rows(name,rep, *, formal=False):
    rows=[]
    keys=["D","A","C","B","D","C","A","B"] if formal else ["A","B","C","D","A","B","C","D"]
    for idx,key in enumerate(keys):
        ver=1; gen=1; complete=True; corrupt=False
        if name=="SUPPORT_VERSION_CHANGE" and idx>=4: ver=2
        if name=="PRODUCER_GENERATION_CHANGE" and idx>=4: gen=2
        if name=="NOVEL_INPUT" and idx in (2,6): key="E"
        if name=="REQUIRED_UNKNOWN": key="C" if idx in (1,3,5,7) else key
        if name=="INCOMPLETE_SUPPORT": complete=False
        if name=="CORRUPT_REGENERATION": corrupt=True
        if name=="RECOVER_COMPLETE_NEW_VERSION":
            if idx<2: complete=False
            else: ver=2; gen=2; complete=True
        rows.append({"schedule":name,"rep":rep,"index":idx,"key":key,"support_version":ver,
                     "producer_generation":gen,"support_complete":complete,"regenerated_corrupt":corrupt})
    return rows

class Versioned:
    def __init__(self): self.identity=None; self.active=False; self.shadow=0
    def step(self,r):
        ident=(r["support_version"],r["producer_generation"],r["support_complete"],r["regenerated_corrupt"])
        if ident!=self.identity:
            self.identity=ident; self.active=False; self.shadow=0
        key=r["key"]; vtruth=truth(r["support_version"],key); m=manifest(r["support_version"],r["support_complete"],r["regenerated_corrupt"])
        known=key in m
        calls=0; specialist=False; reason=None; attest=False
        if not r["support_complete"] or not known:
            calls=1; value=vtruth; reason="GENERAL_INCOMPLETE_OR_NOVEL"
        elif self.active:
            value=m[key]; specialist=True
        else:
            calls=1; value=vtruth; shadow_value=m[key]
            if shadow_value==vtruth:
                self.shadow+=1
                if self.shadow>=4: self.active=True
            else:
                self.shadow=0; reason="SHADOW_MISMATCH"
        return value,calls,specialist,reason,attest

class Regen:
    def __init__(self): self.identity=None; self.active=False; self.artifact=None
    def step(self,r):
        ident=(r["support_version"],r["producer_generation"],r["support_complete"],r["regenerated_corrupt"])
        attest=False; reason=None
        if ident!=self.identity:
            self.identity=ident; self.active=False; self.artifact=None
            m=manifest(r["support_version"],r["support_complete"],r["regenerated_corrupt"])
            if r["support_complete"] and set(m)==set(BASE_SUPPORT):
                attest=all(m[k]==truth(r["support_version"],k) for k in sorted(BASE_SUPPORT))
                if attest:
                    self.active=True; self.artifact=m
                else: reason="ATTESTATION_FAILED"
            else: reason="SUPPORT_INCOMPLETE"
        key=r["key"]; vtruth=truth(r["support_version"],key)
        if self.active and key in self.artifact:
            return self.artifact[key],0,True,reason,attest
        return vtruth,1,False,(reason or "GENERAL_NOVEL_OR_UNATTESTED"),attest

def execute(mode):
    schedules=SCHEDULES if mode=="formal" else ["STABLE_BASE","SUPPORT_VERSION_CHANGE","NOVEL_INPUT","INCOMPLETE_SUPPORT","CORRUPT_REGENERATION"]
    reps=[10,11] if mode=="formal" else [99]
    out=[]
    for sch in schedules:
      for rep in reps:
        vs=Versioned(); rg=Regen()
        for r in schedule_rows(sch,rep,formal=(mode=="formal")):
            oracle=truth(r["support_version"],r["key"])
            policies={}
            policies["ALWAYS_GENERAL"]={"value":oracle,"graph":graph(oracle),"general_calls":1,"specialist_used":False,"reason":"BASELINE","attestation":False,"authority_granted":False}
            for name,obj in [("VERSIONED_SHADOW_SWITCH",vs),("REGENERATE_AND_ATTEST",rg)]:
                value,calls,specialist,reason,attest=obj.step(r)
                policies[name]={"value":value,"graph":graph(value),"general_calls":calls,"specialist_used":specialist,
                                "reason":reason,"attestation":attest,"authority_granted":False}
            out.append({**r,"oracle_value":oracle,"oracle_graph":graph(oracle),"policies":policies})
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("mode",choices=["construction","formal"]); ap.add_argument("out")
    a=ap.parse_args(); rows=execute(a.mode)
    pathlib.Path(a.out).parent.mkdir(parents=True,exist_ok=True)
    pathlib.Path(a.out).write_text(json.dumps({"mode":a.mode,"rows":rows},sort_keys=True,separators=(",",":"))+"\n")
    print(json.dumps({"mode":a.mode,"rows":len(rows)}))
if __name__=="__main__": main()
