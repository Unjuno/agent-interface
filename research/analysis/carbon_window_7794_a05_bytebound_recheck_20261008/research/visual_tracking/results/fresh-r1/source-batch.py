import argparse,hashlib,json
from pathlib import Path
from run import run,HERE


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    paths=[HERE/n for n in ('arena.py','run.py','batch.py','PROTOCOL.md')]
    paths += [HERE.parent/'observation_gating/gui_suite.py',HERE.parent/'observation_gating/exact_gate.py',HERE.parent/'real_apps_v1/real_app_suite_v1.py']
    hashes={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    (a.out/'freeze.json').write_text(json.dumps(hashes,indent=2))
    for p in paths[:4]:(a.out/('source-'+p.name)).write_bytes(p.read_bytes())
    rows=[]
    try:
        for i,seed in enumerate(range(860201,860204)):
            for j,delay in enumerate((250,1000)):
                for mode in (('local','delayed') if (i+j)%2==0 else ('delayed','local')):
                    name=f'{seed}-{delay}-{mode}'
                    try:
                        r=run(a.out/name,seed,mode,delay,6);r['status']='ok'
                    except Exception as exc:
                        r=dict(seed=seed,delay_ms=delay,mode=mode,status='failed',error=repr(exc))
                    rows.append(r);print(json.dumps(r),flush=True)
    finally:(a.out/'summary.json').write_text(json.dumps(rows,indent=2))
