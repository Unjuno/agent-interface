from __future__ import annotations
import argparse,json,subprocess
from pathlib import Path

def sh(repo,*a):
    p=subprocess.run(['git','--no-replace-objects','-C',str(repo),*a],capture_output=True)
    if p.returncode: raise AssertionError((a,p.returncode,p.stderr.decode()))
    return p.stdout
def entries(repo,oid):
    out={}
    for item in sh(repo,'ls-tree','-rz',oid).split(b'\0'):
        if item:
            meta,name=item.split(b'\t',1); out[name.decode()]=tuple(meta.decode().split())
    return out
def audit_case(d):
    r=json.loads((d/'result.json').read_text()); repo=d/'repo.git'; ce=entries(repo,r['candidate']); cur=entries(repo,r['current'])
    desired=('desired-'+r['id']+'\n').encode(); actual=sh(repo,'show',f"{r['candidate']}:output/effect.txt") if 'output/effect.txt' in ce else b''
    bytes_ok=actual==desired; full_ok=('output/effect.txt' in ce and ce['output/effect.txt'][0]=='100644' and ce['output/effect.txt'][1]=='blob' and bytes_ok)
    assert bytes_ok==r['bytes_ok']; assert full_ok==r['full_ok']
    should=r['scenario'] in ('correct','unrelated_preserved'); correct=(r['reason']=='applied') if should else (r['reason']!='applied'); assert correct==r['ground_truth_correct']
    if r['scenario']=='unrelated_preserved' and r['reason']=='applied': assert sh(repo,'show',f"{r['final']}:keep.txt")==b'new keep\n'
    return r
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root',type=Path); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); rows=[audit_case(d) for d in sorted(a.root.iterdir()) if d.is_dir() and (d/'result.json').exists()]
    by={}
    for r in rows:
        k=r['policy']+':'+r['scenario']; s=by.setdefault(k,{'n':0,'correct':0,'applied':0}); s['n']+=1; s['correct']+=int(r['ground_truth_correct']); s['applied']+=int(r['reason']=='applied')
    out={'cases':len(rows),'all_evidence_valid':len(rows)>0,'by_cell':by}; a.out.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
if __name__=='__main__': main()
