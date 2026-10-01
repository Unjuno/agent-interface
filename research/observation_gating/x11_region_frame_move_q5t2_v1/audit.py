from __future__ import annotations
import argparse, copy, hashlib, json
from pathlib import Path

POLICIES=("PINNED_SCREEN","REFRESH_SCREEN","WINDOW_CLIENT")
SCHEDULES=("STABLE","MOVE_BEFORE","MOVE_BETWEEN")
EXPECTED={
 ("PINNED_SCREEN","STABLE"):True,
 ("REFRESH_SCREEN","STABLE"):True,
 ("WINDOW_CLIENT","STABLE"):True,
 ("PINNED_SCREEN","MOVE_BEFORE"):False,
 ("REFRESH_SCREEN","MOVE_BEFORE"):True,
 ("WINDOW_CLIENT","MOVE_BEFORE"):True,
 ("PINNED_SCREEN","MOVE_BETWEEN"):False,
 ("REFRESH_SCREEN","MOVE_BETWEEN"):False,
 ("WINDOW_CLIENT","MOVE_BETWEEN"):True,
}

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def validate_row(row,case_dir,expected_rep=None):
    e=[]; checks=0
    def ck(cond,msg):
        nonlocal checks; checks+=1
        if not cond:e.append(msg)
    ck(row.get("schema")=="x11-region-frame-move-case-v1","schema")
    p=row.get("policy"); s=row.get("schedule")
    ck(p in POLICIES,"policy"); ck(s in SCHEDULES,"schedule")
    if expected_rep is not None: ck(row.get("rep")==expected_rep,"rep")
    ck(row.get("complete") is True,"complete")
    ck(type(row.get("authority")) is bool and row.get("authority") is False,"authority")
    ck(row.get("task_success") is None,"task_success")
    ck(type(row.get("target_xid_initial")) is int and row.get("target_xid_initial")==row.get("target_xid_final"),"xid_lifetime")
    ck(row.get("initial_geometry",{}).get("w")==120 and row.get("initial_geometry",{}).get("h")==80,"initial_size")
    ck(row.get("final_geometry",{}).get("w")==120 and row.get("final_geometry",{}).get("h")==80,"final_size")
    files=row.get("files",{})
    for name in ("initial_window.bin","candidate.bin","scorer_window.bin","scorer_root.bin"):
        path=case_dir/name; meta=files.get(name,{})
        ck(path.is_file(),f"file:{name}")
        if path.is_file():
            ck(path.stat().st_size==meta.get("bytes"),f"bytes:{name}")
            ck(sha(path)==meta.get("sha256"),f"sha:{name}")
    ih=files.get("initial_window.bin",{}).get("sha256"); ch=files.get("candidate.bin",{}).get("sha256"); wh=files.get("scorer_window.bin",{}).get("sha256"); rh=files.get("scorer_root.bin",{}).get("sha256")
    ck(ih==wh,"target_pixels_unchanged")
    ck(wh==rh,"scorer_window_root")
    expected=EXPECTED.get((p,s))
    ck(type(row.get("candidate_matches_current_window")) is bool,"match_type")
    if expected is not None: ck(row.get("candidate_matches_current_window") is expected,"expected_match")
    ck((ch==wh)==row.get("candidate_matches_current_window"),"match_hash_consistency")
    if p=="WINDOW_CLIENT": ck(row.get("candidate_source")=="window" and row.get("candidate_screen_geometry") is None,"window_source")
    else: ck(row.get("candidate_source")=="root" and isinstance(row.get("candidate_screen_geometry"),dict),"root_source")
    if expected is False:
        ck(p!="WINDOW_CLIENT","negative_is_screen")
        cg=row.get("candidate_screen_geometry"); fg=row.get("final_geometry")
        ck(isinstance(cg,dict),"negative_screen_geometry")
        ck(isinstance(fg,dict),"negative_final_geometry")
        if isinstance(cg,dict) and isinstance(fg,dict):
            ck((cg.get("x"),cg.get("y"))!=(fg.get("x"),fg.get("y")),"stale_coords")
        else:
            ck(False,"stale_coords")
        ck(row.get("stale_coordinate_witness") is True,"stale_witness")
    else:
        ck(row.get("stale_coordinate_witness") is False,"no_stale_witness")
    # Reconstruct schedule from retained event order, not only from the label.
    kinds=[e0.get("kind") for e0 in row.get("events",[]) if isinstance(e0,dict)]
    acquisition_kind={"PINNED_SCREEN":"use_pinned_geometry","REFRESH_SCREEN":"refresh_geometry","WINDOW_CLIENT":"window_client_prepare"}.get(p)
    ck(acquisition_kind in kinds,"acquisition_event")
    move_before=[i for i,k in enumerate(kinds) if k=="move_before"]
    move_between=[i for i,k in enumerate(kinds) if k=="move_between"]
    if s=="STABLE":
        ck(not move_before and not move_between,"stable_no_move")
    elif s=="MOVE_BEFORE":
        ck(len(move_before)==1 and not move_between,"move_before_count")
        if acquisition_kind in kinds and move_before:
            ck(move_before[0] < kinds.index(acquisition_kind),"move_before_order")
        else: ck(False,"move_before_order")
    elif s=="MOVE_BETWEEN":
        ck(len(move_between)==1 and not move_before,"move_between_count")
        if acquisition_kind in kinds and move_between:
            ck(kinds.index(acquisition_kind) < move_between[0],"move_between_order")
        else: ck(False,"move_between_order")
    proc=row.get("process",{})
    ck(proc.get("app_exit")==0,"app_exit")
    ck(proc.get("xvfb_exit") in (-15,0),"xvfb_exit")
    ck(proc.get("socket_absent_after_cleanup") is True,"socket_cleanup")
    return checks,e

def audit(root:Path,expected_reps):
    errors=[]; checks=0; rows=[]
    for rep in expected_reps:
        batch=root/f"batch-{rep}"; endp=batch/"END.json"
        if not endp.is_file(): errors.append(f"missing_end:{rep}"); continue
        end=json.loads(endp.read_text()); checks+=1
        if end.get("complete") is not True or end.get("case_count")!=9: errors.append(f"bad_end:{rep}")
        cases=sorted(batch.glob("case-*/CASE.json"))
        checks+=1
        if len(cases)!=9: errors.append(f"case_count:{rep}:{len(cases)}")
        for cp in cases:
            row=json.loads(cp.read_text()); rows.append((row,cp.parent)); c,e=validate_row(row,cp.parent,rep); checks+=c; errors.extend(f"{cp.parent.name}:{x}" for x in e)
    # exact unique matrix
    cells=[(r[0].get("rep"),r[0].get("policy"),r[0].get("schedule")) for r in rows]
    checks+=1
    if len(cells)!=len(set(cells)): errors.append("duplicate_cell")
    summary={p:{"cases":0,"matches":0,"mismatches":0} for p in POLICIES}
    for row,_ in rows:
        if row.get("policy") in summary:
            x=summary[row["policy"]]; x["cases"]+=1
            if row.get("candidate_matches_current_window"):x["matches"]+=1
            else:x["mismatches"]+=1
    return {"schema":"x11-region-frame-move-audit-v1","checks":checks,"errors":errors,"case_count":len(rows),"summary":summary,"pass":not errors}

def controls(root:Path,expected_reps):
    # Load one known positive and one known negative; mutate only in-memory record while leaving raw bytes fixed.
    cases=[]
    for rep in expected_reps:
        for cp in sorted((root/f"batch-{rep}").glob("case-*/CASE.json")): cases.append((json.loads(cp.read_text()),cp.parent))
    pos=next(x for x in cases if x[0]["policy"]=="WINDOW_CLIENT" and x[0]["schedule"]=="MOVE_BETWEEN")
    neg=next(x for x in cases if x[0]["policy"]=="REFRESH_SCREEN" and x[0]["schedule"]=="MOVE_BETWEEN")
    muts=[]
    def add(name,base,fn):
        r=copy.deepcopy(base[0]); fn(r); c,e=validate_row(r,base[1],base[0]["rep"]); muts.append({"name":name,"rejected":bool(e),"errors":e,"checks":c})
    add("flip_match",pos,lambda r:r.__setitem__("candidate_matches_current_window",False))
    add("authority_true",pos,lambda r:r.__setitem__("authority",True))
    add("task_success_true",pos,lambda r:r.__setitem__("task_success",True))
    add("xid_change",pos,lambda r:r.__setitem__("target_xid_final",r["target_xid_final"]+1))
    add("candidate_sha",pos,lambda r:r["files"]["candidate.bin"].__setitem__("sha256","0"*64))
    add("scorer_sha",pos,lambda r:r["files"]["scorer_root.bin"].__setitem__("sha256","1"*64))
    add("app_exit",pos,lambda r:r["process"].__setitem__("app_exit",7))
    add("socket_cleanup",pos,lambda r:r["process"].__setitem__("socket_absent_after_cleanup",False))
    add("negative_stale_false",neg,lambda r:r.__setitem__("stale_coordinate_witness",False))
    add("negative_final_coords",neg,lambda r:r["final_geometry"].update({"x":r["candidate_screen_geometry"]["x"],"y":r["candidate_screen_geometry"]["y"]}))
    add("policy_relabel",pos,lambda r:r.__setitem__("policy","PINNED_SCREEN"))
    add("schedule_relabel",pos,lambda r:r.__setitem__("schedule","STABLE"))
    return {"schema":"x11-region-frame-move-controls-v1","count":len(muts),"rejected":sum(1 for m in muts if m["rejected"]),"controls":muts,"pass":all(m["rejected"] for m in muts)}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("root"); ap.add_argument("--reps",default="0,1,2"); ap.add_argument("--controls",action="store_true"); ap.add_argument("--out")
    a=ap.parse_args(); reps=tuple(int(x) for x in a.reps.split(",") if x!="")
    result=audit(Path(a.root),reps)
    if a.controls: result["corruption_controls"]=controls(Path(a.root),reps)
    text=json.dumps(result,indent=2,sort_keys=True)+"\n"
    if a.out: Path(a.out).write_text(text)
    print(text,end="")
    raise SystemExit(0 if result["pass"] and (not a.controls or result["corruption_controls"]["pass"]) else 1)
if __name__=="__main__":main()
