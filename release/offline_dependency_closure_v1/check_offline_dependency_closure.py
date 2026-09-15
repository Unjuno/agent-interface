from __future__ import annotations
import argparse, json, re, subprocess, tempfile, time
from pathlib import Path

def canon(name:str)->str:return re.sub(r'[-_.]+','-',name).lower()
def wheel_index(directory:Path):
    out={}
    for p in directory.glob('*.whl'):
        parts=p.name[:-4].split('-')
        if len(parts)>=2: out.setdefault(canon(parts[0]),set()).add(parts[1])
    return out

def inspect(requirements:Path,wheelhouse:Path,run_pip=False):
    avail=wheel_index(wheelhouse); rows=[]
    for raw in requirements.read_text(encoding='utf-8').splitlines():
        line=raw.strip()
        if not line or line.startswith('#'):continue
        if line.count('==')!=1: raise ValueError(f'exact pin required: {line}')
        name,ver=line.split('==',1); versions=sorted(avail.get(canon(name),set()))
        rows.append({'requirement':line,'available_versions':versions,'exact_match':ver in versions})
    result={'schema':'golden-offline-dependency-closure-v1','passed':all(r['exact_match'] for r in rows),
            'requirements_total':len(rows),'exact_matches':sum(r['exact_match'] for r in rows),
            'requirements':rows,'wheelhouse_files':len(list(wheelhouse.glob('*.whl'))),
            'claim_boundary':'offline exact-pin wheelhouse closure only; not supported-host online compatibility'}
    result['status']='PASS_OFFLINE_EXACT_PIN_CLOSURE' if result['passed'] else 'FAIL_OFFLINE_EXACT_PIN_CLOSURE'
    if run_pip:
        with tempfile.TemporaryDirectory() as td:
            venv=Path(td)/'venv'; subprocess.run(['python3','-m','venv',str(venv)],check=True)
            start=time.perf_counter_ns(); cp=subprocess.run([str(venv/'bin/python'),'-m','pip','install','--disable-pip-version-check','--no-index',f'--find-links={wheelhouse}','-r',str(requirements)],capture_output=True,text=True)
            result['pip']={'exit_code':cp.returncode,'elapsed_ms':(time.perf_counter_ns()-start)/1e6,'stdout':cp.stdout,'stderr':cp.stderr}
    return result

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('requirements',type=Path);ap.add_argument('wheelhouse',type=Path);ap.add_argument('--run-pip',action='store_true');ap.add_argument('--out',type=Path)
    a=ap.parse_args(); r=inspect(a.requirements,a.wheelhouse,a.run_pip); text=json.dumps(r,indent=2)+'\n'
    if a.out:a.out.write_text(text,encoding='utf-8')
    print(text,end=''); return 0 if r['passed'] else 1
if __name__=='__main__': raise SystemExit(main())
