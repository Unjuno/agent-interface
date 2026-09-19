import json,hashlib,sys,collections
from pathlib import Path

def sha(b):return hashlib.sha256(b).hexdigest()
def manifest(root):
 for n,h in json.loads((root/'manifest.json').read_text()).items():
  if sha((root/n).read_bytes())!=h:raise AssertionError(('hash',root.name,n))
def audit_a6(root):
 rs=[json.loads(x) for x in (root/'raw.jsonl').read_text().splitlines()];assert len(rs)==18;meta=json.loads((root/'prereg.json').read_text());A=meta['commit_ids']['A'];B=meta['commit_ids']['B'];C=meta['commit_ids']['C'];cnt=collections.Counter()
 for r in rs:
  assert all(r['mechanics'].values());assert r['checked']['current']==A;assert r['competitor_start_ns']>=r['checked']['read_end_ns'];assert r['terminal']['effect_start_ns']>=r['competitor_end_ns'];t=r['after']['target'];u=r['after']['unrelated'];rc=r['terminal']['git_returncode']
  if r['case']=='stable':cl='correct';assert t==B and u==A and rc==0
  elif r['case']=='target_changed_after_check' and r['mode']=='nonatomic_precheck':cl='wrong_overwrite';assert t==B and u==A and rc==0
  elif r['case']=='target_changed_after_check':cl='safe_reject';assert t==C and u==A and rc!=0
  else:cl='correct_unrelated_progress';assert t==B and u==C and rc==0
  cnt[(r['case'],r['mode'],cl)]+=1
 manifest(root);return cnt
def audit_r2(root):
 rs=[json.loads(x) for x in (root/'raw.jsonl').read_text().splitlines()];assert len(rs)==12;meta=json.loads((root/'prereg.json').read_text());A=meta['A'];B=meta['B'];C=meta['C'];cnt=collections.Counter()
 for r in rs:
  if r['case']=='stable':cl='correct';assert r['final_ref']==B and r['terminal']['returncode']==0 and r['terminal']['expected_used']==A
  elif r['mode']=='plan_bound_cas':cl='safe_reject';assert r['final_ref']==C and r['terminal']['returncode']!=0 and r['terminal']['expected_used']==A
  else:cl='wrong_laundered_overwrite';assert r['final_ref']==B and r['terminal']['returncode']==0 and r['terminal']['expected_used']==C
  assert r['terminal']['effect_start_ns']>=r['competitor_end_ns'];cnt[(r['case'],r['mode'],cl)]+=1
 manifest(root);return cnt
def audit_bench(root):
 rs=[json.loads(x) for x in (root/'raw.jsonl').read_text().splitlines()];assert len(rs)==600;cnt=collections.Counter()
 for r in rs:
  assert r['ns']>0
  if r['mode']=='blind_changed':assert r['returncode']==0 and r['classification']=='wrong_overwrite'
  elif r['mode']=='cas_stable':assert r['returncode']==0 and r['classification']=='correct'
  elif r['mode']=='cas_mismatch':assert r['returncode']!=0 and r['classification']=='safe_reject'
  else:raise AssertionError(r)
  cnt[(r['mode'],r['classification'])]+=1
 return cnt
def main(base):
 b=Path(base);out={'a6':{'|'.join(k):v for k,v in audit_a6(b/'run-a6').items()},'r2':{'|'.join(k):v for k,v in audit_r2(b/'run-r2-a1').items()},'bench':{'|'.join(k):v for k,v in audit_bench(b/'bench-a1').items()},'checked_rows':630};(b/'audit_all_result.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main(sys.argv[1])
