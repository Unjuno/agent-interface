from pathlib import Path
import argparse, hashlib, json, math, itertools
import numpy as np
from PIL import Image

def sha(b): return hashlib.sha256(b).hexdigest()
def ref_shift(a,b,lim):
    h,w=a.shape; candidates=[]
    for dy in range(-lim,lim+1):
        for dx in range(-lim,lim+1):
            ylo=max(0,dy); yhi=min(h,h+dy); xlo=max(0,dx); xhi=min(w,w+dx)
            p=a[ylo:yhi,xlo:xhi]; q=b[ylo-dy:yhi-dy,xlo-dx:xhi-dx]
            p=p-p.mean(); q=q-q.mean()
            den=math.sqrt(float(np.sum(p*p))*float(np.sum(q*q)))
            corr=float(np.sum(p*q)/den) if den else -1.0
            candidates.append((corr,-abs(dx)-abs(dy),-dy,-dx,dy,dx))
    z=max(candidates)
    return {"correlation":z[0],"dy_small":z[4],"dx_small":z[5]}
def auc(scores,labels):
    p=[v for v,y in zip(scores,labels) if y]; n=[v for v,y in zip(scores,labels) if not y]
    return sum(1.0 if x>y else .5 if x==y else 0.0 for x in p for y in n)/(len(p)*len(n))
def exact_p(scores,labels):
    npos=sum(labels); observed=auc(scores,labels); total=extreme=0
    for inds in itertools.combinations(range(len(scores)),npos):
        chosen=set(inds); value=auc(scores,[i in chosen for i in range(len(scores))]); total+=1
        if abs(value-.5)>=abs(observed-.5)-1e-12: extreme+=1
    return extreme/total,total
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--repo-root",required=True);ap.add_argument("--package",required=True);a=ap.parse_args()
    root=Path(a.repo_root); pkg=Path(a.package); result=json.loads((pkg/"RESULT.json").read_text()); freeze=json.loads((pkg/"FREEZE.json").read_text())
    assert result["freeze"]["main"]==freeze["current_main"]
    assert result["freeze"]["manifest_sha256"]==freeze["source_hashes"]["manifest_sha256"]
    run=root/"research/doom/results"/freeze["episode"]
    mb=(run/"retention-manifest.json").read_bytes(); eb=(run/"runtime/events.jsonl").read_bytes()
    assert sha(mb)==freeze["source_hashes"]["manifest_sha256"]
    assert sha(eb)==freeze["source_hashes"]["events_sha256"]
    manifest=json.loads(mb); hashes={r["path"]:r["sha256"] for r in manifest["files"]}
    events=[json.loads(s) for s in eb.splitlines() if s.strip()]
    params=result["freeze"]; seqs=params["sequences"]
    typed={r["sequence"]:r for r in events if r.get("event")=="typed_observation" and r.get("sequence") in seqs}
    plain={r["sequence"]:r for r in events if r.get("event")=="observation" and r.get("sequence") in seqs}
    assert len(typed)==len(plain)==len(seqs)==53
    x0,y0,x1,y1=params["world_crop_xyxy"]; f=params["downsample_factor"]; lim=params["translation_search_downsample_px"]
    frames={}
    for n in seqs:
        rel=f"runtime/{n:03d}.png"; raw=(run/rel).read_bytes()
        assert sha(raw)==hashes[rel]
        assert plain[n]["image"].replace("\\","/").endswith("/"+rel)
        image=np.asarray(Image.open(run/rel).convert("RGB"))
        frame_hash=sha(image.tobytes())
        assert frame_hash==typed[n]["frame_rgb_sha256"]
        frames[n]=(image,typed[n],sha(raw))
    assert len(result["rows"])==52
    errors=[]; rows=[]
    for i,(n,m) in enumerate(zip(seqs[:-1],seqs[1:])):
        a,ta,ha=frames[n]; b,tb,hb=frames[m]
        row=result["rows"][i]
        assert (row["from"],row["to"],row["from_png_sha256"],row["to_png_sha256"])==(n,m,ha,hb)
        health_delta=ta["signals"]["health"]["value"]-tb["signals"]["health"]["value"]
        assert row["health_loss_points"]==health_delta
        assert row["health_loss"]==(health_delta>0)
        assert abs(row["capture_interval_ms"]-(tb["capture_ns"]-ta["capture_ns"])/1e6)<1e-8
        assert abs(row["full_rgb_mae"]-float(np.abs(a.astype(np.int16)-b.astype(np.int16)).mean()))<1e-9
        aw=a[y0:y1,x0:x1]; bw=b[y0:y1,x0:x1]
        assert abs(row["world_rgb_mae_unregistered"]-float(np.abs(aw.astype(np.int16)-bw.astype(np.int16)).mean()))<1e-9
        ag=(aw[:,:,0]*.299+aw[:,:,1]*.587+aw[:,:,2]*.114).astype(np.float32)
        bg=(bw[:,:,0]*.299+bw[:,:,1]*.587+bw[:,:,2]*.114).astype(np.float32)
        def ds(g): return g[:g.shape[0]//f*f,:g.shape[1]//f*f].reshape(g.shape[0]//f,f,g.shape[1]//f,f).mean((1,3))
        shift=ref_shift(ds(ag),ds(bg),lim)
        assert shift["dx_small"]==row["dx_small"] and shift["dy_small"]==row["dy_small"]
        assert abs(shift["correlation"]-row["correlation"])<1e-6
        dy=shift["dy_small"]*f; dx=shift["dx_small"]*f
        h,w=aw.shape[:2]; y0a=max(0,dy); y1a=min(h,h+dy); x0a=max(0,dx); x1a=min(w,w+dx)
        ar=aw[y0a:y1a,x0a:x1a]; br=bw[y0a-dy:y1a-dy,x0a-dx:x1a-dx]
        residual=float(np.abs(ar.astype(np.int16)-br.astype(np.int16)).mean())
        assert abs(row["world_rgb_mae_translation_compensated"]-residual)<1e-9
        rows.append(row)
    labels=[r["health_loss"] for r in rows]
    raw=[r["world_rgb_mae_unregistered"] for r in rows]
    comp=[r["world_rgb_mae_translation_compensated"] for r in rows]
    ar=auc(raw,labels); ac=auc(comp,labels); neg=[v for v,y in zip(comp,labels) if not y]; pos=[v for v,y in zip(comp,labels) if y]
    above=sum(v>float(np.median(neg)) for v in pos)
    passed=ac>=.75 and ac-ar>=.10 and above>=3
    p_raw,nperm=exact_p(raw,labels); p_comp,nperm2=exact_p(comp,labels)
    assert nperm==nperm2==result["metrics"]["permutations"]
    assert abs(result["metrics"]["exact_permutation_p_world_raw"]-p_raw)<1e-12
    assert abs(result["metrics"]["exact_permutation_p_compensated"]-p_comp)<1e-12
    assert abs(result["metrics"]["world_raw_auc"]-ar)<1e-12
    assert abs(result["metrics"]["world_translation_compensated_auc"]-ac)<1e-12
    assert abs(result["metrics"]["auc_gain"]-(ac-ar))<1e-12
    assert result["metrics"]["health_loss_pairs_above_no_loss_median"]==above
    assert result["criterion_met"]==passed and result["status"]==("PASS_SCOPED" if passed else "FAIL_SCOPED")
    audit={"schema":"issue59-camera-compensated-motion-a01-audit-v1","status":"PASS_EVIDENCE_AND_RECOMPUTATION_SCOPED","source_main":freeze["current_main"],"source_hashes":freeze["source_hashes"],"pairs_recomputed":len(rows),"health_loss_pairs":sum(labels),"metrics_recomputed":{"world_raw_auc":ar,"world_translation_compensated_auc":ac,"auc_gain":ac-ar,"health_loss_pairs_above_no_loss_median":above},"checks":["manifest and event-log SHA-256","all 53 PNG hashes versus frozen manifest","typed RGB hashes and sequence-to-image joins","all 52 adjacent-pair health labels and capture intervals","raw full-screen and world-crop RGB MAE","independent exhaustive registration shift search","translation-compensated residual MAE","AUC, exact permutation p-values, and frozen FAIL/PASS criterion"],"scope":"Independent arithmetic/provenance audit of one posthoc episode; no semantic labels or causal claims"}
    (pkg/"AUDIT.json").write_text(json.dumps(audit,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(audit,indent=2))
if __name__=="__main__":main()
