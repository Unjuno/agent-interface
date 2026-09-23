from __future__ import annotations
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
r = json.loads((HERE / 'result.json').read_text(encoding='utf-8'))
assert r['schema'] == 'inkscape-expired-authority-semantics-v1-result'
assert r['base_commit'] == '0bf4103e69e4108f92a153e38a5ea1f7253f1f93'
assert r['hard_gate_pass'] is True
assert r['decision'] == 'FAIL_DIRECT_UPGRADE_RETAIN_SEMANTIC_MISMATCH'
p = r['provenance']
assert p['terminal_status']['status'] == 'CONTRADICTORY'
assert p['terminal_status']['value'] == 'expired'
assert p['post_authority.captures']['status'] == 'CONTRADICTORY'
assert p['post_authority.captures']['value'] == 2
assert p['post_authority.sequence']['status'] == 'AMBIGUOUS'
assert p['post_authority.sequence']['value'] == [7, 8]
for key in ('post_authority.within_lifecycle_deadline', 'post_authority.snapshot_finished_ns', 'post_authority.lifecycle_deadline_ns'):
    assert p[key]['status'] == 'UNAVAILABLE'
assert r['timing']['release_minus_old_deadline_ns'] == 1_344_937
assert r['timing']['first_capture_minus_old_deadline_ns'] == 95_018_835
assert r['unchanged_bridge_first_result'] == {'accepted': False, 'error': 'scheduled authority_ended status required'}
assert r['diagnostic_counterfactual_relabel_only'] == {'accepted': False, 'error': 'exactly one passive post-authority capture required'}
assert r['diagnostic_counterfactual_relabel_and_single_capture'] == {'accepted': False, 'error': 'post-authority observation outside lifecycle deadline'}
assert r['source_identities']['source_git_blob_sha1'] == 'aae6d81013e479d2ad1f2f068ccc4c8ad5c8c653'
assert r['source_identities']['bridge_sha256'] == '2c9684d8f731b36469df06532fc2ce566716c0380002d18da1f317814f7acb1e'
print('PASS retained Inkscape expired/authority semantic-mismatch audit')
