"""Execution-envelope wrapper for allocation-02; scientific cases/candidate unchanged."""
import argparse, hashlib, json, sys
from pathlib import Path
import run
ROOT=Path(__file__).resolve().parent
SLICES=((0,9),(9,18),(18,26),(26,34))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify():
    f=json.loads((ROOT/'FREEZE02.json').read_text())
    for n,h in f['files'].items():
        if sha(ROOT/n)!=h: raise SystemExit(f'FREEZE02_HASH:{n}')
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--batch',type=int,choices=range(4),required=True);ap.add_argument('--out');ap.add_argument('--list',action='store_true');a=ap.parse_args()
    verify(); allcases=run.cases(False); lo,hi=SLICES[a.batch]; selected=allcases[lo:hi]
    if a.list:
        print(json.dumps({'batch':a.batch,'lo':lo,'hi':hi,'cases':[c['name'] for c in selected]},sort_keys=True));return 0
    if not a.out: raise SystemExit('--out required')
    orig=run.cases
    run.cases=lambda construction=False: orig(True) if construction else selected
    old=sys.argv[:];sys.argv=['run.py','--out',a.out]
    try: rc=run.main()
    finally: sys.argv=old;run.cases=orig
    p=Path(a.out)
    if p.exists():
        (p/'BATCH_WRAPPER.json').write_text(json.dumps({'allocation':'wallclock-source-time-reversal-2442-20260922-02-batches','batch':a.batch,'slice':[lo,hi],'case_names':[c['name'] for c in selected],'run_returncode':rc,'freeze02_sha256':sha(ROOT/'FREEZE02.json')},indent=2,sort_keys=True)+'\n')
    return rc
if __name__=='__main__':raise SystemExit(main())
