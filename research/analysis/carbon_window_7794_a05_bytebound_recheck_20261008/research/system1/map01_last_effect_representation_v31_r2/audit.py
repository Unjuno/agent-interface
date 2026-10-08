from __future__ import annotations
import base64, hashlib, json, sys
from collections import defaultdict
from pathlib import Path

def stable(v): return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def gblob(b): return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def is_eligible(r):
 e=r['eligibility']; return e['planner_turn_status']=='completed' and e['planner_answer_eligible'] is True and e['model_action_discarded'] is False and e['plan_terminal']=='completed' and r['teacher_label'] is not None
def prior(rows,it):
 lookup={r['iteration']:r for r in rows}
 for j in range(it-1,-1,-1):
  r=lookup.get(j)
  if not r: continue
  e=r['eligibility']
  if e['model_action_discarded'] is False and e['plan_terminal']=='completed':
   recs=r.get('own_effect_receipts',[])
   if not recs:return {'kind':'UNKNOWN','source_iteration':j}
   x=recs[-1]; return {'kind':'RECEIPT','action':x['action'],'extent':x['extent'],'result':x['result'],'source_iteration':j}
 return {'kind':'NONE'}
def rep(x):
 if x['kind']!='RECEIPT': return {'kind':x['kind']}
 return {k:x[k] for k in ('kind','action','extent','result')}
def collisions(rows,enriched):
 d=defaultdict(list)
 for r in rows:
  if not is_eligible(r):continue
  raw=base64.b64decode(r['prompt_b64'])
  payload=raw if not enriched else raw+b'\0LAST_EFFECT\0'+stable(rep(prior(rows,r['iteration']))).encode()
  key=hashlib.sha256(payload).hexdigest(); d[key].append((r['iteration'],stable(r['teacher_label'])))
 out=[]
 for k,v in d.items():
  if len(set(x[1] for x in v))>1:out.append(sorted(x[0] for x in v))
 return sorted(out),len(d)
def main():
 f=json.loads(Path(sys.argv[1]).read_text()); result=json.loads(Path(sys.argv[2]).read_text()); rows=f['rows']; errs=[]
 if f['source'].get('v31_report_git_blob')!='2aed2e7e3f58b4f8b013fc98c79482a4036225ae':errs.append('report_blob')
 if f['source'].get('source_rows_git_blob')!='4ab9129253b0c2d976c932d07ed744528ea23734':errs.append('source_rows_blob')
 if f['source'].get('predecessor_result_git_blob')!='d08d66c07ed70cd4f02609a1122df664b90f1a2c':errs.append('predecessor_result_blob')
 for r in rows:
  try: raw=base64.b64decode(r['prompt_b64'],validate=True)
  except Exception: errs.append(f"prompt_b64:{r['iteration']}"); continue
  if gblob(raw)!=r['prompt_git_blob']:errs.append(f"prompt_blob:{r['iteration']}")
  if is_eligible(r)!=r['eligible_expected']:errs.append(f"eligibility:{r['iteration']}")
  if prior(rows,r['iteration'])!=r['last_effect_receipt']:errs.append(f"receipt:{r['iteration']}")
 pcol,pg=collisions(rows,False); ecol,eg=collisions(rows,True)
 if [r['iteration'] for r in rows if is_eligible(r)]!=[1,2,3,4,5]:errs.append('eligible_set')
 if pcol!=[[1,2]]:errs.append('prompt_collision')
 if prior(rows,1)!={'kind':'NONE'}:errs.append('iter1_none')
 if prior(rows,2)!={'kind':'RECEIPT','action':'retreat_fire','extent':'short','result':'visible_change','source_iteration':1}:errs.append('iter2_receipt')
 if ecol:errs.append('enriched_collision')
 expected_decision='PASS_LAST_EFFECT_REPRESENTATION_V31_R2_SCOPED' if not errs else 'FAIL_INTEGRITY'
 if result.get('formal_invocations')!=1 or result.get('reruns')!=0:errs.append('invocation')
 if result.get('prompt_signature_groups')!=pg or result.get('enriched_signature_groups')!=eg:errs.append('group_counts')
 if sorted([sorted(x['iterations']) for x in result.get('prompt_collisions',[])])!=pcol:errs.append('result_prompt_collision')
 if result.get('enriched_collisions')!=[]:errs.append('result_enriched_collision')
 if result.get('decision')!='PASS_LAST_EFFECT_REPRESENTATION_V31_R2_SCOPED' or result.get('pass') is not True:errs.append('result_decision')
 out={'pass':not errs,'errors':errs,'decision':'PASS_LAST_EFFECT_REPRESENTATION_V31_R2_SCOPED' if not errs else 'FAIL_INTEGRITY','fixture_sha256':hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest(),'result_sha256':hashlib.sha256(Path(sys.argv[2]).read_bytes()).hexdigest(),'eligible_rows':5,'prompt_collision_iterations':[1,2],'enriched_collision_groups':0}
 Path(sys.argv[3]).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True));raise SystemExit(0 if not errs else 2)
if __name__=='__main__':main()
