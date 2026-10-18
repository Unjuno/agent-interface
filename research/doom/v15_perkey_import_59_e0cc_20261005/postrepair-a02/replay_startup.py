"""Materialize frozen PR #8065 sources and run the guarded boundary probe."""
from __future__ import annotations
import argparse, hashlib, json, subprocess, sys
from pathlib import Path

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('output',type=Path)
    args=parser.parse_args(); package=Path(__file__).resolve().parent
    manifest=json.loads((package/'source-manifest.json').read_text())
    args.output.mkdir(parents=True,exist_ok=False); source=(args.output/'source').resolve()
    for rel,record in manifest['files'].items():
        data=(package/'source-snapshots'/(rel+'.txt')).read_bytes()
        if len(data)!=record['bytes'] or hashlib.sha256(data).hexdigest()!=record['sha256']:
            raise ValueError('frozen source mismatch: '+rel)
        target=source/rel; target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(data)
    runner=package/'probe_startup.py'
    outcomes=[]
    for route in ('v12-perkey','v15-default','v15-perkey'):
        result=subprocess.run([sys.executable,'-B',str(runner),str(source),str((args.output/route).resolve()),route],capture_output=True,timeout=20)
        (args.output/(route+'.stdout.txt')).write_bytes(result.stdout); (args.output/(route+'.stderr.txt')).write_bytes(result.stderr)
        outcomes.append({'route':route,'exit_code':result.returncode})
        if result.returncode: break
    (args.output/'run-status.json').write_text(json.dumps(outcomes,indent=2)+'\n')
    return int(any(x['exit_code'] for x in outcomes))
if __name__=='__main__': raise SystemExit(main())
