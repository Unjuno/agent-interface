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
    for k in ['A','B','C']:
        assert sh(repo,'git','cat-file','-t',r[k])=='commit'
    final=sh(repo,'git','rev-parse','refs/heads/target')
    other=sh(repo,'git','rev-parse','refs/heads/unrelated')
    assert final==r['final_target']; assert other==r['final_other']
    ground=r['C'] if r['schedule']=='target_changed' else r['B']
    expected_nonzero=(r['policy']=='cas' and r['schedule']=='target_changed')
    assert r['expected_final']==ground
    assert ((r['returncode']!=0)==expected_nonzero)
    observed_correct=(final==ground and ((r['returncode']!=0)==expected_nonzero))
    assert r['correct']==observed_correct
    if expected_nonzero:
        assert 'expected' in r['stderr'] and r['A'] in r['stderr'] and r['C'] in r['stderr']
    else:
        assert r['returncode']==0
    if r['schedule']=='unrelated_changed': assert other==r['C']
    else: assert other==r['A']
    reflog=sh(repo,'git','reflog','show','--format=%H%x09%gs','refs/heads/target').splitlines()
    assert reflog==r['reflog']
    return r

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root',type=Path); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    ds=sorted([p for p in a.root.iterdir() if p.is_dir() and (p/'result.json').is_file()])
    rows=[audit_case(d) for d in ds]
    by={}
    for r in rows:
        k=f"{r['policy']}:{r['schedule']}"; s=by.setdefault(k,{'n':0,'ground_truth_correct':0,'writes_B':0,'preserves_C':0,'rejects':0})
        s['n']+=1; s['ground_truth_correct']+=int(r['correct']); s['writes_B']+=int(r['final_target']==r['B']); s['preserves_C']+=int(r['final_target']==r['C']); s['rejects']+=int(r['returncode']!=0)
    out={'schema':'git-ref-cas-audit-v2','cases':len(rows),'integrity_pass':True,'by_cell':by}
    a.out.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__': main()
