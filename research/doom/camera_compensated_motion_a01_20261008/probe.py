from pathlib import Path
import argparse, hashlib, itertools, json
import numpy as np
from PIL import Image

FREEZE = {
    "main": "1aaa633c4f1aeec25e4b4617d92dd93af3b20603",
    "manifest_sha256": "8dfbac52c298d865b4484aaa51dc0d821bb0d74f8c5995d3117206a1ed0dbda2",
    "events_sha256": "2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381",
    "episode": "map01-v39-coast-liveness-live-01",
    "sequences": [166, *range(167, 219)],
    "world_crop_xyxy": [321, 180, 961, 584],
    "downsample_factor": 4,
    "translation_search_downsample_px": 8,
    "decision": "PASS only if compensated AUC >= 0.75, improves raw AUC by >= 0.10, and at least 3/4 health-loss pairs exceed the no-loss median; otherwise FAIL_SCOPED",
}
def sha(b): return hashlib.sha256(b).hexdigest()
def auc(scores, labels):
    pos=[s for s,y in zip(scores,labels) if y]
    neg=[s for s,y in zip(scores,labels) if not y]
    return sum((p>n)+0.5*(p==n) for p in pos for n in neg)/(len(pos)*len(neg))
def exact_two_sided(scores, labels):
    # Exact label-permutation tail probability for the positive-class mean rank statistic.
    npos=sum(labels); observed=auc(scores,labels); total=0; extreme=0
    for idx in itertools.combinations(range(len(scores)),npos):
        mask=set(idx); ys=[i in mask for i in range(len(scores))]
        v=auc(scores,ys); total+=1
        if abs(v-0.5)>=abs(observed-0.5)-1e-12: extreme+=1
    return extreme/total, total
def downsample(gray, factor):
    h=(gray.shape[0]//factor)*factor; w=(gray.shape[1]//factor)*factor
    return gray[:h,:w].reshape(h//factor,factor,w//factor,factor).mean((1,3))
def best_shift(a,b,limit):
    h,w=a.shape[:2]; best=None
    for dy in range(-limit,limit+1):
      for dx in range(-limit,limit+1):
        ay0=max(0,dy); ay1=min(h,h+dy); ax0=max(0,dx); ax1=min(w,w+dx)
        aa=a[ay0:ay1,ax0:ax1]
        bb=b[ay0-dy:ay1-dy,ax0-dx:ax1-dx]
        ac=aa-aa.mean(); bc=bb-bb.mean()
        den=float(np.sqrt((ac*ac).sum()*(bc*bc).sum()))
        corr=float((ac*bc).sum()/den) if den else -1.0
        item=(corr,-(abs(dx)+abs(dy)),-dy,-dx,dy,dx)
        if best is None or item>best: best=item
    return {"correlation":best[0],"dy_small":best[4],"dx_small":best[5]}
def overlap_pair(a,b,dy,dx):
    h,w=a.shape[:2]
    ay0=max(0,dy); ay1=min(h,h+dy); ax0=max(0,dx); ax1=min(w,w+dx)
    return a[ay0:ay1,ax0:ax1], b[ay0-dy:ay1-dy,ax0-dx:ax1-dx]
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--repo-root",required=True); ap.add_argument("--out",required=True)
    args=ap.parse_args(); root=Path(args.repo_root); out=Path(args.out); out.mkdir(parents=True,exist_ok=False)
    run=root/"research/doom/results"/FREEZE["episode"]
    mb=(run/"retention-manifest.json").read_bytes(); eb=(run/"runtime/events.jsonl").read_bytes()
    assert sha(mb)==FREEZE["manifest_sha256"]; assert sha(eb)==FREEZE["events_sha256"]
    manifest=json.loads(mb); file_hash={r["path"]:r["sha256"] for r in manifest["files"]}
    events=[json.loads(x) for x in eb.splitlines() if x.strip()]
    typed={r["sequence"]:r for r in events if r.get("event")=="typed_observation" and r.get("sequence") in FREEZE["sequences"]}
    plain={r["sequence"]:r for r in events if r.get("event")=="observation" and r.get("sequence") in FREEZE["sequences"]}
    assert len(typed)==len(plain)==53
    x0,y0,x1,y1=FREEZE["world_crop_xyxy"]; f=FREEZE["downsample_factor"]; limit=FREEZE["translation_search_downsample_px"]
    frames={}
    for seq in FREEZE["sequences"]:
        rel=f"runtime/{seq:03d}.png"; p=run/rel; raw=p.read_bytes(); digest=sha(raw)
        assert digest==file_hash[rel]
        assert plain[seq]["image"].replace("\\","/").endswith("/"+rel)
        obs_hash=typed[seq].get("frame_rgb_sha256")
        rgb=np.asarray(Image.open(p).convert("RGB"))
        if obs_hash: assert sha(rgb.tobytes())==obs_hash
        frames[seq]={"rgb":rgb,"png_sha256":digest,"health":typed[seq]["signals"]["health"]["value"],"ammo":typed[seq]["signals"]["ammo"]["value"],"capture_ns":typed[seq]["capture_ns"],"frame_rgb_sha256":obs_hash}
    rows=[]
    for aseq,bseq in zip(FREEZE["sequences"][:-1],FREEZE["sequences"][1:]):
        a,b=frames[aseq],frames[bseq]
        full_raw=float(np.abs(a["rgb"].astype(np.int16)-b["rgb"].astype(np.int16)).mean())
        aw=a["rgb"][y0:y1,x0:x1]; bw=b["rgb"][y0:y1,x0:x1]
        world_raw=float(np.abs(aw.astype(np.int16)-bw.astype(np.int16)).mean())
        ag=(aw[:,:,0]*.299+aw[:,:,1]*.587+aw[:,:,2]*.114).astype(np.float32)
        bg=(bw[:,:,0]*.299+bw[:,:,1]*.587+bw[:,:,2]*.114).astype(np.float32)
        align=best_shift(downsample(ag,f),downsample(bg,f),limit)
        dy=align["dy_small"]*f; dx=align["dx_small"]*f
        ar,br=overlap_pair(aw, bw, dy, dx)
        comp=float(np.abs(ar.astype(np.int16)-br.astype(np.int16)).mean())
        dh=a["health"]-b["health"]
        rows.append({"from":aseq,"to":bseq,"health_from":a["health"],"health_to":b["health"],"health_loss":dh>0,"health_loss_points":dh,"capture_interval_ms":(b["capture_ns"]-a["capture_ns"])/1e6,"from_png_sha256":a["png_sha256"],"to_png_sha256":b["png_sha256"],"full_rgb_mae":full_raw,"world_rgb_mae_unregistered":world_raw,"world_rgb_mae_translation_compensated":comp,**align})
    labels=[r["health_loss"] for r in rows]
    raw=[r["world_rgb_mae_unregistered"] for r in rows]; comp=[r["world_rgb_mae_translation_compensated"] for r in rows]; full=[r["full_rgb_mae"] for r in rows]
    auc_raw=auc(raw,labels); auc_comp=auc(comp,labels); auc_full=auc(full,labels)
    neg=[v for v,y in zip(comp,labels) if not y]; pos=[v for v,y in zip(comp,labels) if y]; medneg=float(np.median(neg)); positives_above=sum(v>medneg for v in pos)
    p_raw,nperm=exact_two_sided(raw,labels); p_comp,_=exact_two_sided(comp,labels)
    criterion=auc_comp>=.75 and auc_comp-auc_raw>=.10 and positives_above>=3
    result={"schema":"issue59-camera-compensated-motion-a01-v1","status":"PASS_SCOPED" if criterion else "FAIL_SCOPED","freeze":FREEZE,"n_pairs":len(rows),"n_health_loss_pairs":sum(labels),"metrics":{"full_screen_raw_auc":auc_full,"world_raw_auc":auc_raw,"world_translation_compensated_auc":auc_comp,"auc_gain":auc_comp-auc_raw,"no_loss_compensated_median":medneg,"health_loss_pairs_above_no_loss_median":positives_above,"exact_permutation_p_world_raw":p_raw,"exact_permutation_p_compensated":p_comp,"permutations":nperm,"world_raw_median":float(np.median(raw)),"world_compensated_median":float(np.median(comp))},"criterion_met":criterion,"rows":rows,"scope":"single retained episode, posthoc health-loss labels; no semantic threat labels, no live detector or task-effect claim"}
    (out/"RESULT.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k!="rows"},indent=2))
if __name__=="__main__": main()
