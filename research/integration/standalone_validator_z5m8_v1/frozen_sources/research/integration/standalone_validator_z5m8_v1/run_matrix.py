"""One-shot engineering allocation; never use this to overwrite retained results."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DIRECT = "import runpy,sys;sys.path.insert(0,sys.argv[1]);p=sys.argv[2];sys.argv=[p,'--program',sys.argv[3]];runpy.run_path(p,run_name='__main__')"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    source_hashes = json.loads((HERE/'FREEZE.json').read_text())['files']
    for rel, digest in source_hashes.items():
        if hashlib.sha256((ROOT/rel).read_bytes()).hexdigest() != digest:
            raise RuntimeError('frozen source mismatch: '+rel)
    builder = runpy.run_path(str(ROOT/'runtime/distribution_v2/build_validator.py'))
    metadata = builder['build'](ROOT, out/'validator.pyz', out/'artifact.json', out/'artifact.sha256')
    builder['build'](ROOT, out/'replica.pyz', out/'replica.json', out/'replica.sha256')
    if (out/'validator.pyz').read_bytes() != (out/'replica.pyz').read_bytes():
        raise RuntimeError('nondeterministic artifact')
    cwd=out/'outside-checkout'
    cwd.mkdir()
    env={k:v for k,v in os.environ.items() if k not in ('DISPLAY','WAYLAND_DISPLAY','PYTHONPATH','PYTHONHOME')}
    rows=[]
    start=time.monotonic_ns()
    with (out/'RAW.jsonl').open('x', encoding='utf-8') as journal:
        for case in json.loads((HERE/'CASES.json').read_text()):
            path=cwd/(case['id']+'.json')
            if not case['missing']:path.write_bytes(case['raw'].encode())
            for entry in ('source','archive'):
                if entry=='source':
                    cmd=[sys.executable,'-I','-S','-B','-c',DIRECT,str(ROOT),str(ROOT/'runtime/cli_v1/validate_program.py'),str(path)]
                else:
                    cmd=[sys.executable,'-I','-S','-B',str(out/'validator.pyz'),'--program',str(path)]
                before=time.monotonic_ns()
                p=subprocess.run(cmd,cwd=cwd,env=env,capture_output=True,timeout=10)
                row={'id':case['id'],'entry':entry,'argv':cmd,'cwd':str(cwd),
                     'start_ns':before,'end_ns':time.monotonic_ns(),'returncode':p.returncode,
                     'stdout':p.stdout.decode('utf-8'),'stderr':p.stderr.decode('utf-8'),
                     'input_after_sha256':hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None,
                     'display_unset':all(k not in env for k in ('DISPLAY','WAYLAND_DISPLAY','PYTHONPATH'))}
                journal.write(json.dumps(row,sort_keys=True)+'\n');journal.flush();rows.append(row)
    result={'status':'COMPLETED_NOT_YET_AUDITED','invocations':len(rows),
            'start_ns':start,'end_ns':time.monotonic_ns(),'python':sys.version,
            'artifact_sha256':metadata['sha256'],'source_root_has_git':(ROOT/'.git').exists()}
    (out/'RUN.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')


if __name__=='__main__':
    main()
