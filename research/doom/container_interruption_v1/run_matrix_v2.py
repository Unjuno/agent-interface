"""Same matrix as v1; validate all runtime dependencies before allocation creation."""
import argparse
import json
import os
import platform
from pathlib import Path
import sys
import time

import run_matrix as previous
from run_matrix import BASE, CASES, digest, write, run_case


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--repo',type=Path,required=True)
    ap.add_argument('--bundle-manifest',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();repo=a.repo.resolve();out=a.out.resolve()
    here=Path(__file__).resolve().parent
    plan=json.loads((here/'plan_v2.json').read_text())
    manifest=json.loads(a.bundle_manifest.read_text())
    if plan['base_commit']!=BASE or manifest['base_commit']!=BASE or plan['cases']!=CASES:
        raise RuntimeError('base/plan mismatch')
    for n,h in plan['source_sha256'].items():
        if digest(here/n)!=h:raise RuntimeError('candidate hash mismatch '+n)
    for n,item in manifest['files'].items():
        if digest(repo/n)!=item['sha256']:raise RuntimeError('base drift '+n)
    # The prior allocation failed here before any GUI: the system-site venv did
    # not include PIL. Do not allow a partial dependency check to consume a run.
    import PIL, Xlib, openpyxl, numpy, vizdoom
    sys.path[:0]=[str(repo/'research/doom'),str(repo/'research/live_control'),
                  str(repo/'research/observation_gating')]
    import session_map01_v12, doom_retained_input_backend_v3, executor_v12
    cpu=next((x.split(':',1)[1].strip() for x in Path('/proc/cpuinfo').read_text().splitlines()
              if x.startswith('model name')),'unknown')
    environment={'python':sys.version,'platform':platform.platform(),'cpu':cpu,
        'cpu_affinity':sorted(os.sched_getaffinity(0)), 'cpu_frequency':'uncontrolled/shared host',
        'clock':vars(time.get_clock_info('perf_counter')),'vizdoom':vizdoom.__version__,
        'pillow':PIL.__version__,'numpy':numpy.__version__,'openpyxl':openpyxl.__version__,
        'source_bundle_manifest_sha256':digest(a.bundle_manifest),'base_commit':BASE}
    out.mkdir(parents=True,exist_ok=False)
    write(out/'plan.json',plan);write(out/'environment.json',environment)
    results=[];error=None
    for case in CASES:
        try:
            r=run_case(repo,out/case['name'],case,plan['seed']);results.append(r)
            print(json.dumps({'case':r['case'],'pass':r['pass'],'status':r['terminal_status'],
                              'occupancy':r['occupancy']}),flush=True)
        except Exception as exc:
            error=repr(exc);break
    result={'schema':'container-map01-interruption-matrix-v2','allocation_id':plan['allocation_id'],
        'cases_completed':len(results),'planned_cases':len(CASES),'pass':error is None and len(results)==len(CASES),
        'error':error,'results':results,'model_calls':0}
    write(out/'summary.json',result)
    write(out/'artifact-manifest.json',{str(p.relative_to(out)):{'sha256':digest(p),'bytes':p.stat().st_size}
                                       for p in sorted(out.rglob('*')) if p.is_file()})
    print(json.dumps({'matrix_pass':result['pass'],'error':error}),flush=True)
    raise SystemExit(0 if result['pass'] else 1)

if __name__=='__main__':main()
