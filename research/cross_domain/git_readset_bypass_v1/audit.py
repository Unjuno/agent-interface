import argparse,json,subprocess
from pathlib import Path

def sh(repo,*a):
    p=subprocess.run(a,cwd=repo,text=True,capture_output=True); assert p.returncode==0,(a,p.stderr); return p.stdout.strip()
def audit_case(d):
    r=json.loads((d/'result.json').read_text()); repo=d/'repo'; assert r['planned_ns']<=r['delivered_ns']<=r['finished_ns']
    paths=[x['path'] for x in r['plan_read_set']]
    assert paths==(['declared.txt','hidden.txt'] if r['policy']=='all_traced' else ['declared.txt'])
    for x in r['plan_read_set']: assert x['blob_oid']==sh(repo,'git','rev-parse',f"{r['A']}:{x['path']}")
    final=sh(repo,'git','rev-parse','refs/heads/target'); assert final==r['final_target']
    expected={'stable':r['B'],'unrelated_changed':r['B'],'hidden_changed':r['H']}[r['schedule']]; assert r['expected_final']==expected
    expected_correct=not(r['policy']=='hidden_bypass' and r['schedule']=='hidden_changed'); assert r['ground_truth_correct']==expected_correct
    if expected_correct: assert final==expected
    else: assert final==r['B'] and final!=expected
    should_reject=r['policy']=='all_traced' and r['schedule']=='hidden_changed'; assert (r['returncode']!=0)==should_reject
    assert r['reflog']==sh(repo,'git','reflog','show','--format=%H%x09%gs','refs/heads/target').splitlines(); return r

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root',type=Path); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); rows=[audit_case(d) for d in sorted(a.root.iterdir()) if d.is_dir() and (d/'result.json').exists()]; by={}
    for r in rows:
        k=f"{r['policy']}:{r['schedule']}"; s=by.setdefault(k,{'n':0,'correct':0,'rejects':0}); s['n']+=1; s['correct']+=int(r['ground_truth_correct']); s['rejects']+=int(r['returncode']!=0)
    out={'schema':'git-readset-bypass-audit-v1','cases':len(rows),'by_cell':by,'all_integrity_pass':len(rows)>0}; a.out.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__': main()
