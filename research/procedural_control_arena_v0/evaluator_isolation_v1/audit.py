"""Independent raw-artifact-only audit. No runner/probe imports."""
import hashlib
import json
from pathlib import Path

E = Path('/evidence')
SRC = Path('/src')
errors = []
leaks = []

def read_json(name):
    try:
        return json.loads((E / name).read_text(encoding='utf-8'))
    except Exception as exc:
        errors.append(f'{name}: {type(exc).__name__}: {exc}')
        return None

freeze_path = SRC / 'research/procedural_control_arena_v0/evaluator_isolation_v1/FREEZE.json'
try:
    freeze = json.loads(freeze_path.read_text(encoding='utf-8'))
except Exception as exc:
    freeze = None
    errors.append(f'FREEZE.json: {type(exc).__name__}: {exc}')

manifest = read_json('RAW_MANIFEST.json')
if manifest:
    for name, digest in manifest.get('files', {}).items():
        path = E / name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            errors.append(f'raw manifest mismatch: {name}')
for name in ('report.json', 'controller-probe.json', 'network-inspect.json', 'controller-inspect.json',
             'evaluator-inspect-before.json', 'evaluator-inspect-after.json', 'evaluator-proc-1-cmdline.txt'):
    if not (E / name).is_file():
        errors.append(f'required raw file missing: {name}')

report = read_json('report.json')
probe = read_json('controller-probe.json')
network = read_json('network-inspect.json')
controller = read_json('controller-inspect.json')
evaluator = read_json('evaluator-inspect-before.json')
state = read_json('RUN_STATE.json')

if freeze:
    if freeze.get('schema') != 'agent-interface-arena-isolation-freeze-v1':
        errors.append('unexpected freeze schema')
    if freeze.get('trial', {}).get('seed') != 2001:
        errors.append('freeze trial seed is not 2001')
    for rel, item in freeze.get('source_hashes', {}).items():
        path = SRC / rel
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != item.get('sha256_worktree_bytes'):
            errors.append(f'frozen source hash mismatch: {rel}')
    if evaluator and evaluator.get('Image') != freeze.get('images', {}).get('evaluator', {}).get('id'):
        errors.append('evaluator image differs from frozen image id')
    if controller and controller.get('Image') != freeze.get('images', {}).get('controller', {}).get('id'):
        errors.append('controller image differs from frozen image id')
if state and state.get('status') != 'CAPTURED':
    errors.append('formal run state is not CAPTURED')
if freeze and state and hashlib.sha256(freeze_path.read_bytes()).hexdigest() != state.get('freeze_sha256'):
    errors.append('FREEZE.json hash differs from run state')
if report:
    episode = report.get('episode', {})
    stages = episode.get('stages', [])
    if episode.get('seed') != 2001:
        errors.append('report seed differs from frozen seed 2001')
    if not stages or stages[0].get('kind') != 'target':
        errors.append('report is not target-first')
    if report.get('success') is not False or report.get('failure_reason') != 'deadline_miss':
        errors.append('expected natural deadline_miss absent')
    if not any(e.get('event') == 'key_down' and e.get('detail', {}).get('key') == 'w' for e in report.get('events', [])):
        errors.append('evaluator ledger lacks injected w key-down')
    if not any(e.get('event') == 'key_up' and e.get('detail', {}).get('key') == 'w' for e in report.get('events', [])):
        errors.append('evaluator ledger lacks injected w key-up')
if probe:
    if any(probe.get(k) != 0 for k in ('xdpyinfo_exit', 'capture_exit', 'key_exit')):
        errors.append('X11/capture/key probe returned nonzero')
    xwd = E / 'screen.xwd'
    if not xwd.is_file():
        errors.append('raw XWD missing')
    else:
        data = xwd.read_bytes()
        size = int.from_bytes(data[:4], 'big') if len(data) >= 4 else 0
        if len(data) != probe.get('capture_bytes') or hashlib.sha256(data).hexdigest() != probe.get('capture_sha256'):
            errors.append('raw XWD does not match probe size/hash')
        if len(data) < 1000 or not 100 <= size <= len(data):
            errors.append('XWD header/size invalid')
    if any('2001' in cmd for cmd in probe.get('proc_cmdlines', {}).values()):
        leaks.append('seed 2001 visible in controller process list')
    if any(probe.get('path_access', {}).values()):
        leaks.append('source/report path visible inside controller')
if not network or network[0].get('Internal') is not True:
    errors.append('Docker network is not internal')
if controller:
    config, host = controller.get('Config', {}), controller.get('HostConfig', {})
    if config.get('User') != '10000:10000': errors.append('controller user differs')
    if host.get('ReadonlyRootfs') is not True: errors.append('controller root is writable')
    if host.get('CapDrop') != ['ALL']: errors.append('controller capabilities not fully dropped')
    if host.get('Privileged') is not False: errors.append('controller is privileged')
    if host.get('PidMode') not in ('', None): errors.append('controller shares PID namespace')
    if host.get('NetworkMode') != 'arena-isolation-formal-001': errors.append('controller network differs from allocated internal network')
    if controller.get('Mounts') != []: errors.append('controller has unexpected mount')
    if set(host.get('Tmpfs', {})) != {'/tmp'}: errors.append('controller tmpfs mount differs')
    if 'no-new-privileges' not in host.get('SecurityOpt', []): errors.append('no-new-privileges missing')
    if any('2001' in env for env in config.get('Env', [])): leaks.append('seed 2001 in controller environment')
    if any('docker.sock' in (m.get('Source', '') + m.get('Destination', '')) for m in controller.get('Mounts', [])):
        leaks.append('Docker socket mounted into controller')
if evaluator:
    argv_path = E / 'evaluator-proc-1-cmdline.txt'
    argv = argv_path.read_text(encoding='utf-8') if argv_path.is_file() else ''
    if '--seed 2001' not in argv: errors.append('evaluator PID 1 argv lacks seed 2001')
    if evaluator.get('HostConfig', {}).get('PidMode') not in ('', None): errors.append('evaluator PID namespace shared')
    if evaluator.get('HostConfig', {}).get('NetworkMode') != 'arena-isolation-formal-001': errors.append('evaluator network differs from allocated internal network')
    if evaluator.get('Mounts', []) != []:
        errors.append('evaluator has unexpected bind/volume mount')
    if set(evaluator.get('HostConfig', {}).get('Tmpfs', {})) != {'/evidence', '/tmp'}:
        errors.append('evaluator private tmpfs mounts incomplete')
    if not (E / 'evaluator.stderr.log').is_file() or 'evaluator_seed_argv=2001' not in (E / 'evaluator.stderr.log').read_text(encoding='utf-8'):
        errors.append('evaluator startup log does not record seed argv')

if leaks:
    disposition = 'FAIL_BOUNDARY_LEAK'
elif errors:
    disposition = 'STOP_AUDIT_OR_PROVENANCE_INCOMPLETE'
else:
    disposition = 'PASS_EVALUATOR_PROCESS_AND_SOURCE_ISOLATION_SCOPED'
result = {'schema': 'arena-isolation-independent-audit-v1', 'disposition': disposition,
          'checks_error_count': len(errors), 'leak_count': len(leaks), 'errors': errors, 'leaks': leaks,
          'scope': 'single seed-2001 inert-input isolation canary; not B0/C1 performance or hostile-X11 security evidence'}
print(json.dumps(result, sort_keys=True))
raise SystemExit(0 if disposition == 'PASS_EVALUATOR_PROCESS_AND_SOURCE_ISOLATION_SCOPED' else 2)
