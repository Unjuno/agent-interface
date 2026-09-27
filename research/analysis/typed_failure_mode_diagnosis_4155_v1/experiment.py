from __future__ import annotations
import argparse, hashlib, itertools, json
from pathlib import Path

FOCUS=("CURRENT","LOST","UNKNOWN")
TARGET=("CURRENT","STALE","UNKNOWN")
MODAL=("ABSENT","PRESENT","UNKNOWN")
APP=("IDLE","PENDING","UNKNOWN")
VARIATIONS=range(4)
RECOVERIES=("RETRY_BOUNDED","REBIND","WAIT_OBSERVE","YIELD")
MODE_TO_RECOVERY={
    "FOCUS_LOST":"REBIND",
    "TARGET_STALE":"YIELD",
    "MODAL_BLOCKED":"RETRY_BOUNDED",
    "APP_BUSY_OR_PENDING":"WAIT_OBSERVE",
    "UNKNOWN":"YIELD",
}

def sha256_file(p: Path) -> str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20), b''):
            h.update(b)
    return h.hexdigest()

def diagnose_mode(r):
    f,t,m,a=r["focus"],r["target"],r["modal"],r["app"]
    if (f,t,m,a)==("LOST","CURRENT","ABSENT","IDLE"):
        return "FOCUS_LOST"
    if (f,t,m,a)==("CURRENT","STALE","ABSENT","IDLE"):
        return "TARGET_STALE"
    if (f,t,m,a)==("CURRENT","CURRENT","PRESENT","IDLE"):
        return "MODAL_BLOCKED"
    if (f,t,m,a)==("CURRENT","CURRENT","ABSENT","PENDING"):
        return "APP_BUSY_OR_PENDING"
    return "UNKNOWN"

def mode_then_recovery(r):
    mode=diagnose_mode(r)
    return mode, MODE_TO_RECOVERY[mode]

def direct_recovery(r):
    # Deliberately independent structure: no call to diagnose_mode or MODE_TO_RECOVERY.
    f,t,m,a=r["focus"],r["target"],r["modal"],r["app"]
    if f=="LOST" and t=="CURRENT" and m=="ABSENT" and a=="IDLE":
        return "REBIND"
    if f=="CURRENT" and t=="CURRENT" and m=="PRESENT" and a=="IDLE":
        return "RETRY_BOUNDED"
    if f=="CURRENT" and t=="CURRENT" and m=="ABSENT" and a=="PENDING":
        return "WAIT_OBSERVE"
    return "YIELD"

def oracle(r):
    # Independent abnormal-set oracle. UNKNOWN evidence is never resolved locally.
    if "UNKNOWN" in (r["focus"],r["target"],r["modal"],r["app"]):
        return "UNKNOWN", "YIELD", False
    abnormal=[]
    if r["focus"]=="LOST": abnormal.append("FOCUS_LOST")
    if r["target"]=="STALE": abnormal.append("TARGET_STALE")
    if r["modal"]=="PRESENT": abnormal.append("MODAL_BLOCKED")
    if r["app"]=="PENDING": abnormal.append("APP_BUSY_OR_PENDING")
    if len(abnormal)!=1:
        return "UNKNOWN", "YIELD", False
    mode=abnormal[0]
    expected={
        "FOCUS_LOST":"REBIND",
        "TARGET_STALE":"YIELD",
        "MODAL_BLOCKED":"RETRY_BOUNDED",
        "APP_BUSY_OR_PENDING":"WAIT_OBSERVE",
    }[mode]
    return mode, expected, True

def rows():
    idx=0
    for f,t,m,a,v in itertools.product(FOCUS,TARGET,MODAL,APP,VARIATIONS):
        base={"row_id":f"r{idx:03d}","symptom":"EXPECTED_EFFECT_MISSING","focus":f,"target":t,"modal":m,"app":a,"variation":v}
        om,od,ident=oracle(base)
        mm,md=mode_then_recovery(base)
        dd=direct_recovery(base)
        ambiguous=not ident
        row={**base,"oracle_mode":om,"oracle_disposition":od,"identifiable_single_fault":ident,
             "direct_disposition":dd,"mode_label":mm,"mode_disposition":md,
             "direct_wrong":dd!=od,"mode_wrong":md!=od,
             "direct_unnecessary_yield":dd=="YIELD" and od!="YIELD",
             "mode_unnecessary_yield":md=="YIELD" and od!="YIELD",
             "direct_unsafe":ambiguous and dd!="YIELD",
             "mode_unsafe":ambiguous and md!="YIELD",
             "semantic_authority":False,"input_authority":False}
        yield row
        idx+=1

def summarize(rs):
    def n(k): return sum(bool(r[k]) for r in rs)
    return {
        "rows":len(rs),
        "identifiable_single_fault_rows":sum(r["identifiable_single_fault"] for r in rs),
        "direct_wrong":n("direct_wrong"),"mode_wrong":n("mode_wrong"),
        "direct_unnecessary_yield":n("direct_unnecessary_yield"),"mode_unnecessary_yield":n("mode_unnecessary_yield"),
        "direct_unsafe":n("direct_unsafe"),"mode_unsafe":n("mode_unsafe"),
        "direct_mode_final_mismatch":sum(r["direct_disposition"]!=r["mode_disposition"] for r in rs),
        "authority_escape":sum(r["semantic_authority"] or r["input_authority"] for r in rs),
    }

def decide(s):
    if s["rows"]!=324 or s["identifiable_single_fault_rows"]==0 or s["authority_escape"]!=0:
        return "FAIL_INTEGRITY"
    direct_bad=s["direct_wrong"]+s["direct_unnecessary_yield"]+s["direct_unsafe"]
    mode_bad=s["mode_wrong"]+s["mode_unnecessary_yield"]+s["mode_unsafe"]
    if mode_bad < direct_bad and s["mode_unsafe"]<=s["direct_unsafe"]:
        return "PASS_TYPED_MODE_DIAGNOSIS_SCOPED"
    if mode_bad==direct_bad==0 and s["direct_mode_final_mismatch"]==0:
        return "FAIL_DIAGNOSIS_LAYER_UNNECESSARY"
    if mode_bad>direct_bad or s["mode_unsafe"]>s["direct_unsafe"]:
        return "FAIL_DIAGNOSIS_MISROUTES_RECOVERY"
    return "HOLD_OBSERVATIONS_NOT_IDENTIFIABLE"

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--source-dir',type=Path,required=True)
    a=ap.parse_args(); a.out.parent.mkdir(parents=True,exist_ok=True)
    rs=list(rows()); s=summarize(rs); decision=decide(s)
    src={p.name:sha256_file(p) for p in sorted(a.source_dir.iterdir()) if p.is_file() and p.name in {"PLAN.md","experiment.py","audit.py","controls.py","test_contract.py","ENVIRONMENT.json","SCHEDULE.json"}}
    out={"schema":"typed-failure-mode-diagnosis-4155-v1","allocation":"typed-failure-mode-diagnosis-4155-20260923-01",
         "formal_invocations":1,"reruns":0,"replacements":0,"tuning_after_freeze":0,
         "decision":decision,"summary":s,"rows":rs,"source_sha256":src}
    a.out.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding='utf-8')
    print(json.dumps({"decision":decision,"summary":s},sort_keys=True))

if __name__=='__main__': main()
