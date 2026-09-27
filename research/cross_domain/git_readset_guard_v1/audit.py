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
    for k in ['A','B','D','H','U']:
        assert sh(repo,'git','cat-file','-t',r[k])=='commit'
    read_paths=[x['path'] for x in r['plan_read_set']]
    assert read_paths==['declared.txt','hidden.txt']
    for x in r['plan_read_set']:
        assert x['blob_oid']==sh(repo,'git','rev-parse',f"{r['A']}:{x['path']}")
    assert r['planner_declared']==['declared.txt']
    if r['policy']=='observed_readset': assert r['validated_paths']==['declared.txt','hidden.txt']
    else: assert r['validated_paths']==['declared.txt']
    final=sh(repo,'git','rev-parse','refs/heads/target')
    assert final==r['final_target']
    expected = {'stable':r['B'],'unrelated_changed':r['B'],'declared_changed':r['D'],'hidden_changed':r['H']}[r['schedule']]
    assert r['expected_final']==expected
    expected_correct = not (r['policy']=='planner_declared' and r['schedule']=='hidden_changed')
    assert r['ground_truth_correct']==expected_correct
    if expected_correct: assert final==expected
    else: assert final==r['B'] and final!=expected
    should_reject = (r['schedule']=='declared_changed') or (r['policy']=='observed_readset' and r['schedule']=='hidden_changed')
    if should_reject:
        assert r['returncode']==97
    else:
        assert r['returncode']==0
    reflog=sh(repo,'git','reflog','show','--format=%H%x09%gs','refs/heads/target').splitlines()
    assert reflog==r['reflog']
    return r

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root',type=Path); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    ds=sorted(p for p in a.root.iterdir() if p.is_dir() and (p/'result.json').is_file())
    rows=[audit_case(d) for d in ds]; by={}
    for r in rows:
        k=f"{r['policy']}:{r['schedule']}"; s=by.setdefault(k,{'n':0,'correct':0,'rejects':0,'writes_B':0})
        s['n']+=1; s['correct']+=int(r['ground_truth_correct']); s['rejects']+=int(r['returncode']!=0); s['writes_B']+=int(r['final_target']==r['B'])
    out={'schema':'git-readset-guard-audit-v1','cases':len(rows),'by_cell':by,'all_integrity_pass':len(rows)>0}
    a.out.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__': main()
