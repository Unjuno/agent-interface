from __future__ import annotations
import argparse, hashlib, itertools, json
from pathlib import Path

FOCUS=("CURRENT","LOST","UNKNOWN"); TARGET=("CURRENT","STALE","UNKNOWN"); MODAL=("ABSENT","PRESENT","UNKNOWN"); APP=("IDLE","PENDING","UNKNOWN"); VARIATIONS=range(4)
SOURCE_NAMES={"PLAN.md","experiment.py","audit.py","controls.py","test_contract.py","ENVIRONMENT.json","SCHEDULE.json"}

def sha256_file(p):
    h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()

def expected(row):
    vals=(row.get("focus"),row.get("target"),row.get("modal"),row.get("app"))
    if any(v=="UNKNOWN" for v in vals): return "UNKNOWN","YIELD",False
    tags=[]
    if vals[0]=="LOST": tags.append("FOCUS_LOST")
    if vals[1]=="STALE": tags.append("TARGET_STALE")
    if vals[2]=="PRESENT": tags.append("MODAL_BLOCKED")
    if vals[3]=="PENDING": tags.append("APP_BUSY_OR_PENDING")
    if len(tags)!=1: return "UNKNOWN","YIELD",False
    mode=tags[0]
    return mode,{"FOCUS_LOST":"REBIND","TARGET_STALE":"YIELD","MODAL_BLOCKED":"RETRY_BOUNDED","APP_BUSY_OR_PENDING":"WAIT_OBSERVE"}[mode],True

def audit(result_path, source_dir):
    data=json.loads(result_path.read_text()); errors=[]
    if data.get("schema")!="typed-failure-mode-diagnosis-4155-v1": errors.append("schema")
    if data.get("formal_invocations")!=1 or data.get("reruns")!=0 or data.get("replacements")!=0 or data.get("tuning_after_freeze")!=0: errors.append("invocation_counts")
    rows=data.get("rows")
    if not isinstance(rows,list) or len(rows)!=324: return {"pass":False,"errors":errors+["row_count"]}
    expected_keys=set(itertools.product(FOCUS,TARGET,MODAL,APP,VARIATIONS)); seen=set(); metrics={k:0 for k in ["identifiable_single_fault_rows","direct_wrong","mode_wrong","direct_unnecessary_yield","mode_unnecessary_yield","direct_unsafe","mode_unsafe","direct_mode_final_mismatch","authority_escape"]}
    for r in rows:
        key=(r.get("focus"),r.get("target"),r.get("modal"),r.get("app"),r.get("variation"))
        if key in seen: errors.append("duplicate_row")
        seen.add(key)
        om,od,ident=expected(r)
        if r.get("oracle_mode")!=om or r.get("oracle_disposition")!=od or r.get("identifiable_single_fault") is not ident: errors.append("oracle_row")
        if r.get("mode_label")!=om: errors.append("mode_label")
        dd=r.get("direct_disposition"); md=r.get("mode_disposition")
        if dd!=od: metrics["direct_wrong"]+=1
        if md!=od: metrics["mode_wrong"]+=1
        if dd=="YIELD" and od!="YIELD": metrics["direct_unnecessary_yield"]+=1
        if md=="YIELD" and od!="YIELD": metrics["mode_unnecessary_yield"]+=1
        if not ident and dd!="YIELD": metrics["direct_unsafe"]+=1
        if not ident and md!="YIELD": metrics["mode_unsafe"]+=1
        if dd!=md: metrics["direct_mode_final_mismatch"]+=1
        if ident: metrics["identifiable_single_fault_rows"]+=1
        if r.get("semantic_authority") is not False or r.get("input_authority") is not False: metrics["authority_escape"]+=1
    if seen!=expected_keys: errors.append("corpus_coverage")
    summary={"rows":324,**metrics}
    if data.get("summary")!=summary: errors.append("summary")
    direct_bad=summary["direct_wrong"]+summary["direct_unnecessary_yield"]+summary["direct_unsafe"]
    mode_bad=summary["mode_wrong"]+summary["mode_unnecessary_yield"]+summary["mode_unsafe"]
    expected_decision=("FAIL_DIAGNOSIS_LAYER_UNNECESSARY" if mode_bad==direct_bad==0 and summary["direct_mode_final_mismatch"]==0 else
                       "PASS_TYPED_MODE_DIAGNOSIS_SCOPED" if mode_bad<direct_bad and summary["mode_unsafe"]<=summary["direct_unsafe"] else
                       "FAIL_DIAGNOSIS_MISROUTES_RECOVERY" if mode_bad>direct_bad or summary["mode_unsafe"]>summary["direct_unsafe"] else "HOLD_OBSERVATIONS_NOT_IDENTIFIABLE")
    if data.get("decision")!=expected_decision: errors.append("decision")
    src={p.name:sha256_file(p) for p in source_dir.iterdir() if p.is_file() and p.name in SOURCE_NAMES}
    if data.get("source_sha256")!=dict(sorted(src.items())): errors.append("source_sha256")
    return {"pass":not errors,"errors":errors,"rows":324,"decision":data.get("decision"),"summary":summary}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--result',type=Path,required=True); ap.add_argument('--source-dir',type=Path,required=True); ap.add_argument('--out',type=Path)
    a=ap.parse_args(); out=audit(a.result,a.source_dir)
    if a.out: a.out.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if out["pass"] else 1)
if __name__=='__main__': main()
