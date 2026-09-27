from __future__ import annotations
import argparse,copy,json
from pathlib import Path
from audit_v4 import audit_rows

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--root',type=Path,required=True);a=ap.parse_args()
 base=json.loads(a.results.read_text());checks=[]
 def check(name,rows,needle):
  errors=audit_rows(rows,a.root,True)
  ok=any(needle in e for e in errors)
  checks.append({'mutation':name,'rejected':ok,'matching_error':next((e for e in errors if needle in e),None)})
  if not ok:raise AssertionError(f'{name} not rejected: {errors}')
 if audit_rows(base,a.root,True):raise AssertionError('baseline evidence did not pass')
 check('empty',[], 'case_count')
 check('truncated',base[:-1], 'case_count')
 bad=copy.deepcopy(base);bad[0]['terminal_status']='failed';check('terminal_failure',bad,'terminal_not_completed')
 bad=copy.deepcopy(base);bad[0]['release']['verified']=False;check('unverified_release',bad,'release_not_verified_empty')
 bad=copy.deepcopy(base);bad[0]['score']['death_count']=1;check('nonzero_death',bad,'unsafe_or_missing_score')
 bad=copy.deepcopy(base);bad[2]['candidate_receipt']['session_id']='foreign-session';check('foreign_session_mutation',bad,'receipt_recomputation_mismatch')
 report={'schema':'issue-2548-auditor-mutation-check-v1','status':'PASS' if all(x['rejected'] for x in checks) else 'FAIL','checks':checks}
 print(json.dumps(report,indent=2,sort_keys=True))
if __name__=='__main__':main()
