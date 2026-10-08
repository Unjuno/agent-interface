from __future__ import annotations
import hashlib,json,sys
from pathlib import Path

root=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
plan=json.loads((root/'preregistration.json').read_text())
result=json.loads((root/'result.json').read_text())
cases=json.loads((root/'cases.json').read_text())
audits=json.loads((root/'terminal-audits.json').read_text())
assert result['task_id']==plan['task_id']=='container-map01-two-phase-observation-transfer-20260915-v1'
assert result['passed'] is True and result['paired_reduction_ms']['median'] >= 5
assert result['hard_gates']=={
    'candidate_release_before_artifact_all': True,
    'candidate_split_once_all': True,
    'controller_scorer_leaks_total': 0,
    'scorer_missed_periods_total': 0,
    'terminal_score_agreement': 'PASS_6_OF_6',
    'verified_empty_release': 'PASS_6_OF_6'}
assert len(cases)==6 and all(x['terminal_status']=='completed' and x['release_verified'] for x in cases)
assert all(a['pass'] is True for a in audits.values()) and len(audits)==6
for name,expected in plan['sources'].items():
    assert sha(root/name)==expected,(name,sha(root/name),expected)
print('PASS compact real MAP01 two-phase observation transfer audit')
