from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
plan=json.loads((ROOT/'preregistration.json').read_text())
result=json.loads((ROOT/'result.json').read_text())
audits=json.loads((ROOT/'terminal-audits.json').read_text())
assert plan['task_id']==result['task_id']=='container-map01-owner-v-two-phase-20260915-v1'
assert result['decision']=='OWNER_PARETO_TIMING_CANDIDATE_REQUIRES_SEMANTIC_REPAIR'
assert result['owner']['empty_median_ms'] <= result['two_phase']['empty_median_ms'] + 2
assert result['owner']['artifact_median_ms'] <= result['two_phase']['artifact_median_ms']
h=result['hard_gates']
assert h['release_verified_6_of_6'] and h['terminal_score_audit_6_of_6']
assert h['scorer_missed_periods_total']==0 and h['controller_scorer_leaks_total']==0
assert h['owner_expired_3_of_3'] and h['two_phase_completed_3_of_3']
assert len(audits)==6 and all(v['pass'] is True for v in audits.values())
assert sha(ROOT/'compare_owner_two_phase_case.py')=='f4ea0106e965ced73db9981922729ae360b73f1285c133604f24c4552cd61354'
print('PASS owner-v-two-phase compact audit')
