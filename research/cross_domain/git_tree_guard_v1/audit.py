import argparse,json,subprocess
from pathlib import Path
def sh(repo,*args):
 p=subprocess.run(args,cwd=repo,text=True,capture_output=True); assert p.returncode==0,(args,p.stderr); return p.stdout.strip()
def audit_case(d):
 r=json.loads((d/'result.json').read_text());repo=d/'repo'
 for k in ['A','B','C','D']: assert sh(repo,'git','cat-file','-t',r[k])=='commit'
 assert sh(repo,'git','rev-parse',r['A']+'^{tree}')==r['A_tree']; assert sh(repo,'git','rev-parse',r['C']+'^{tree}')==r['A_tree']; assert sh(repo,'git','rev-parse',r['D']+'^{tree}')!=r['A_tree']
 final=sh(repo,'git','rev-parse','refs/heads/target'); assert final==r['final']; assert r['correct']==(final==r['ground'])
 if r['policy']=='exact_old':
  if r['schedule']=='stable': assert r['returncode']==0
  else: assert r['returncode']!=0
 if r['policy']=='tree_current_cas':
  if r['schedule']=='semantic_different': assert r['decision']=='predicate_reject' and r['returncode'] is None
  else: assert r['decision']=='attempted' and r['returncode']==0 and r['checked_tree']==r['A_tree']
 assert sh(repo,'git','reflog','show','--format=%H%x09%gs','refs/heads/target').splitlines()==r['reflog']
 return r
def main():
 ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();rows=[audit_case(d) for d in sorted(a.root.iterdir()) if d.is_dir() and (d/'result.json').exists()]
 by={}
 for r in rows:
  k=r['policy']+':'+r['schedule'];s=by.setdefault(k,{'n':0,'correct':0,'rejects':0});s['n']+=1;s['correct']+=int(r['correct']);s['rejects']+=int(r['decision']=='predicate_reject' or (r['returncode'] not in (0,None)))
 out={'schema':'git-tree-guard-audit-v1','cases':len(rows),'integrity_pass':True,'by_cell':by};a.out.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
