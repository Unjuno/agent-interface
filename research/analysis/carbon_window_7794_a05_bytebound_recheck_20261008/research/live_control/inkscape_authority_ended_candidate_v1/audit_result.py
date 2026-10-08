import json
from pathlib import Path
R=Path(__file__).resolve().parent
r=json.loads((R/'result.json').read_text())
assert r['schema']=='inkscape-authority-ended-candidate-v1-result'
assert r['base_commit']=='7f42fd577dff98d6a27a8eceb79d86bee0358bf9'
assert r['hard_gate_pass'] is True
assert r['decision']=='PASS_OFFLINE_RECEIPT_MECHANISM'
assert len(r['rows'])==9 and all(x['pass'] is True for x in r['rows'])
assert r['max_snapshot_calls_any_case']==1
rows={x['case']:x for x in r['rows']}
clean=rows['clean_receipt_accepted']['detail']
assert clean['bridge']=={'accepted':True,'decision':{'status':'safe_yield','reason':'authority_unavailable','completed_actions':0}}
assert clean['receipt']['terminal_status']=='authority_ended'
assert clean['receipt']['authority_end_reason']=='expired'
assert clean['receipt']['post_authority']['captures']==1
assert clean['receipt']['post_authority']['sequence']==6
assert clean['receipt']['post_authority']['sequence_advanced'] is True
assert clean['receipt']['post_authority']['within_lifecycle_deadline'] is True
assert rows['late_snapshot_rejected']['detail']['bridge']['error']=='post-authority observation outside lifecycle deadline'
assert rows['snapshot_exception_rejected']['detail']['bridge']['error']=='exactly one passive post-authority capture required'
assert rows['nonadvancing_sequence_rejected']['detail']['bridge']['error']=='post-authority observation must advance sequence'
for key in ('post_release_admission_rejected_before_snapshot','unverified_release_rejected_before_snapshot','dirty_release_rejected_before_snapshot','nonpositive_budget_rejected_before_snapshot'):
    assert rows[key]['detail']['snapshot_calls']==0
assert rows['two_capture_mutation_rejected']['detail']['bridge']['error']=='exactly one passive post-authority capture required'
assert r['bridge_sha256']=='2c9684d8f731b36469df06532fc2ce566716c0380002d18da1f317814f7acb1e'
print('PASS independent offline authority-ended candidate audit')
