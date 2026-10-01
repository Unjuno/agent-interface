"""Consume one NEW fixed arithmetic allocation. Never launches GUI/input."""
from __future__ import annotations
import argparse,json,hashlib,sys,time,os
from pathlib import Path
from clock_bounds import outcome
from corpus import records,COUNT

def main():
    ap=argparse.ArgumentParser();ap.add_argument('out');args=ap.parse_args()
    root=Path(__file__).resolve().parent.parent
    freeze=json.loads((root/'FREEZE.json').read_text())
    for name,h in freeze['files'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=h:
            raise SystemExit('source mismatch: '+name)
    out=Path(args.out);out.mkdir(parents=True,exist_ok=False)
    (out/'CONSUMED').write_text(freeze['allocation']+'\n')
    started=time.monotonic_ns();count=0
    with (out/'raw.jsonl').open('x') as f:
        for row in records():
            row['output']=outcome(row['input'])
            f.write(json.dumps(row,sort_keys=True,separators=(',',':'))+'\n')
            count+=1
    result={'allocation':freeze['allocation'],'rows':count,'expected':COUNT,
        'pid':os.getpid(),'argv':sys.argv,'started_ns':started,
        'ended_ns':time.monotonic_ns(),'scope':'synthetic_exact_arithmetic',
        'gui_model_input_calls':0}
    (out/'runner.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True));return int(count!=COUNT)
if __name__=='__main__':raise SystemExit(main())
