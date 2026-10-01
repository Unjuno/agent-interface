"""Independent raw-only audit of evaluator isolation v2. Standard library only."""
import hashlib
import json
from pathlib import Path

E = Path('/evidence')
SRC = Path('/src')
FREEZE = SRC / 'research/procedural_control_arena_v0/evaluator_isolation_v2/FREEZE.json'
errors = []
leaks = []

def read_json(path, label=None):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception as exc:
        errors.append(f'{label or path.name}: {type(exc).__name__}: {exc}')
        return None

freeze = read_json(FREEZE, 'FREEZE.json')
state = read_json(E / 'RUN_STATE.json')
manifest = read_json(E / 'RAW_MANIFEST.json')
if manifest:
    for rel, digest in manifest.get('files', {}).items():
        path = E / rel
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            errors.append(f'raw manifest mismatch: {rel}')
for rel in ('report.json', 'controller-probe.json', 'controller-inspect.json', 'evaluator-inspect-before.json',
            'evaluator-inspect-after.json', 'evaluator-proc-1-cmdline.txt', 'network-inspect.json',
            'evaluator-result/report.json', 'screen.xwd', 'evaluator.stderr.log'):
    if not (E / rel).is_file():
        errors.append(f'required artifact missing: {rel}')

report = read_json(E / 'report.json')
probe = read_json(E / 'controller-probe.json')
controller_docs = read_json(E / 'controller-inspect.json')
eval_docs = read_json(E / 'evaluator-inspect-before.json')
net_docs = read_json(E / 'network-inspect.json')
controller = controller_docs[0] if isinstance(controller_docs, list) and controller_docs else controller_docs
evaluator = eval_docs[0] if isinstance(eval_docs, list) and eval_docs else eval_docs
network = net_docs[0] if isinstance(net_docs, list) and net_docs else net_docs

if state and state.get('status') != 'CAPTURED':
    errors.append('runner state is not CAPTURED')
if freeze and state and hashlib.sha256(FREEZE.read_bytes()).hexdigest() != state.get('freeze_sha256'):
    errors.append('FREEZE hash differs from run state')
if freeze:
    if freeze.get('schema') != 'agent-interface-arena-isolation-v2-freeze-v1':
        errors.append('freeze schema mismatch')
    if freeze.get('trial', {}).get('seed') != 2003:
        errors.append('frozen trial seed is not 2003')
    for rel, item in freeze.get('source_hashes', {}).items():
        path = SRC / rel
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != item.get('sha256_worktree_bytes'):
            errors.append(f'frozen source hash mismatch: {rel}')
    if evaluator and evaluator.get('Image') != freeze.get('images', {}).get('evaluator', {}).get('id'):
        errors.append('evaluator image id mismatch')
    if controller and controller.get('Image') != freeze.get('images', {}).get('controller', {}).get('id'):
        errors.append('controller image id mismatch')

if report:
    episode = report.get('episode', {})
    stages = episode.get('stages', [])
    if episode.get('seed') != 2003:
        errors.append('report seed mismatch')
    if not stages or stages[0].get('kind') != 'target':
        errors.append('episode is not target-first')
    if report.get('success') is not False or report.get('failure_reason') != 'deadline_miss':
        errors.append('expected natural deadline_miss absent')
    for kind in ('key_down', 'key_up'):
        if not any(e.get('event') == kind and e.get('detail', {}).get('key') == 'w' for e in report.get('events', [])):
            errors.append(f'evaluator ledger lacks w {kind}')

if probe:
    if any(probe.get(k) != 0 for k in ('xdpyinfo_exit', 'capture_exit', 'key_exit')):
        errors.append('controller X11/capture/key command failed')
    if any('2003' in cmd for cmd in probe.get('proc_cmdlines', {}).values()):
        leaks.append('seed visible in controller process list')
    if any(probe.get('path_access', {}).values()):
        leaks.append('source or report path visible in controller')
    xwd = E / 'screen.xwd'
    if not xwd.is_file():
        errors.append('raw XWD missing')
    else:
        raw = xwd.read_bytes()
        header = int.from_bytes(raw[:4], 'big') if len(raw) >= 4 else 0
        if len(raw) != probe.get('capture_bytes') or hashlib.sha256(raw).hexdigest() != probe.get('capture_sha256'):
            errors.append('XWD differs from controller probe hash/length')
        if len(raw) < 1000 or not 100 <= header <= len(raw):
            errors.append('XWD header invalid')

if network and network.get('Internal') is not True:
    errors.append('network is not internal')
if controller:
    config = controller.get('Config', {})
    host = controller.get('HostConfig', {})
    if config.get('User') != '10000:10000': errors.append('controller uid/gid mismatch')
    if host.get('ReadonlyRootfs') is not True: errors.append('controller root is writable')
    if host.get('CapDrop') != ['ALL']: errors.append('controller caps not fully dropped')
    if host.get('Privileged') is not False: errors.append('controller privileged')
    if host.get('PidMode') not in ('', None): errors.append('controller shares PID namespace')
    if host.get('NetworkMode') != 'arena-isolation-v2-formal-002': errors.append('controller network mismatch')
    if controller.get('Mounts') != []: errors.append('controller has a mount')
    if set(host.get('Tmpfs', {})) != {'/tmp'}: errors.append('controller writable tmpfs mismatch')
    if 'no-new-privileges' not in host.get('SecurityOpt', []): errors.append('controller no-new-privileges missing')
    if any('2003' in env for env in config.get('Env', [])): leaks.append('seed visible in controller environment')
    if any('docker.sock' in (m.get('Source', '') + m.get('Destination', '')) for m in controller.get('Mounts', [])):
        leaks.append('Docker socket mounted in controller')
if evaluator:
    ehost = evaluator.get('HostConfig', {})
    mounts = evaluator.get('Mounts', [])
    if ehost.get('ReadonlyRootfs') is not True: errors.append('evaluator root is writable')
    if ehost.get('CapDrop') != ['ALL']: errors.append('evaluator caps not fully dropped')
    if ehost.get('PidMode') not in ('', None): errors.append('evaluator shares PID namespace')
    if ehost.get('NetworkMode') != 'arena-isolation-v2-formal-002': errors.append('evaluator network mismatch')
    if len(mounts) != 1 or mounts[0].get('Type') != 'bind' or mounts[0].get('Destination') != '/evidence' or mounts[0].get('RW') is not True:
        errors.append('evaluator host evidence bind differs from preregistration')
    elif str(mounts[0].get('Source', '')).replace('\\', '/').rstrip('/').split('/')[-1] != 'evaluator-result':
        errors.append('evaluator evidence bind target directory mismatch')
    if set(ehost.get('Tmpfs', {})) != {'/tmp'}: errors.append('evaluator tmpfs mismatch')
    env = evaluator.get('Config', {}).get('Env', [])
    if not any(x == 'ARENA_AUTOCLOSE=30' for x in env): errors.append('evaluator auto-close window differs')
    argv = (E / 'evaluator-proc-1-cmdline.txt').read_text(encoding='utf-8') if (E / 'evaluator-proc-1-cmdline.txt').is_file() else ''
    if '--seed 2003' not in argv: errors.append('evaluator PID 1 argv lacks frozen seed')
    if not (E / 'evaluator.stderr.log').is_file() or 'evaluator_seed_argv=2003' not in (E / 'evaluator.stderr.log').read_text(encoding='utf-8'):
        errors.append('evaluator startup seed record missing')
    ev_cookie = next((item.partition('=')[2] for item in env if item.startswith('X11_COOKIE_SHA256=')), None)
    ctl_env = controller.get('Config', {}).get('Env', []) if controller else []
    ctl_cookie = next((item.partition('=')[2] for item in ctl_env if item.startswith('X11_COOKIE_SHA256=')), None)
    if not ev_cookie or ev_cookie != ctl_cookie:
        errors.append('redacted X11 cookie digest does not match across the two containers')
    if any(item.startswith('X11_COOKIE=') for item in env + ctl_env):
        errors.append('unredacted X11 cookie persisted in inspect evidence')

if leaks:
    disposition = 'FAIL_BOUNDARY_LEAK'
elif errors:
    disposition = 'STOP_AUDIT_OR_PROVENANCE_INCOMPLETE'
else:
    disposition = 'PASS_EVALUATOR_PROCESS_AND_SOURCE_ISOLATION_SCOPED'
result = {'schema': 'arena-isolation-v2-independent-audit-v1', 'disposition': disposition,
          'error_count': len(errors), 'leak_count': len(leaks), 'errors': errors, 'leaks': leaks,
          'scope': 'single seed-2003 inert-input isolation canary; not B0/C1 performance or hostile-X11 security evidence'}
print(json.dumps(result, sort_keys=True))
raise SystemExit(0 if disposition == 'PASS_EVALUATOR_PROCESS_AND_SOURCE_ISOLATION_SCOPED' else 2)
