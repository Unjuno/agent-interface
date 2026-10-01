from __future__ import annotations
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
R=json.loads((H/'formal-result.json').read_text())
EXPECTED_RESULT_SHA='8734b094b5755142c9532b008add84c382026d61fb189d956e928926430e18e7'
expected_cases=[
 'current_bridge_identity_recomputed',
 'current_normalizer_identity_recomputed',
 'manifest_formal_claims_mismatch_current_sources',
 'build_gate_reuses_stale_manifest_claims',
 'bridge_absent_at_formal_evidence_commit',
 'normalizer_absent_at_formal_evidence_commit',
 'formal_evidence_precedes_both_source_add_commits',
 'reconciled_main_retains_postformal_source_blobs',
]
errors=[]
if hashlib.sha256((H/'formal-result.json').read_bytes()).hexdigest()!=EXPECTED_RESULT_SHA: errors.append('formal_result_hash')
if R.get('schema')!='inkscape-abi-v2-provenance-reaudit-v1-formal-result': errors.append('schema')
if R.get('result_id')!='inkscape-abi-v2-provenance-reaudit-v1-20260916-01': errors.append('result_id')
if R.get('base_commit')!='227ba648f1c0b83e9a5b69f4e0c7d39839d3578f': errors.append('base_commit')
if R.get('formal_retries')!=0: errors.append('formal_retries')
if R.get('hard_gate_pass') is not True: errors.append('hard_gate')
if R.get('decision')!='INVALIDATE_ABI_V2_FORMAL_SOURCE_PROVENANCE_REQUIRE_RERUN': errors.append('decision')
rows=R.get('rows',[])
if [x.get('case') for x in rows]!=expected_cases: errors.append('case_order')
if len(rows)!=8 or not all(x.get('pass') is True for x in rows): errors.append('row_passes')
by={x['case']:x for x in rows if 'case' in x}
try:
 if by[expected_cases[0]]['detail']['sha256']!='37e544086fe70087c0a2e6c03ce8c42c1c5dd71989f7fe541eb9055b3551eb52': errors.append('bridge_sha')
 if by[expected_cases[0]]['detail']['git_blob']!='63639f44eba47a2842e57e3761730e6f6224e815': errors.append('bridge_blob')
 if by[expected_cases[1]]['detail']['sha256']!='dc664652c7c29b002005feb7b69122d29619a449c6ad781a65ac5abfaa186d41': errors.append('normalizer_sha')
 if by[expected_cases[1]]['detail']['git_blob']!='a6eb2b8a8964b34ac22dd4f1cbeaaff879f7e5b1': errors.append('normalizer_blob')
 if by[expected_cases[4]]['detail']['observation']!='404_not_found' or by[expected_cases[5]]['detail']['observation']!='404_not_found': errors.append('formal_path_absence')
 chain=by[expected_cases[6]]['detail']['chain']
 if chain[1]['parent']!=chain[0]['sha'] or chain[2]['parent']!=chain[1]['sha']: errors.append('commit_chain')
except Exception as e: errors.append('detail_shape:'+type(e).__name__)
for name in ['audit_input.json','formal_runner.py']:
 actual=hashlib.sha256((H/name).read_bytes()).hexdigest()
 if R.get('source_sha256',{}).get(name)!=actual: errors.append(name+':source_hash')
out={'schema':'inkscape-abi-v2-provenance-reaudit-v1-audit','pass':not errors,'errors':errors,'formal_result_sha256':hashlib.sha256((H/'formal-result.json').read_bytes()).hexdigest()}
print(json.dumps(out,indent=2,sort_keys=True))
raise SystemExit(0 if not errors else 2)
