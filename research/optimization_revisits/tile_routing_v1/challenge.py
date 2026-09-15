"""Post-result falsification, separately frozen as OPT-REVISIT-TILE-002.

Do not pool with the first benchmark. Same unchanged encoders; vary spatial
spread of exactly twenty one-byte changes in a deterministic textured frame.
"""
import argparse
import json
from pathlib import Path
import random

from benchmark import Frame, evaluate, save, verify_sources


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args(); args.out.mkdir(parents=True,exist_ok=False)
    verify_sources()
    base=Frame(640,480,'RGB',random.Random(990702).randbytes(640*480*3))
    results=[]
    for name,positions in (
        ('clustered20',[3*i for i in range(20)]),
        ('distributed20',[((i//10)*64*640+(i%10)*64)*3 for i in range(20)])):
        data=bytearray(base.pixels)
        for p in positions: data[p]^=1
        new=Frame(640,480,'RGB',bytes(data))
        for arm in ('O1','O2','coverage25'):
            row=evaluate(arm,name,[base,new],0,('O1','O2','coverage25').index(arm))
            row['changed_channel_bytes']=sum(a!=b for a,b in zip(base.pixels,new.pixels))
            results.append(row)
    checks={}
    for name in ('clustered20','distributed20'):
        byarm={r['arm']:r for r in results if r['workload']==name}
        ratio=byarm['coverage25']['warm_bytes']/byarm['O2']['warm_bytes']
        checks[name]=dict(candidate_warm_bytes=byarm['coverage25']['warm_bytes'],
                          O2_warm_bytes=byarm['O2']['warm_bytes'],ratio=ratio,
                          changed_bytes=byarm['coverage25']['changed_channel_bytes'],
                          gate_pass=ratio<=1.05)
    save(args.out/'result.json',dict(allocation='OPT-REVISIT-TILE-002',
        kind='posthoc-selected deterministic falsification; not a preregistered efficacy sample',
        rows=results,checks=checks,
        result_class='COUNTEREXAMPLE_FOUND' if not all(c['gate_pass'] for c in checks.values()) else 'COUNTEREXAMPLE_NOT_FOUND',
        timing_claim='none: one pass per arm, no warmup/order balance'))


if __name__=='__main__': main()
