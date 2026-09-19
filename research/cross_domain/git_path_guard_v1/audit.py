from __future__ import annotations
import argparse,json,subprocess
from pathlib import Path

def sh(repo,*args):
    p=subprocess.run(args,cwd=repo,text=True,capture_output=True)
    if p.returncode: raise AssertionError((args,p.returncode,p.stderr))
    return p.stdout.strip()

def audit_case(d:Path):
    r=json.loads((d/'result.json').read_text()); repo=d/'repo'
    assert r['planned_ns'] <= r['delivered_ns'] <= r['finished_ns']
    for k in ['A','B','C','D']:
        assert sh(repo,'git','cat-file','-t',r[k])=='commit'
    assert sh(repo,'git','rev-parse',f"{r['A']}^{{tree}}") == r['A_tree']
    assert sh(repo,'git','rev-parse',f"{r['C']}^{{tree}}") == r['C_tree']
    assert sh(repo,'git','rev-parse',f"{r['D']}^{{tree}}") == r['D_tree']
    assert sh(repo,'git','rev-parse',f"{r['A']}:dependency.txt") == r['A_dep_blob']
    assert sh(repo,'git','rev-parse',f"{r['C']}:dependency.txt") == r['C_dep_blob']
    assert sh(repo,'git','rev-parse',f"{r['D']}:dependency.txt") == r['D_dep_blob']
    assert r['A_tree'] != r['C_tree']
    assert r['A_tree'] != r['D_tree']
    assert r['A_dep_blob'] == r['C_dep_blob']
    assert r['A_dep_blob'] != r['D_dep_blob']
    final=sh(repo,'git','rev-parse','refs/heads/target')
    assert final==r['final_target']
    ground=r['B'] if r['schedule'] in ('stable','unrelated_changed') else r['D']
    assert r['ground_truth_final']==ground
    assert r['ground_truth_correct']==(final==ground)
    if r['policy']=='tree_current_cas':
        pred = r['schedule']=='stable'
    elif r['policy']=='path_current_cas':
        pred = r['schedule'] in ('stable','unrelated_changed')
    else: raise AssertionError(r['policy'])
    assert r['predicate_valid']==pred
    if pred:
        assert r['returncode']==0 and final==r['B']
    else:
        assert r['returncode']!=0
        assert final==(r['C'] if r['schedule']=='unrelated_changed' else r['D'])
    reflog=sh(repo,'git','reflog','show','--format=%H%x09%gs','refs/heads/target').splitlines()
    assert reflog==r['reflog']
    return r

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root',type=Path); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    ds=sorted(p for p in a.root.iterdir() if p.is_dir() and (p/'result.json').is_file())
    rows=[audit_case(d) for d in ds]
    by={}
    for r in rows:
        k=f"{r['policy']}:{r['schedule']}"; s=by.setdefault(k,{'n':0,'correct':0,'accepts':0,'rejects':0})
        s['n']+=1; s['correct']+=int(r['ground_truth_correct']); s['accepts']+=int(r['returncode']==0); s['rejects']+=int(r['returncode']!=0)
    out={'schema':'git-path-guard-audit-v1','cases':len(rows),'all_integrity_pass':len(rows)>0,'by_cell':by}
    a.out.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__': main()
