from __future__ import annotations
import argparse, hashlib, itertools, json
from pathlib import Path
PROFILES={
 'SINGLE_STRONG':([100],True,'ALLOW'),'UNIQUE_WIDE':([100,70],True,'ALLOW'),'UNIQUE_EXACT_MARGIN':([100,80],True,'ALLOW'),
 'UNIQUE_NARROW':([100,85],False,None),'TWO_WAY_TIE':([100,100],False,None),'THREE_WAY_TIE':([100,100,100],False,None),
 'BELOW_MIN':([70,20],False,'REJECT'),'EMPTY':([],False,'REJECT')}
PROVENANCE=('VALID','STALE','WRONG_SOURCE','WRONG_GEOMETRY'); SOURCE_NAMES={'PLAN.md','experiment.py','audit.py','controls.py','test_contract.py','ENVIRONMENT.json','SCHEDULE.json'}
def sha(p): h=hashlib.sha256();h.update(p.read_bytes());return h.hexdigest()
def expected(profile,prov,probe):
 scores,safe,base=PROFILES[profile]
 if prov!='VALID': return False,'REJECT'
 if safe: return True,'ALLOW'
 if profile in {'UNIQUE_NARROW','TWO_WAY_TIE','THREE_WAY_TIE'}: return False,'PROBE' if probe else 'NEEDS_DECISION'
 return False,'REJECT'
def audit(path,source):
 d=json.loads(path.read_text()); errs=[]; rows=d.get('rows')
 if d.get('schema')!='target-belief-admission-4150-v1': errs.append('schema')
 if d.get('formal_invocations')!=1 or d.get('reruns')!=0 or d.get('replacements')!=0 or d.get('tuning_after_freeze')!=0: errs.append('invocations')
 if not isinstance(rows,list) or len(rows)!=64: return {'pass':False,'errors':errs+['row_count']}
 expected_keys=set(itertools.product(PROFILES,PROVENANCE,(False,True))); seen=set(); counts={x:0 for x in ('ALLOW','PROBE','NEEDS_DECISION','REJECT')}; cfa=tfa=csa=mismatch=autherr=0
 for r in rows:
  key=(r.get('profile'),r.get('provenance'),r.get('probe_available')); seen.add(key)
  if key not in expected_keys: errs.append('unexpected_row'); continue
  safe,decision=expected(*key)
  if r.get('scores')!=PROFILES[key[0]][0] or r.get('oracle_safe_to_act') is not safe or r.get('oracle_decision')!=decision: errs.append('oracle')
  cd=r.get('candidate_decision'); td=r.get('top1_decision')
  if cd not in counts: errs.append('candidate_decision'); continue
  counts[cd]+=1; cfa+=cd=='ALLOW' and not safe; tfa+=td=='ALLOW' and not safe; csa+=cd=='ALLOW' and safe; mismatch+=cd!=decision; autherr+=r.get('candidate_input_authority')!=(cd=='ALLOW')
 if seen!=expected_keys or len(seen)!=64: errs.append('coverage')
 s={'rows':64,'candidate_counts':counts,'candidate_false_allow':cfa,'top1_false_allow':tfa,'candidate_safe_allow':csa,'candidate_oracle_mismatch':mismatch,'authority_errors':autherr}
 if d.get('summary')!=s: errs.append('summary')
 expected_dec='PASS_TARGET_BELIEF_ADMISSION_CONTRACT_SCOPED' if s=={'rows':64,'candidate_counts':{'ALLOW':6,'PROBE':3,'NEEDS_DECISION':3,'REJECT':52},'candidate_false_allow':0,'top1_false_allow':6,'candidate_safe_allow':6,'candidate_oracle_mismatch':0,'authority_errors':0} else 'FAIL_TARGET_BELIEF_ADMISSION_CONTRACT'
 if d.get('decision')!=expected_dec: errs.append('decision')
 src={p.name:sha(p) for p in source.iterdir() if p.is_file() and p.name in SOURCE_NAMES}
 if d.get('source_sha256')!=dict(sorted(src.items())): errs.append('source_sha256')
 return {'pass':not errs,'errors':errs,'decision':d.get('decision'),'summary':s}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--result',type=Path,required=True);ap.add_argument('--source-dir',type=Path,required=True);ap.add_argument('--out',type=Path);a=ap.parse_args();o=audit(a.result,a.source_dir)
 if a.out:a.out.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n')
 print(json.dumps(o,sort_keys=True));raise SystemExit(0 if o['pass'] else 1)
if __name__=='__main__':main()
