from __future__ import annotations
import argparse, hashlib, itertools, json
from pathlib import Path
MIN_SCORE=80
REQUIRED_MARGIN=20
PROFILES={
 'SINGLE_STRONG':[100],
 'UNIQUE_WIDE':[100,70],
 'UNIQUE_EXACT_MARGIN':[100,80],
 'UNIQUE_NARROW':[100,85],
 'TWO_WAY_TIE':[100,100],
 'THREE_WAY_TIE':[100,100,100],
 'BELOW_MIN':[70,20],
 'EMPTY':[],
}
PROVENANCE=('VALID','STALE','WRONG_SOURCE','WRONG_GEOMETRY')
SAFE_ALLOW={'SINGLE_STRONG','UNIQUE_WIDE','UNIQUE_EXACT_MARGIN'}
AMBIGUOUS={'UNIQUE_NARROW','TWO_WAY_TIE','THREE_WAY_TIE'}

def sha256_file(p:Path):
 h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()

def top1_score_admit(scores,provenance,probe_available):
 if provenance!='VALID': return 'REJECT'
 if not scores or max(scores)<MIN_SCORE: return 'REJECT'
 return 'ALLOW'

def belief_margin_admit(scores,provenance,probe_available):
 if provenance!='VALID': return 'REJECT'
 if not scores: return 'REJECT'
 vals=sorted(scores,reverse=True)
 if vals[0]<MIN_SCORE: return 'REJECT'
 if len(vals)==1 or vals[0]-vals[1]>=REQUIRED_MARGIN: return 'ALLOW'
 return 'PROBE' if probe_available else 'NEEDS_DECISION'

def oracle(profile,provenance,probe_available):
 if provenance!='VALID': return {'safe_to_act':False,'expected':'REJECT'}
 if profile in SAFE_ALLOW: return {'safe_to_act':True,'expected':'ALLOW'}
 if profile in AMBIGUOUS: return {'safe_to_act':False,'expected':'PROBE' if probe_available else 'NEEDS_DECISION'}
 return {'safe_to_act':False,'expected':'REJECT'}

def make_rows():
 out=[]; idx=0
 for profile,provenance,probe in itertools.product(PROFILES,PROVENANCE,(False,True)):
  scores=PROFILES[profile]
  truth=oracle(profile,provenance,probe)
  c=belief_margin_admit(scores,provenance,probe)
  t=top1_score_admit(scores,provenance,probe)
  row={'row_id':f'r{idx:02d}','profile':profile,'scores':scores,'provenance':provenance,'probe_available':probe,
       'oracle_safe_to_act':truth['safe_to_act'],'oracle_decision':truth['expected'],
       'candidate_decision':c,'top1_decision':t,
       'candidate_input_authority':c=='ALLOW','top1_input_authority':t=='ALLOW',
       'candidate_false_allow':c=='ALLOW' and not truth['safe_to_act'],
       'top1_false_allow':t=='ALLOW' and not truth['safe_to_act']}
  out.append(row); idx+=1
 return out

def summary(rows):
 counts={k:sum(r['candidate_decision']==k for r in rows) for k in ('ALLOW','PROBE','NEEDS_DECISION','REJECT')}
 return {'rows':len(rows),'candidate_counts':counts,
         'candidate_false_allow':sum(r['candidate_false_allow'] for r in rows),
         'top1_false_allow':sum(r['top1_false_allow'] for r in rows),
         'candidate_safe_allow':sum(r['candidate_decision']=='ALLOW' and r['oracle_safe_to_act'] for r in rows),
         'candidate_oracle_mismatch':sum(r['candidate_decision']!=r['oracle_decision'] for r in rows),
         'authority_errors':sum(r['candidate_input_authority']!=(r['candidate_decision']=='ALLOW') for r in rows)}

def decide(s):
 ok=(s['rows']==64 and s['candidate_false_allow']==0 and s['top1_false_allow']==6 and s['candidate_safe_allow']==6 and
     s['candidate_counts']=={'ALLOW':6,'PROBE':3,'NEEDS_DECISION':3,'REJECT':52} and s['candidate_oracle_mismatch']==0 and s['authority_errors']==0)
 return 'PASS_TARGET_BELIEF_ADMISSION_CONTRACT_SCOPED' if ok else 'FAIL_TARGET_BELIEF_ADMISSION_CONTRACT'

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--source-dir',type=Path,required=True); a=ap.parse_args()
 rows=make_rows(); s=summary(rows); d=decide(s)
 names={'PLAN.md','experiment.py','audit.py','controls.py','test_contract.py','ENVIRONMENT.json','SCHEDULE.json'}
 src={p.name:sha256_file(p) for p in a.source_dir.iterdir() if p.is_file() and p.name in names}
 obj={'schema':'target-belief-admission-4150-v1','allocation':'target-belief-admission-4150-20260927-03','formal_invocations':1,'reruns':0,'replacements':0,'tuning_after_freeze':0,'decision':d,'summary':s,'rows':rows,'source_sha256':dict(sorted(src.items()))}
 a.out.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n'); print(json.dumps({'decision':d,'summary':s},sort_keys=True))
if __name__=='__main__': main()
