#!/usr/bin/env python3
import copy, json, shutil, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
AUDIT=ROOT/'audit.py'

def load(root,i):
    p=root/f'case-{i:02d}.json'; return p,json.loads(p.read_text())
def save(p,x): p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')

def run(root):
    p=subprocess.run([sys.executable,'-B',str(AUDIT),str(root)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    return {'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}

def main():
    if len(sys.argv)!=2: raise SystemExit('usage: controls.py FORMAL_ROOT')
    src=Path(sys.argv[1])
    cases=[
      ('missing_case', lambda r: (r/'case-19.json').unlink()),
      ('schedule_arm', lambda r: (lambda p,x:(x['cfg'].__setitem__('arm','HIT_GRAB_PROBE'),save(p,x)))(*load(r,0))),
      ('leaf_identity', lambda r: (lambda p,x:(x.__setitem__('leaf',x['leaf']+1),save(p,x)))(*load(r,0))),
      ('probe_bool', lambda r: (lambda p,x:(x.__setitem__('probe',True),save(p,x)))(*load(r,3))),
      ('probe_false_success', lambda r: (lambda p,x:(x.__setitem__('probe',0),save(p,x)))(*load(r,3))),
      ('foreign_press_removed', lambda r: (lambda p,x:(x['grabber'].__setitem__('press',0),save(p,x)))(*load(r,2))),
      ('wrong_text_added', lambda r: (lambda p,x:(x['final'].__setitem__('a','7'),save(p,x)))(*load(r,2))),
      ('bad_app_exit', lambda r: (lambda p,x:(x.__setitem__('app_exit',23),save(p,x)))(*load(r,0))),
      ('neutral_false', lambda r: (lambda p,x:(x.__setitem__('neutral',False),save(p,x)))(*load(r,0))),
    ]
    out={}
    for name,mut in cases:
        with tempfile.TemporaryDirectory(prefix='pg-mut-') as td:
            dst=Path(td)/'formal';shutil.copytree(src,dst);mut(dst);res=run(dst)
            out[name]={'rejected':res['returncode']!=0,'returncode':res['returncode']}
    print(json.dumps(out,indent=2,sort_keys=True))
    raise SystemExit(0 if all(v['rejected'] for v in out.values()) else 1)
if __name__=='__main__':main()
