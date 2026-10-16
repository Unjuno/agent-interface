from __future__ import annotations
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
r=json.loads((HERE/'result.json').read_text())
assert r['schema']=='inkscape-authority-durable-token-compat-v1-result'
assert r['upstream_authority_abi_head']=='d1c7d0531993b23a61c7f38e12d979c27948cf6e'
assert r['hard_gate_pass'] is True
assert r['decision']=='RETAIN_COMPOSITION_GAP'
rows={x['case']:x for x in r['rows']}
assert len(rows)==5 and all(x['pass'] is True for x in rows.values())
assert rows['current_v2_ledger_rejects_truthful_two_capture_receipt']['detail']=={'type':'AuthorityEndedNotReady','error':'exactly one passive post-authority capture required'}
assert rows['bridge_v2_exposes_missing_runtime_authority_end_id']['detail']=={'type':'StateError','error':'runtime authority_end_id required'}
assert rows['diagnostic_id_allows_single_issue']['detail']['post_sequence']==11
assert rows['diagnostic_duplicate_rejected']['detail']=={'type':'DuplicateReceipt','error':'authority_end_id already exists'}
assert rows['diagnostic_pending_recovers_after_restart']['detail']['status']=='pending'
assert r['executed_source_sha256']['durable_token_state_v2.py']=='72a3481653cf9c41ec1a03f4c7a7bf1c482ff69468b5d92986bad8cf814950b4'
assert r['executed_source_sha256']['authority_ended_bridge_v1.py']=='2c9684d8f731b36469df06532fc2ce566716c0380002d18da1f317814f7acb1e'
assert r['executed_source_sha256']['current_pr168_authority_ended_bridge_v2.py']=='37e544086fe70087c0a2e6c03ce8c42c1c5dd71989f7fe541eb9055b3551eb52'
assert r['current_pr168_bridge_v2_git_blob']=='63639f44eba47a2842e57e3761730e6f6224e815'
print('PASS ABI-v2 durable-token composition-gap retained-result audit')
