from __future__ import annotations
import argparse, hashlib, json, random, statistics, time
from pathlib import Path

PREDICATES=("TARGET_CORRECT","FORM_COMPLETE","MODAL_BLOCKING","RECOVERY_NEEDED","INTENT_SUBMIT","ENVELOPE_VALID")
FEATURES={
 "TARGET_CORRECT":("target_pos","target_neg"),
 "FORM_COMPLETE":("form_pos","form_neg"),
 "MODAL_BLOCKING":("modal_pos","modal_neg"),
 "RECOVERY_NEEDED":("recovery_pos","recovery_neg"),
 "INTENT_SUBMIT":("intent_pos","intent_neg"),
 "ENVELOPE_VALID":("envelope_pos","envelope_neg"),
}

def classify_pair(pos:int,neg:int)->str:
    score=int(pos)-int(neg)
    return "TRUE" if score>0 else ("FALSE" if score<0 else "UNKNOWN")

def general_backend(f):
    return {p:classify_pair(f[a],f[b]) for p,(a,b) in FEATURES.items()}

def graph(pred):
    if any(pred[p]=="UNKNOWN" for p in PREDICATES): return "YIELD_UNKNOWN"
    if pred["ENVELOPE_VALID"]=="FALSE": return "YIELD_OUT_OF_ENVELOPE"
    if pred["MODAL_BLOCKING"]=="TRUE": return "YIELD_MODAL"
    if pred["TARGET_CORRECT"]=="FALSE": return "YIELD_TARGET"
    if pred["FORM_COMPLETE"]=="FALSE": return "CONTINUE_FILL"
    if pred["RECOVERY_NEEDED"]=="TRUE": return "RECOVER"
    if pred["TARGET_CORRECT"]!="TRUE": return "YIELD_TARGET"
    if pred["INTENT_SUBMIT"]!="TRUE": return "YIELD_INTENT"
    return "SUBMIT_READY"

def support_rows():
    pairs=[(1,0),(0,1),(0,0),(1,1)]
    rows=[]
    for pi,pair in enumerate(pairs):
        for j in range(8):
            f={"target_pos":pair[0],"target_neg":pair[1]}
            # frozen nuisance schedule; never an input to specialist
            for k,name in enumerate(("form","modal","recovery","intent","envelope")):
                bit=(j>>((k+pi)%3))&1
                f[name+"_pos"]=bit
                f[name+"_neg"]=1-bit if (j+k)%4 else bit
            f["toolbar_flash"]=(j*3+pi)%5
            rows.append({"features":f,"label":classify_pair(*pair)})
    return rows

def train(rows):
    counts={}
    for r in rows:
        f=r["features"]; key=f"{f['target_pos']},{f['target_neg']}"
        counts.setdefault(key,{"TRUE":0,"FALSE":0,"UNKNOWN":0})[r["label"]]+=1
    table={}
    for key,c in sorted(counts.items()):
        m=max(c.values()); winners=[k for k,v in c.items() if v==m]
        table[key]=winners[0] if len(winners)==1 else "UNKNOWN"
    return table

def specialist(table,f):
    return table.get(f"{f['target_pos']},{f['target_neg']}","UNKNOWN")

def eval_rows():
    rng=random.Random(4218)
    pairs=[(1,0),(0,1),(0,0),(1,1)]
    rows=[]
    for i in range(256):
        pair=pairs[i%4]
        f={"target_pos":pair[0],"target_neg":pair[1]}
        for name in ("form","modal","recovery","intent","envelope"):
            f[name+"_pos"]=rng.randrange(2); f[name+"_neg"]=rng.randrange(2)
        f["toolbar_flash"]=rng.randrange(9)
        rows.append(f)
    return rows

def bench(fn,rows):
    # 9 batches, 2000 warmups + 20000 measured calls per batch
    vals=[]
    idx=0
    for _ in range(9):
        for __ in range(2000): fn(rows[idx%len(rows)]); idx+=1
        t0=time.perf_counter_ns()
        for __ in range(20000): fn(rows[idx%len(rows)]); idx+=1
        vals.append((time.perf_counter_ns()-t0)/20000.0)
    return vals

def main(out):
    out=Path(out); out.mkdir(parents=True,exist_ok=False)
    support=support_rows(); table=train(support); rows=eval_rows()
    artifact=json.dumps({"schema":"tiny-target-specialist-v1","table":table},sort_keys=True,separators=(",",":"))
    correct=unknown=unknown_ok=false_exec=graph_eq=0
    records=[]
    for i,f in enumerate(rows):
        gp=general_backend(f); truth=gp["TARGET_CORRECT"]; got=specialist(table,f)
        if got==truth: correct+=1
        if truth=="UNKNOWN":
            unknown+=1
            if got=="UNKNOWN": unknown_ok+=1
            if got in {"TRUE","FALSE"}: false_exec+=1
        sp=dict(gp); sp["TARGET_CORRECT"]=got
        geq=graph(sp)==graph(gp); graph_eq+=int(geq)
        records.append({"i":i,"features":f,"truth":truth,"specialist":got,"graph_general":graph(gp),"graph_specialist":graph(sp)})
    general_times=bench(general_backend,rows)
    spec_times=bench(lambda f:specialist(table,f),rows)
    gmed=statistics.median(general_times); smed=statistics.median(spec_times)
    result={
      "allocation":"tiny-predicate-specialist-4218-20260923-01",
      "support_rows":len(support),"eval_rows":len(rows),"target_correct":correct,
      "unknown_rows":unknown,"unknown_correct":unknown_ok,"false_executable_on_unknown":false_exec,
      "graph_equal":graph_eq,"artifact":artifact,"artifact_bytes":len(artifact.encode()),
      "general_batch_ns":general_times,"specialist_ns":spec_times,
      "general_median_ns":gmed,"specialist_median_ns":smed,"timing_ratio":smed/gmed,
      "formal_invocations":1,"reruns":0,"replacements":0,"tuning":0,
      "records":records,"support":support,
    }
    Path(out/"RAW.json").write_text(json.dumps(result,sort_keys=True,separators=(",",":"))+"\n")
    summary={k:v for k,v in result.items() if k not in {"records","support"}}
    gates=(correct==256 and unknown_ok==unknown and false_exec==0 and graph_eq==256 and len(artifact.encode())<=1024)
    if not gates: decision="FAIL_PREDICATE_SPECIALIST_FIDELITY"
    elif smed/gmed<=0.50: decision="PASS_TINY_PREDICATE_SPECIALIST_SCOPED"
    else: decision="HOLD_GENERAL_BACKEND_ALREADY_CHEAP"
    summary["decision_pre_audit"]=decision
    Path(out/"RESULT.json").write_text(json.dumps(summary,sort_keys=True,indent=2)+"\n")
    return 0
if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("out");a=ap.parse_args();raise SystemExit(main(a.out))
