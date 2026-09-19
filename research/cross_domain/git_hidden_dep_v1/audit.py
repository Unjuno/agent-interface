from __future__ import annotations
import argparse,json,subprocess
from pathlib import Path

def sh(repo,*args):
    p=subprocess.run(args,cwd=repo,text=True,capture_output=True)
    if p.returncode: raise AssertionError((args,p.returncode,p.stderr))
    return p.stdout.strip()
def b(repo,c,p): return sh(repo,'git','rev-parse',f'{c}:{p}')

def audit_case(d:Path):
    r=json.loads((d/'result.json').read_text()); repo=d/'repo'; assert r['planned_ns']<=r['delivered_ns']<=r['finished_ns']
    for k in ['A','B','C','D','E']: assert sh(repo,'git','cat-file','-t',r[k])=='commit'
    assert r['A_declared']!=r['C_declared']; assert r['A_declared']==r['D_declared']==r['E_declared']
    assert r['A_hidden']==r['C_hidden']==r['E_hidden']; assert r['A_hidden']!=r['D_hidden']
    for k in ['A','C','D','E']:
        assert b(repo,r[k],'declared.txt')==r[f'{k}_declared']; assert b(repo,r[k],'hidden.txt')==r[f'{k}_hidden']
    final=sh(repo,'git','rev-parse','refs/heads/target'); assert final==r['final_target']
    current={'stable':r['A'],'declared_changed':r['C'],'hidden_changed':r['D'],'unrelated_changed':r['E']}[r['schedule']]
    ground=r['B'] if r['schedule'] in ('stable','unrelated_changed') else current
    assert r['ground_truth_final']==ground; assert r['ground_truth_correct']==(final==ground)
    declared_ok=r['schedule']!='declared_changed'; hidden_ok=r['schedule']!='hidden_changed'
    assert r['declared_ok']==declared_ok; assert r['hidden_ok']==hidden_ok
    pred=declared_ok if r['policy']=='declared_only' else declared_ok and hidden_ok
    assert r['predicate_valid']==pred
    if pred: assert r['returncode']==0 and final==r['B']
    else: assert r['returncode']!=0 and final==current
    assert sh(repo,'git','reflog','show','--format=%H%x09%gs','refs/heads/target').splitlines()==r['reflog']
    return r

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root',type=Path); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); ds=sorted(p for p in a.root.iterdir() if p.is_dir() and (p/'result.json').is_file()); rows=[audit_case(d) for d in ds]
    by={}
    for r in rows:
        k=f"{r['policy']}:{r['schedule']}"; s=by.setdefault(k,{'n':0,'correct':0,'accepts':0,'rejects':0}); s['n']+=1;s['correct']+=int(r['ground_truth_correct']);s['accepts']+=int(r['returncode']==0);s['rejects']+=int(r['returncode']!=0)
    out={'schema':'git-hidden-dep-audit-v1','cases':len(rows),'all_integrity_pass':len(rows)>0,'by_cell':by}; a.out.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__': main()
