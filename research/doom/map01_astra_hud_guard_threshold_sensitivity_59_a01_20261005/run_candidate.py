"""A01 exploratory threshold sensitivity over retained MAP01 decision frames."""
import hashlib, json, sys
from pathlib import Path
from PIL import Image
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "research/live_control"))
from policy_invalidation_guard_v1 import PolicyInvalidationGuard
ROOT = REPO / "research/doom/results/map01-astra-attempt-v1"
HEALTH = [100,100,100,100,100,84,84,53,49,22,11,4,0]
BOXES = {"health": [440,585,535,635], "face_control": [610,580,675,650]}

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
    report = json.loads((ROOT/"report.json").read_text())
    manifest = json.loads((ROOT/"frame-manifest.json").read_text())
    frames = [ROOT/row["file"] for row in manifest]
    assert len(frames) == len(report["decisions"]) == len(HEALTH) == 13
    assert all(sha(p) == row["sha256"] for p,row in zip(frames,manifest))
    rows=[]
    for roi, box in BOXES.items():
        for threshold in (16,32,64):
            for minimum in (25,100,250):
                intervals=[]
                for i in range(12):
                    with Image.open(frames[i]) as im: before=im.convert("RGB")
                    with Image.open(frames[i+1]) as im: after=im.convert("RGB")
                    spec={"op":"policy_invalidation_guard","guard_id":f"{roi}-{threshold}-{minimum}-{i}","source_sequence":1,"box":box,"metric":"rgb_change","rgb_threshold":threshold,"minimum_changed_pixels":minimum,"max_source_age_ms":30000,"on_change":"needs_decision","on_unknown":"needs_decision"}
                    guard=PolicyInvalidationGuard(spec,before,1,"retained-map01",1_000_000_000)
                    outcome=guard.evaluate(after,2,"retained-map01",2_000_000_000)
                    intervals.append({"index":i,"status":outcome["status"],"changed_pixels":outcome["changed_pixels"],"expected_health_change": HEALTH[i] != HEALTH[i+1]})
                expected = [x["expected_health_change"] for x in intervals] if roi=="health" else [False]*12
                predicted = [x["status"]=="INVALIDATED" for x in intervals]
                rows.append({"roi":roi,"rgb_threshold":threshold,"minimum_changed_pixels":minimum,"tp":sum(a and b for a,b in zip(predicted,expected)),"fp":sum(a and not b for a,b in zip(predicted,expected)),"fn":sum((not a) and b for a,b in zip(predicted,expected)),"intervals":intervals})
    result={"schema":"map01-astra-hud-guard-threshold-sensitivity-a01","source_commit":"406431f5790ca2e8a8888bcfe1e82730432d8b49","input_sha256":{"report.json":sha(ROOT/"report.json"),"events.jsonl":sha(ROOT/"events.jsonl"),"frame-manifest.json":sha(ROOT/"frame-manifest.json"),"policy_invalidation_guard_v1.py":sha(REPO/"research/live_control/policy_invalidation_guard_v1.py")},"frame_count":len(frames),"interval_count":12,"health_transcription":HEALTH,"rows":rows,"scope":"posthoc exploratory sensitivity on one retained failed run; manual HUD labels; no live integration or causal task-effect claim"}
    (HERE/"candidate.raw.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"output":"candidate.raw.json","rows":len(rows),"health_rows_at_16_or_32":sum(r["roi"]=="health" and r["rgb_threshold"] in (16,32) and r["tp"]==7 and r["fp"]==0 and r["fn"]==0 for r in rows),"face_control_fp_range":[min(r["fp"] for r in rows if r["roi"]=="face_control"),max(r["fp"] for r in rows if r["roi"]=="face_control")]},indent=2))
if __name__=="__main__": main()
