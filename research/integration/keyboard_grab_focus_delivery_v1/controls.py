#!/usr/bin/env python3
import copy, json, shutil, sys, tempfile
from pathlib import Path
import audit

def mutate(base,name):
    dst=Path(tempfile.mkdtemp(prefix='kg-control-'))
    for p in Path(base).glob('case-*.json'): shutil.copy2(p,dst/p.name)
    def load(i):
        p=dst/f'case-{i:02d}.json'; r=json.loads(p.read_text()); return p,r
    if name=='missing_case': (dst/'case-00.json').unlink(); return dst
    idx={'schedule':0,'focus_basis':0,'text':0,'foreign_count':2,'probe':3,'neutral':0,'exit':0,'sent':0,'key_event':0}[name]
    p,r=load(idx)
    if name=='schedule': r['cfg']['arm']='NO_TASK_INPUT'
    elif name=='focus_basis': r['pre']['focus']='.b'
    elif name=='text': r['final']['a']='x'
    elif name=='foreign_count': r['grabber']['press']=9
    elif name=='probe': r['probe']=9
    elif name=='neutral': r['neutral']=False
    elif name=='exit': r['app_exit']=1
    elif name=='sent': r['sent']=False
    elif name=='key_event': r['final']['keys']=[]
    p.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
    return dst

def main(root):
    names=['missing_case','schedule','focus_basis','text','foreign_count','probe','neutral','exit','sent','key_event']
    out={}
    for n in names:
        d=mutate(root,n)
        try: out[n]=bool(audit.audit(d)['errors'])
        finally: shutil.rmtree(d)
    print(json.dumps(out,indent=2,sort_keys=True))
    raise SystemExit(0 if all(out.values()) else 1)
if __name__=='__main__': main(sys.argv[1])
