"""Independent raw-only auditor for visual-effects construction case 2447006."""
from pathlib import Path
import argparse, hashlib, json
import cv2
import numpy as np
from PIL import Image

ROI = (20, 300, 20, 620)
MIN_TRACKS = 80


def pixel_hash(path):
    return hashlib.sha256(np.asarray(Image.open(path).convert("RGB")).tobytes()).hexdigest()


def visual_flow(before, after):
    a = np.asarray(Image.open(before).convert("L"), np.uint8)[ROI[0]:ROI[1], ROI[2]:ROI[3]]
    b = np.asarray(Image.open(after).convert("L"), np.uint8)[ROI[0]:ROI[1], ROI[2]:ROI[3]]
    pts = cv2.goodFeaturesToTrack(a, maxCorners=700, qualityLevel=.01, minDistance=6, blockSize=7)
    if pts is None:
        return {"valid_tracks": 0, "median_dx_px": None, "median_dy_px": None, "status": "UNKNOWN"}
    nxt, st, _ = cv2.calcOpticalFlowPyrLK(a,b,pts,None,winSize=(31,31),maxLevel=4,
        criteria=(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,30,.01))
    if nxt is None or st is None:
        return {"valid_tracks": 0, "median_dx_px": None, "median_dy_px": None, "status": "UNKNOWN"}
    ok=st[:,0]==1; d=nxt[ok,0,:]-pts[ok,0,:]
    if len(d): d=d[np.hypot(d[:,0],d[:,1])<100]
    n=int(len(d))
    if n<MIN_TRACKS:return {"valid_tracks":n,"median_dx_px":None,"median_dy_px":None,"status":"UNKNOWN"}
    return {"valid_tracks":n,"median_dx_px":float(np.median(d[:,0])),
            "median_dy_px":float(np.median(d[:,1])),"status":"MEASURED"}


def audit(root):
    root=Path(root); score=json.loads((root/"score.json").read_text()); errors=[]; pairs=[]
    if score.get("seed")!=2447006 or score.get("class")!="drop" or score.get("gate")!="temporal_gate":errors.append("case_identity")
    if score.get("error") is not None:errors.append("runner_error")
    for name,key,release_ns,effect_ns in (
        ("next_subgoal","Right","next_subgoal_release_done_ns","next_subgoal_after_action_ns"),
        ("third_subgoal","Left","third_subgoal_release_done_ns","third_subgoal_after_action_ns")):
        d=root/name; receipt=json.loads((d/"result.json").read_text()); before=d/"before-action.png"; after=d/"after-action.png"
        row={"name":name,"expected_key":key,"recorded_key":receipt.get("key"),
             "before_image_sha_matches_handoff":before.exists() and pixel_hash(before)==receipt.get("observation_sha256"),
             "after_image_exists":after.exists(),"visual_flow":None,"ordered_after_release":False,
             "release_verified_empty":bool(receipt.get("release",{}).get("verified") and not receipt.get("release",{}).get("keys_down") and not receipt.get("release",{}).get("buttons_down"))}
        row["ordered_after_release"]=bool(receipt.get("release_done_ns",0)<score.get(effect_ns,0))
        if before.exists() and after.exists():row["visual_flow"]=visual_flow(before,after)
        if row["recorded_key"]!=key:errors.append(name+":wrong_key")
        if not row["before_image_sha_matches_handoff"]:errors.append(name+":before_hash")
        if not row["after_image_exists"]:errors.append(name+":after_missing")
        if not row["ordered_after_release"]:errors.append(name+":effect_order")
        if not row["release_verified_empty"]:errors.append(name+":release")
        if row["visual_flow"] and row["visual_flow"]["status"]!="MEASURED":errors.append(name+":flow_unknown")
        pairs.append(row)
    result={"schema":"issue2447-visual-effects-audit-v1","case":"issue2447-visual-effects-construction-2447006",
            "decision":"PASS_CONSTRUCTION_INSTRUMENTATION" if not errors else "HOLD_CONSTRUCTION_INSTRUMENTATION",
            "errors":errors,"pairs":pairs,"formal_rows":0,"retries":0,
            "scope":"Instrumentation evidence only; visual flow does not by itself establish task-semantic correctness or Issue #2447 acceptance."}
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument("--evidence",required=True);p.add_argument("--out",required=True);a=p.parse_args()
    r=audit(a.evidence);Path(a.out).write_text(json.dumps(r,indent=2,sort_keys=True)+"\n");print(json.dumps(r,sort_keys=True))

if __name__=="__main__":main()
