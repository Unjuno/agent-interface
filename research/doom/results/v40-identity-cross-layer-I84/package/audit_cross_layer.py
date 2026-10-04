import json
from pathlib import Path
root=Path(__file__).resolve().parent
raw=json.loads((root/'raw-cases.json').read_text(encoding='utf8'))
# Candidate output is provided on stdin by the caller so this auditor does not import either implementation.
import sys
candidate=json.load(sys.stdin)
expected={c['case']:c for c in raw['cases']}
errors=[]
for row in candidate['results']:
    case=expected[row['case']]
    if row['producer_verified'] is not case['expected_verified']:
        errors.append({'case':row['case'],'field':'producer_verified','expected':case['expected_verified'],'actual':row['producer_verified']})
    if row['consumer_result']['measurement_ready'] is not case['expected_ready']:
        errors.append({'case':row['case'],'field':'measurement_ready','expected':case['expected_ready'],'actual':row['consumer_result']['measurement_ready']})
    if row['case']=='matching_nonempty_string' and row['consumer_result']['hold_count']!=1:
        errors.append({'case':row['case'],'field':'valid_hold_count','expected':1,'actual':row['consumer_result']['hold_count']})
summary={'schema':'map01-v3-backend-direct-analyzer-token-cross-layer-audit-I84-v1','case_count':len(candidate['results']),'positive_control':'matching_nonempty_string','invalid_identity_cases':len(candidate['results'])-1,'errors':errors,'decision':'PASS_PRODUCER_CONSUMER_IDENTITY_ALIGNMENT' if not errors and len(candidate['results'])==len(expected) else 'FAIL'}
print(json.dumps(summary,indent=2))
if summary['decision']!='PASS_PRODUCER_CONSUMER_IDENTITY_ALIGNMENT': raise SystemExit(1)
