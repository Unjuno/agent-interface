"""Read-only audit of a retained STOP allocation; never upgrades it to PASS."""
import hashlib
import json
from pathlib import Path

E = Path('/evidence')
freeze = json.loads(Path('/freeze/FREEZE.json').read_text(encoding='utf-8'))
state = json.loads((E / 'RUN_STATE.json').read_text(encoding='utf-8'))
probe = json.loads((E / 'controller-probe.json').read_text(encoding='utf-8'))
controller = json.loads((E / 'controller-inspect.json').read_text(encoding='utf-8'))[0]
evaluator = json.loads((E / 'evaluator-inspect-before.json').read_text(encoding='utf-8'))[0]
network = json.loads((E / 'network-inspect.json').read_text(encoding='utf-8'))[0]
argv = (E / 'evaluator-proc-1-cmdline.txt').read_text(encoding='utf-8')
errors = []

freeze_hash = hashlib.sha256(Path('/freeze/FREEZE.json').read_bytes()).hexdigest()
if state.get('freeze_sha256') != freeze_hash: errors.append('run state/FREEZE hash mismatch')
capture = E / 'screen.xwd'
if not capture.is_file(): errors.append('raw screenshot absent')
else:
    raw = capture.read_bytes()
    if len(raw) != probe.get('capture_bytes') or hashlib.sha256(raw).hexdigest() != probe.get('capture_sha256'):
        errors.append('raw screenshot differs from controller probe')
if probe.get('key_exit') != 0: errors.append('controller key command failed')
if any('2001' in cmd for cmd in probe.get('proc_cmdlines', {}).values()): errors.append('seed leaked into controller process list')
if any(probe.get('path_access', {}).values()): errors.append('controller could access source/report path')
if '--seed 2001' not in argv: errors.append('captured evaluator argv missing seed')
if controller.get('Image') != freeze['images']['controller']['id']: errors.append('controller image id mismatch')
if evaluator.get('Image') != freeze['images']['evaluator']['id']: errors.append('evaluator image id mismatch')
if network.get('Internal') is not True: errors.append('network not internal')
host = controller.get('HostConfig', {})
if controller.get('Config', {}).get('User') != '10000:10000': errors.append('controller user mismatch')
if host.get('ReadonlyRootfs') is not True or host.get('CapDrop') != ['ALL'] or host.get('Privileged') is not False:
    errors.append('controller hardening config mismatch')
if controller.get('Mounts') != [] or host.get('PidMode') not in ('', None): errors.append('controller mount/PID isolation mismatch')
if host.get('NetworkMode') != network.get('Name'): errors.append('controller network does not match inspection')
if (E / 'report.json').exists(): errors.append('unexpected evaluator report exists; STOP record needs review')
if (E / 'evaluator-inspect-after.json').exists(): errors.append('unexpected post-run evaluator inspect exists; STOP record needs review')
result = {
    'schema': 'arena-isolation-posthoc-stop-audit-v1',
    'disposition': 'STOP_EVALUATOR_REPORT_UNAVAILABLE' if not errors else 'STOP_PARTIAL_EVIDENCE_AUDIT_ERRORS',
    'errors': errors,
    'checks': {'freeze_hash_matches_run_state': state.get('freeze_sha256') == freeze_hash,
               'capture_bytes': capture.stat().st_size if capture.exists() else None,
               'capture_sha256': hashlib.sha256(capture.read_bytes()).hexdigest() if capture.exists() else None,
               'key_command_exit': probe.get('key_exit'), 'controller_pid_view': probe.get('proc_cmdlines'),
               'controller_path_access': probe.get('path_access'), 'report_available': (E / 'report.json').is_file(),
               'evaluator_pid1_cmdline': argv.strip(), 'network_internal': network.get('Internal')},
    'interpretation': 'The controller capture and isolation metadata are internally consistent, but without the evaluator report the injected key ledger and natural failure outcome are unverified. This formal allocation remains STOP; no retry or PASS upgrade.',
    'prior_independent_auditor_error': 'frozen audit.py raised AttributeError while treating docker inspect JSON array as an object',
}
print(json.dumps(result, sort_keys=True))
raise SystemExit(0 if not errors else 2)
