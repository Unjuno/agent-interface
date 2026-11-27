import hashlib, json, math
from pathlib import Path
root = Path(__file__).resolve().parent
raw = json.loads((root / 'raw' / 'r02.json').read_text(encoding='utf-8'))
conditions = json.loads((root / 'conditions-r02.json').read_text(encoding='utf-8'))
fail = []
sha = hashlib.sha256((root / 'conditions-r02.json').read_bytes()).hexdigest()
if raw.get('conditions_sha256') != sha: fail.append('conditions SHA256 mismatch')
if raw.get('audit', {}).get('status') != 'PASS': fail.append('runner audit is not PASS')
rows = raw.get('trials', [])
if len(rows) != 6: fail.append('expected six trial rows')
for arm, settings in conditions['arms'].items():
    selected = [row for row in rows if row.get('arm') == arm]
    if len(selected) != settings['trials']: fail.append(f'{arm}: unexpected trial count')
for row in rows:
    tid = row.get('trial_id', '<missing>')
    cancel = row.get('cancel') or {}
    disconnect = cancel.get('owner_client_disconnect') or {}
    release = cancel.get('owner_release_attempt') or {}
    terminal = row.get('terminal_call') or {}
    helpers = row.get('helper_start_receipts') or []
    if row.get('status') == 'incomplete': fail.append(f'{tid}: incomplete')
    if len(helpers) != 1 or not helpers or helpers[0].get('pid') is None:
        fail.append(f'{tid}: expected one started helper with PID')
    if helpers and helpers[0].get('worker_retired') is False:
        fail.append(f'{tid}: helper not retired')
    if disconnect.get('status') != 'unknown' or disconnect.get('reason') != 'supervision_timeout':
        fail.append(f'{tid}: disconnect did not remain UNKNOWN at supervisor timeout')
    if disconnect.get('worker_retired') is not True or disconnect.get('worker_exitcode') is None:
        fail.append(f'{tid}: timed-out helper retirement receipt is incomplete')
    if release.get('status') != 'not_attempted': fail.append(f'{tid}: release gate opened')
    if cancel.get('release_confirmed') is not False: fail.append(f'{tid}: false release claim')
    if cancel.get('cleanup_status') != 'UNKNOWN': fail.append(f'{tid}: cleanup not UNKNOWN')
    if cancel.get('task_success') is not None: fail.append(f'{tid}: task success is not null')
    if cancel.get('replay_allowed') is not False: fail.append(f'{tid}: replay not denied')
    if terminal.get('status') != 'runtime_failed': fail.append(f'{tid}: wrong terminal status')
    if not isinstance(row.get('cancel_tool_elapsed_ms'), (int, float)): fail.append(f'{tid}: missing cancel duration')
    if not isinstance(row.get('max_event_loop_gap_ms'), (int, float)): fail.append(f'{tid}: missing heartbeat gap')
base = [r for r in rows if r.get('arm') == 'actual-spawn-no-delay']
delayed = [r for r in rows if r.get('arm') == 'actual-spawn-with-delay']
if base and delayed:
    if min(r['cancel_tool_elapsed_ms'] for r in delayed) <= max(r['cancel_tool_elapsed_ms'] for r in base): fail.append('delayed cancel latency does not separate')
    if min(r['max_event_loop_gap_ms'] for r in delayed) <= max(r['max_event_loop_gap_ms'] for r in base): fail.append('delayed heartbeat gap does not separate')
r01 = json.loads((root / 'raw' / 'r01.json').read_text(encoding='utf-8'))
r01_conditions = hashlib.sha256((root / 'raw' / 'r01-conditions.json').read_bytes()).hexdigest()
if r01.get('conditions_sha256') != r01_conditions: fail.append('preserved r01 conditions snapshot does not match its recorded digest')
result = {'status': 'PASS' if not fail else 'FAIL', 'independent_checks': 7, 'failures': fail,
          'scope': 'descriptive Windows spawn/caller timing and conservative release gate only'}
print(json.dumps(result, indent=2))
raise SystemExit(0 if not fail else 1)
