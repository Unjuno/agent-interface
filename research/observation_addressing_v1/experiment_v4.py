"""Allocation04 repairs fixture script redeclaration; resolver and input unchanged."""
import argparse, hashlib, json, shutil
from pathlib import Path
import experiment_v2
import fixture_v2

HERE=Path(__file__).resolve().parent

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--layout',type=int,choices=(0,1),required=True)
    args=ap.parse_args();out=args.out.resolve()
    spec=json.loads((HERE/'plan_v4.json').read_text())
    base=(HERE/'plan_v2.json').read_bytes()
    if hashlib.sha256(base).hexdigest()!=spec['base_plan_sha256']:raise ValueError('base plan mismatch')
    plan=json.loads(base);plan['allocation_id']=spec['allocation_id']
    plan['sources'].update(spec['extra_sources'])
    plan['supervision']=spec['supervision']
    staging=out.parent/(out.name+'-source-stage');staging.mkdir(parents=True,exist_ok=False)
    for name in plan['sources']:shutil.copy2(HERE/name,staging/name)
    (staging/'plan_v2.json').write_text(json.dumps(plan,indent=2)+'\n')
    experiment_v2.html=fixture_v2.html
    experiment_v2.HERE=staging
    experiment_v2.run(out,args.layout)
