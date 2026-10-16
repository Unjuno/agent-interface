from __future__ import annotations
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
r=json.loads((H/'formal-result.json').read_text())
f=json.loads((H/'retained_terminal_fixture.json').read_text())
assert r['schema']=='authority-end-identity-binding-v1-formal-result'
assert r['result_id']=='authority-end-identity-binding-v1-20260916-01'
assert r['formal_retries']==0 and r['hard_gate_pass'] is True and r['decision']=='RETAIN_INTENT_TOKEN_BINDING'
rows={x['case']:x for x in r['rows']}
assert len(rows)==13 and all(x['pass'] is True for x in rows.values())
term=f['terminal'];rid=term['interruption']['intent_token']
assert rid=='c516e6cfcf8041e0b1f68cdadd1dc265'
assert term['release']['intent_token']==rid
assert f['input_events'][0]['intent_token']==rid
assert f['input_stopped_emit_ns'] < f['first_post_authority_capture_ns']
assert rows['valid_two_capture_binds_existing_intent_token']['detail']['id']==rid
assert rows['durable_issue_preserves_exact_runtime_id']['detail']['id']==rid
assert rows['restart_recovers_pending_same_id']['detail']['id']==rid
assert rows['duplicate_same_receipt_rejected']['detail']['error']=='authority_end_id already exists'
assert rows['same_epoch_altered_post_sequence_rejected']['detail']['error']=='authority_end_id already exists'
assert rows['missing_intent_token_rejected']['detail']['error']=='runtime interruption intent_token required'
assert rows['mismatched_caller_id_rejected']['detail']['error']=='caller authority_end_id mismatch'
assert rows['legacy_expired_not_promoted']['detail']['error']=='authority_ended terminal required'
assert rows['unverified_interruption_rejected']['detail']['error']=='verified empty expiry interruption required'
assert rows['non_expiry_interruption_rejected']['detail']['error']=='verified expiry interruption required'
assert rows['release_token_mismatch_rejected']['detail']['error']=='release/interruption intent_token mismatch'
for n,h in r['source_sha256'].items(): assert hashlib.sha256((H/n).read_bytes()).hexdigest()==h,(n,h)
print('PASS independent authority-end identity binding audit')
