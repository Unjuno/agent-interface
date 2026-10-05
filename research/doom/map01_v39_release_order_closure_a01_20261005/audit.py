"""Independent consistency audit for the retained inert V39 release trace."""
import hashlib, json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
freeze=json.loads((HERE/'FREEZE.json').read_text())
trace=json.loads((HERE/'TRACE.json').read_text())
assert freeze['schema']=='v39-release-order-closure-freeze-v1'
assert trace['schema']=='v39-selected-release-closure-trace-v1'
assert trace['source_commit']==freeze['source_commit']
for path, pins in freeze['source_files'].items():
    blob=subprocess.check_output(['git','rev-parse',f"{freeze['source_commit']}:{path}"],cwd=ROOT,text=True).strip()
    raw=subprocess.check_output(['git','show',f"{freeze['source_commit']}:{path}"],cwd=ROOT)
    assert blob==pins['git_blob'],(path,'git blob mismatch')
    assert hashlib.sha256(raw).hexdigest()==pins['sha256'],(path,'source hash mismatch')
events=trace['events']
assert all(type(e.get('time_ns')) is int for e in events)
ups=[e for e in events if e['event']=='key_up']
assert [e['keycode'] for e in ups]==[38,65],ups
queries=[e for e in events if e['event']=='query_keymap']
assert len(queries)==1,queries
samples=[e for e in events if e['event']=='input_state_sample_start']
finishes=[e for e in events if e['event']=='input_state_sample_finish']
assert len(samples)==len(finishes)==1
assert ups[0]['time_ns'] < ups[1]['time_ns'] < samples[0]['time_ns'] < finishes[0]['time_ns'] < queries[0]['time_ns']
assert not any(ups[0]['time_ns'] < e['time_ns'] < ups[1]['time_ns'] for e in queries)
rows=trace['release_rows']
assert [r['key'] for r in rows]==['a','space']
assert [r['release_batch_position'] for r in rows]==[0,1]
assert all(r['release_batch_size']==2 for r in rows)
assert all(r['owner_thread_keyup_verified'] is True for r in rows)
assert all(r['owner_transition_verified'] is True for r in rows)
assert all(r['owned_keycodes_after_batch']==[] for r in rows)
assert all(r['physical_verification_authoritative'] is False for r in rows)
assert all(r['owner_thread_keyup_receipt']['server_sync_completed'] is True for r in rows)
assert trace['live_game'] is False and trace['gui'] is False and trace['model_calls']==0
print('AUDIT_PASS: exact source pins, ordered two-key receipts, one post-batch owner sample, later cleanup keymap query, no authority')
