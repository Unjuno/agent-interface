#!/usr/bin/env python3
import argparse, hashlib, json, statistics
from pathlib import Path

ROI_PIXELS=1024; ROI_BYTES=4096; TARGET_BGR=bytes((50,50,220)); CORPUS_N=512
SEED=b"quiet-watch-predicate-cost-v1|20260916"
BOUNDARIES=(0,1,2,255,256,510,511,512,513,514,768,1022,1023,1024)
EXPECTED_GIT_BLOBS={
  'native_predicate.c':'e05bbd069cc087ca4ce023b42a45e3e652cc72c2',
  'experiment.py':'7ed2a46d9c6acff2cacf261ce16f721046ea88dc',
  'audit.py':'9d1972fd5ccdc459e60827b1d7664aee682a6808',
  'prereg.json':'39b79d6a873c991e8d241ab18b3ae6f4601e61e9',
  'correctness_preflight.json':'2b0bf9cd70edaeff209d6a87c27cff049b675d5b',
}

def sha256(b): return hashlib.sha256(b).hexdigest()
def git_blob_sha(b): return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def stream_bytes(i,n):
    out=bytearray(); ctr=0; prefix=SEED+i.to_bytes(4,'little')
    while len(out)<n:
        out.extend(hashlib.sha256(prefix+ctr.to_bytes(4,'little')).digest()); ctr+=1
    return bytes(out[:n])
def desired_count(i):
    if i<len(BOUNDARIES): return BOUNDARIES[i]
    h=hashlib.sha256(SEED+b'count'+i.to_bytes(4,'little')).digest()
    return int.from_bytes(h[:2],'little')%(ROI_PIXELS+1)
def make_frame(i):
    raw=bytearray(stream_bytes(i,ROI_BYTES))
    for j in range(0,ROI_BYTES,4):
        if raw[j:j+3]==TARGET_BGR: raw[j]^=1
    count=desired_count(i)
    d=hashlib.sha256(SEED+b'perm'+i.to_bytes(4,'little')).digest(); m=(int.from_bytes(d[:2],'little')|1)%ROI_PIXELS
    if m==0: m=1
    off=int.from_bytes(d[2:4],'little')%ROI_PIXELS
    for j in range(count):
        pix=(off+j*m)%ROI_PIXELS; base=4*pix; raw[base:base+3]=TARGET_BGR
    return bytes(raw),count
def reference_count(raw): return sum(raw[i:i+3]==TARGET_BGR for i in range(0,ROI_BYTES,4))
def close(a,b,tol=1e-12): return abs(a-b)<=tol*max(1.0,abs(a),abs(b))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('result'); ap.add_argument('--root',default='.'); ap.add_argument('--out',required=True); args=ap.parse_args()
    root=Path(args.root); r=json.loads(Path(args.result).read_text()); checks=[]
    prereg=json.loads((root/'prereg.json').read_text())
    checks.append(['schema',r.get('schema')=='quiet_watch_predicate_cost_v1_result'])
    checks.append(['task',r.get('task')==prereg['task']])
    for f,want in EXPECTED_GIT_BLOBS.items(): checks.append([f'blob:{f}',git_blob_sha((root/f).read_bytes())==want])
    frames=[]; expected=[]
    for i in range(CORPUS_N): b,c=make_frame(i); frames.append(b); expected.append(c)
    ref=[reference_count(b) for b in frames]
    checks += [
      ['corpus_hash',r.get('corpus_sha256')==sha256(b''.join(frames))],
      ['reference_expected',ref==expected],
      ['python_counts',r.get('python_counts')==ref],
      ['native_counts',r.get('native_counts')==ref],
    ]
    blocks=r.get('blocks',[]); checks.append(['pair_count',len(blocks)==16])
    wr=[]; cr=[]; pwall=[]; nwall=[]; pcpu=[]; ncpu=[]; block_ok=True
    checksum=sum(ref)*16
    if len(blocks)==16:
      for i,b in enumerate(blocks):
        if b.get('pair')!=i or b.get('order_first')!=('python' if i%2==0 else 'native'): block_ok=False
        for arm in ('python','native'):
          a=b.get('arms',{}).get(arm,{})
          if a.get('n')!=8192 or a.get('checksum')!=checksum: block_ok=False; continue
          wpe=a['wall_ns']/a['n']; cpe=a['thread_cpu_ns']/a['n']
          if not close(a['wall_ns_per_eval'],wpe) or not close(a['thread_cpu_ns_per_eval'],cpe): block_ok=False
        if block_ok:
          p=b['arms']['python']; n=b['arms']['native']
          pw=p['wall_ns']/p['n']; nw=n['wall_ns']/n['n']; pc=p['thread_cpu_ns']/p['n']; nc=n['thread_cpu_ns']/n['n']
          wr.append(nw/pw); cr.append(nc/pc); pwall.append(pw); nwall.append(nw); pcpu.append(pc); ncpu.append(nc)
    checks.append(['raw_derived_block_integrity',block_ok and len(wr)==16])
    if len(wr)==16:
      medw=statistics.median(wr); medc=statistics.median(cr)
      s=r['summary']
      checks += [
        ['wall_ratio_summary',close(medw,s['median_paired_wall_ratio'])],
        ['cpu_ratio_summary',close(medc,s['median_paired_thread_cpu_ratio'])],
        ['python_wall_summary',close(statistics.median(pwall),s['python_wall_ns_per_eval_median'])],
        ['native_wall_summary',close(statistics.median(nwall),s['native_wall_ns_per_eval_median'])],
        ['python_cpu_summary',close(statistics.median(pcpu),s['python_thread_cpu_ns_per_eval_median'])],
        ['native_cpu_summary',close(statistics.median(ncpu),s['native_thread_cpu_ns_per_eval_median'])],
        ['wall_ratio_vector',all(close(a,b) for a,b in zip(wr,s['wall_ratios'])) and len(s['wall_ratios'])==16],
        ['cpu_ratio_vector',all(close(a,b) for a,b in zip(cr,s['thread_cpu_ratios'])) and len(s['thread_cpu_ratios'])==16],
      ]
      decision='PASS_COST_SCOPED' if medw<=1/3 and medc<=1/3 else 'HOLD_COST'
      checks.append(['decision',s['decision']==decision])
    else:
      medw=medc=None; decision='INVALID'; checks.append(['decision',False])
    checks.append(['selected_cpu_recorded',r.get('environment',{}).get('selected_cpu') is not None])
    out={'schema':'quiet_watch_predicate_cost_v1_strict_posthoc_audit','checks':checks,'pass':all(v for _,v in checks),'decision':decision,'median_paired_wall_ratio':medw,'median_paired_thread_cpu_ratio':medc,'formal_result_sha256':sha256(Path(args.result).read_bytes())}
    Path(args.out).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,indent=2,sort_keys=True))
    if not out['pass']: raise SystemExit(2)
if __name__=='__main__': main()
