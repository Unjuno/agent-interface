"""Independent pixel-difference audit of the A01 candidate output."""
import hashlib,json
from pathlib import Path
from PIL import Image
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
ROOT=REPO/"research/doom/results/map01-astra-attempt-v1"
HEALTH=[100,100,100,100,100,84,84,53,49,22,11,4,0]
BOXES={"health":[440,585,535,635],"face_control":[610,580,675,650]}
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def changed_pixels(before,after,box,threshold):
    a=before.crop(box).load(); b=after.crop(box).load(); left,top,right,bottom=box
    return sum(max(abs(x-y) for x,y in zip(a[i,j],b[i,j]))>threshold for j in range(bottom-top) for i in range(right-left))
def main():
    result=json.loads((HERE/"candidate.raw.json").read_text())
    manifest=json.loads((ROOT/"frame-manifest.json").read_text()); frames=[ROOT/x["file"] for x in manifest]
    assert len(frames)==13 and all(sha(p)==r["sha256"] for p,r in zip(frames,manifest))
    pinned={"report.json":sha(ROOT/"report.json"),"events.jsonl":sha(ROOT/"events.jsonl"),"frame-manifest.json":sha(ROOT/"frame-manifest.json"),"policy_invalidation_guard_v1.py":sha(REPO/"research/live_control/policy_invalidation_guard_v1.py")}
    assert result["input_sha256"]==pinned
    assert result["frame_count"]==13 and len(result["rows"])==18
    for row in result["rows"]:
        box=BOXES[row["roi"]]; expected=[]
        for i,interval in enumerate(row["intervals"]):
            with Image.open(frames[i]) as im: before=im.convert("RGB")
            with Image.open(frames[i+1]) as im: after=im.convert("RGB")
            n=changed_pixels(before,after,box,row["rgb_threshold"])
            assert n==interval["changed_pixels"]
            assert (n>=row["minimum_changed_pixels"]) == (interval["status"]=="INVALIDATED")
            label=(HEALTH[i]!=HEALTH[i+1]);
            assert label==interval["expected_health_change"]
            expected.append(label if row["roi"]=="health" else False)
        pred=[x["status"]=="INVALIDATED" for x in row["intervals"]]
        assert row["tp"]==sum(a and b for a,b in zip(pred,expected))
        assert row["fp"]==sum(a and not b for a,b in zip(pred,expected))
        assert row["fn"]==sum((not a) and b for a,b in zip(pred,expected))
    summary={"audit":"PASS_METHOD_SCOPED","independent_pixel_replay":True,"source_frames_hash_verified":True,"rows_reconciled":len(result["rows"]),"scope":result["scope"]}
    (HERE/"independent_audit.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
