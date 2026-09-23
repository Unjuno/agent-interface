from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parent
r=json.loads((ROOT/'result.json').read_text())
assert r['schema']=='authority-ended-durable-submit-composition-v1-result'
assert r['base_commit']=='d21482d1a3cc16b54447d14d0a2d93aa70409162'
assert r['hard_gate_pass'] is True
assert r['decision']=='RETAIN_COMPOSITION_BOUNDARY_HOLD_ATOMIC_EXACTLY_ONCE'
rows={x['case']:x for x in r['rows']}
assert len(rows)==6 and all(x['pass'] is True for x in rows.values())
assert rows['pending_token_without_submit_is_recoverable_precondition']['detail']['classification']=='TOKEN_PENDING_NO_SUBMIT'
b=rows['consume_before_submit_crash_leaves_no_submit_identity']['detail']
assert b['classification']=='CONSUMED_WITHOUT_SUBMIT_RECORD' and b['process']['returncode']==81 and b['token_recovery']=='authority_end_id already consumed'
c=rows['transport_crash_after_submit_persist_is_explicit_unknown']['detail']
assert c['classification']=='PENDING_OR_UNKNOWN_DELIVERY' and c['write_state']=='may_have_been_sent' and c['process']['returncode']==82
d=rows['restart_refuses_blind_new_command_before_transport']['detail']['result']
assert d=={'error':'unresolved command; read only','transport_reached':False}
rdo=rows['read_only_timeout_preserves_pending_identity_without_command']['detail']
assert rdo['request_id_before']==rdo['request_id_after'] and 'command' not in rdo['request']
e=rows['submit_before_consume_reaches_transport_with_token_still_pending']['detail']
assert e['classification']=='SUBMIT_PENDING_BEFORE_TOKEN_CONSUME' and e['process']['returncode']==83
assert e['transport_marker']=={'request_has_command':True,'token_status_at_transport':'pending'}
expected={
 'authority_ended_restart_durability_v1/durable_token_state_v2.py':'e48f4e2c1949ffd494a7e4e61510e9d3148aa646',
 'authority_ended_restart_durability_v1/authority_ended_bridge_v1.py':'9fcfdce5229cb58b3d1a17aacbcef0cb44bd10f1',
 'durable_submit_v1.py':'aaee9d460bcf114dbe1603056c79e6ecc65403e2',
 'received_continuation_v1.py':'b27d922799cfcfc66ad092c8edb8b7134e1889e5',
 'unix_json_deadline.py':'267b5ccce24ca43b8a6e9b36219d50342888aa27',
 'authority_ended_receipt_ledger_v1/receipt-fixture.json':'4070fd206c859357125a2cb327affa5aec6de8b8',
}
assert {k:v['git_blob_sha1'] for k,v in r['source_identities'].items()}==expected
print('PASS retained durable-token/durable-submit composition audit')
