#!/usr/bin/env python3
import argparse, hashlib, json, statistics
from pathlib import Path

ROI_PIXELS=1024; ROI_BYTES=4096; TARGET_BGR=bytes((50,50,220)); THRESHOLD=512
SEED=b"quiet-watch-predicate-cost-v1|20260916"; CORPUS_N=512
BOUNDARIES=(0,1,2,255,256,510,511,512,513,514,768,1022,1023,1024)

def sha256(b): return hashlib.sha256(b).hexdigest()
def stream_bytes(i,n):
    out=bytearray(); ctr=0; prefix=SEED+i.to_bytes(4,"little")
    while len(out)<n:
        out.extend(hashlib.sha256(prefix+ctr.to_bytes(4,"little")).digest()); ctr+=1
    return bytes(out[:n])
def desired_count(i):
    if i<len(BOUNDARIES): return BOUNDARIES[i]
    h=hashlib.sha256(SEED+b"count"+i.to_bytes(4,"little")).digest()
    return int.from_bytes(h[:2],"little")%(ROI_PIXELS+1)
def make_frame(i):
    raw=bytearray(stream_bytes(i,ROI_BYTES))
    for j in range(0,ROI_BYTES,4):
        if raw[j:j+3]==TARGET_BGR: raw[j]^=1
    count=desired_count(i)
    d=hashlib.sha256(SEED+b"perm"+i.to_bytes(4,"little")).digest(); m=(int.from_bytes(d[:2],"little")|1)%ROI_PIXELS
    if m==0: m=1
    off=int.from_bytes(d[2:4],"little")%ROI_PIXELS
    for j in range(count):
        pix=(off+j*m)%ROI_PIXELS; base=4*pix; raw[base:base+3]=TARGET_BGR
    return bytes(raw),count
def reference_count(raw):
    if len(raw)!=ROI_BYTES: raise ValueError
    return sum(raw[i:i+3]==TARGET_BGR for i in range(0,ROI_BYTES,4))
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("result"); ap.add_argument("--out",required=True); args=ap.parse_args()
    r=json.loads(Path(args.result).read_text())
    frames=[]; expected=[]
    for i in range(CORPUS_N):
        b,c=make_frame(i); frames.append(b); expected.append(c)
    ref=[reference_count(b) for b in frames]
    checks=[]
    checks.append(["schema",r.get("schema")=="quiet_watch_predicate_cost_v1_result"])
    checks.append(["corpus_hash",r.get("corpus_sha256")==sha256(b"".join(frames))])
    checks.append(["reference_expected",ref==expected])
    checks.append(["python_counts",r.get("python_counts")==ref])
    checks.append(["native_counts",r.get("native_counts")==ref])
    blocks=r.get("blocks",[]); checks.append(["pair_count",len(blocks)==16])
    checksum=sum(ref)*16
    checks.append(["checksums",all(b["arms"]["python"]["checksum"]==checksum and b["arms"]["native"]["checksum"]==checksum for b in blocks)])
    wr=[]; cr=[]
    for b in blocks:
        p=b["arms"]["python"]; n=b["arms"]["native"]
        wr.append(n["wall_ns_per_eval"]/p["wall_ns_per_eval"])
        cr.append(n["thread_cpu_ns_per_eval"]/p["thread_cpu_ns_per_eval"])
    medw=statistics.median(wr) if wr else None; medc=statistics.median(cr) if cr else None
    checks.append(["wall_ratio_recomputed",abs(medw-r["summary"]["median_paired_wall_ratio"])<1e-15])
    checks.append(["cpu_ratio_recomputed",abs(medc-r["summary"]["median_paired_thread_cpu_ratio"])<1e-15])
    decision="PASS_COST_SCOPED" if medw<=1/3 and medc<=1/3 else "HOLD_COST"
    checks.append(["decision_recomputed",decision==r["summary"]["decision"]])
    out={"schema":"quiet_watch_predicate_cost_v1_audit","checks":checks,"pass":all(v for _,v in checks),"decision":decision,"median_paired_wall_ratio":medw,"median_paired_thread_cpu_ratio":medc,"corpus_sha256":sha256(b"".join(frames))}
    Path(args.out).write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,indent=2,sort_keys=True))
    if not out["pass"]: raise SystemExit(2)
if __name__=="__main__": main()
