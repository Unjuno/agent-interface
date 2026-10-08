"""Effective well-formed evidence mutations; never execute a measurement."""
import copy,hashlib,json,shutil,sys,tempfile
from pathlib import Path
from audit import audit


def write(p,v):p.write_text(json.dumps(v,sort_keys=True,separators=(',',':'))+'\n')
def load(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def rebind(path,policy):
    p=path/(policy+'.json');h=sha(p);size=p.stat().st_size
    rows=[json.loads(x) for x in (path/'samples.jsonl').read_bytes().splitlines()]
    for r in rows:
        if r['policy']==policy:r.update(sha256=h,bytes=size)
    (path/'samples.jsonl').write_text(''.join(json.dumps(r,separators=(',',':'),sort_keys=True)+'\n' for r in rows))
    r=load(path/'RECORD.json');r['accounting'][policy]['output_sha256']=h;write(path/'RECORD.json',r)


def mutate(root,i,construction):
    parent=root/('construction' if construction else 'formal');name='construction' if construction else 'c0';p=parent/name
    if i in (0,1,2):
        f=p/'samples.jsonl';rows=[json.loads(x) for x in f.read_bytes().splitlines()]
        if i==0:rows.pop()
        elif i==1:rows[-1]=copy.deepcopy(rows[0])
        else:rows[-1]['wall_end_ns']=rows[-1]['wall_start_ns']-1
        f.write_text(''.join(json.dumps(r,separators=(',',':'))+'\n' for r in rows))
    elif i in (3,4,5,6,7,8):
        for policy in ('baseline','candidate'):
            f=p/(policy+'.json');r=load(f)
            if i==3:r['authority']='input'
            elif i==4:r['outcome_summary']['recovery_required']=False
            elif i==5:r['outcome_summary']['input_release_verified']=True
            elif i==6:r['image_reference']['sha256']='0'*64
            elif i==7:r['receipt']['source']['sha256']='0'*64
            elif i==8:r['image']['data']='AA=='
            write(f,r);rebind(p,policy)
    elif i==9:
        f=p/'RECORD.json';r=load(f);r['accounting']['candidate']['reads']*=2;write(f,r)
    elif i==10:
        f=parent/(name+'.exit.json');r=load(f);r['returncode']=False;write(f,r)
    elif i==11:
        f=p/'RECORD.json';r=load(f);r['pid']+=100000;write(f,r)


def run(root,construction=False):
    root=Path(root);original=audit(root,construction)
    if original['errors']:raise ValueError('ORIGINAL_AUDIT_FAILED')
    rows=[]
    for i in range(12):
        with tempfile.TemporaryDirectory(prefix='c7r8-control-') as td:
            d=Path(td)/'study';shutil.copytree(root,d)
            before={str(p.relative_to(d)):sha(p) for p in d.rglob('*') if p.is_file()}
            mutate(d,i,construction)
            after={str(p.relative_to(d)):sha(p) for p in d.rglob('*') if p.is_file()}
            changed=[k for k in before if before[k]!=after[k]]
            r=audit(d,construction)
            row={'mutation':i,'changed_files':changed,'rejected':bool(r['errors']),
                 'errors':r['errors'],'effective':bool(changed),'normal_audit_return':True}
            rows.append(row)
    ok=all(r['rejected'] and r['effective'] for r in rows)
    return {'pass':ok,'count':len(rows),'original_errors':original['errors'],'mutations':rows}


if __name__=='__main__':
    r=run(sys.argv[1],construction='--construction' in sys.argv)
    print(json.dumps(r,indent=2,sort_keys=True));sys.exit(not r['pass'])
