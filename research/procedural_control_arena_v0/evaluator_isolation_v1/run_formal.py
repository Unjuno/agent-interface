"""One-shot seed-2001 isolation allocation. Never retry formal/001."""
import base64
import hashlib
import json
import secrets
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
BASE = 'python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9'
OUT = HERE / 'formal/001'
NETWORK, EVAL, CTL = 'arena-isolation-formal-001', 'arena-isolation-formal-001-eval', 'arena-isolation-formal-001-controller'

def call(args, *, check=True, timeout=30):
    p = subprocess.run(args, cwd=REPO, capture_output=True, text=True, timeout=timeout)
    if check and p.returncode:
        raise RuntimeError(f"command failed ({p.returncode}): {args}\n{p.stdout}\n{p.stderr}")
    return p

if OUT.exists():
    raise SystemExit('STOP: formal/001 already exists; preregistration forbids retry')
freeze_path = HERE / 'FREEZE.json'
if not freeze_path.is_file():
    raise SystemExit('STOP: missing committed FREEZE.json')
freeze = json.loads(freeze_path.read_text(encoding='utf-8'))
head = call(['git', 'rev-parse', 'HEAD']).stdout.strip()
parents = call(['git', 'rev-list', '--parents', '-n', '1', 'HEAD']).stdout.split()
if len(parents) != 2 or parents[1] != freeze['freeze_commit_parent_must_equal']:
    raise SystemExit('STOP: formal HEAD is not the single frozen-manifest child commit')
if freeze.get('schema') != 'agent-interface-arena-isolation-freeze-v1' or freeze.get('source_commit') != parents[1]:
    raise SystemExit('STOP: freeze identity/parent mismatch')
if call(['git', 'status', '--porcelain']).stdout.strip():
    raise SystemExit('STOP: working tree is not clean')
for rel, item in freeze['source_hashes'].items():
    path = REPO / rel
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256_worktree_bytes']:
        raise SystemExit(f'STOP: frozen file hash mismatch: {rel}')
for name, image in freeze['images'].items():
    if json.loads(call(['docker', 'image', 'inspect', image['tag']]).stdout)[0]['Id'] != image['id']:
        raise SystemExit(f'STOP: image id mismatch: {name}')
expected_trial = {'seed': 2001, 'difficulty': 1.0, 'clock': 'fixed', 'first_stage': 'target', 'deadline_seconds': 2.6,
                  'controller_action': 'send exactly one w key-down/key-up', 'formal_allocation': 'formal/001 only; one attempt'}
if freeze.get('trial') != expected_trial:
    raise SystemExit('STOP: formal trial differs from preregistered contract')

# Exclusive directory allocation is the no-retry barrier.
OUT.mkdir(parents=True, exist_ok=False)
state = {'schema': 'arena-isolation-formal-run-v1', 'status': 'RUNNING', 'head_commit': head,
         'freeze_sha256': hashlib.sha256(freeze_path.read_bytes()).hexdigest(), 'started_utc': datetime.now(timezone.utc).isoformat(),
         'seed': 2001, 'network': NETWORK, 'evaluator_container': EVAL, 'controller_container': CTL}
(OUT / 'RUN_STATE.json').write_text(json.dumps(state, indent=2, sort_keys=True) + '\n', encoding='utf-8')
cookie = secrets.token_hex(16)
network_created = False
containers = []
try:
    call(['docker', 'network', 'create', '--internal', NETWORK])
    network_created = True
    network_raw = call(['docker', 'network', 'inspect', NETWORK]).stdout
    (OUT / 'network-inspect.json').write_text(network_raw, encoding='utf-8')
    evaluator_image, controller_image = freeze['images']['evaluator']['id'], freeze['images']['controller']['id']
    call(['docker', 'run', '-d', '--name', EVAL, '--platform', 'linux/amd64', '--network', NETWORK,
          '-e', 'ARENA_SEED=2001', '-e', f'X11_COOKIE={cookie}',
          '--tmpfs', '/evidence:rw,noexec,nosuid,size=16m', '--tmpfs', '/tmp:rw,noexec,nosuid,size=8m', evaluator_image])
    containers.append(EVAL)
    ready = False
    for _ in range(100):
        p = call(['docker', 'exec', '-e', 'XAUTHORITY=/tmp/Xauthority', EVAL, 'xwininfo', '-display', ':0', '-root', '-tree'], check=False)
        if 'Procedural Control Arena v0' in p.stdout:
            ready = True
            break
        if not json.loads(call(['docker', 'inspect', EVAL]).stdout)[0]['State']['Running']:
            break
        time.sleep(0.1)
    if not ready:
        raise RuntimeError('STOP: evaluator window did not become ready')
    (OUT / 'evaluator-inspect-before.json').write_text(call(['docker', 'inspect', EVAL]).stdout, encoding='utf-8')
    argv = call(['docker', 'exec', '-e', 'XAUTHORITY=/tmp/Xauthority', EVAL, 'python', '-c',
                 "import pathlib; print(pathlib.Path('/proc/1/cmdline').read_bytes().replace(b'\\0',b' ').decode())"])
    (OUT / 'evaluator-proc-1-cmdline.txt').write_text(argv.stdout, encoding='utf-8')
    call(['docker', 'run', '-d', '--name', CTL, '--platform', 'linux/amd64', '--network', NETWORK,
          '-e', f'DISPLAY={EVAL}:0', '-e', f'X11_COOKIE={cookie}', '--read-only', '--cap-drop=ALL',
          '--security-opt=no-new-privileges', '--user=10000:10000', '--tmpfs', '/tmp:rw,noexec,nosuid,size=8m', controller_image])
    containers.append(CTL)
    ctl_exit = int(call(['docker', 'wait', CTL], timeout=30).stdout.strip())
    ctl_logs = call(['docker', 'logs', CTL], check=False)
    (OUT / 'controller.stdout.log').write_text(ctl_logs.stdout, encoding='utf-8')
    (OUT / 'controller.stderr.log').write_text(ctl_logs.stderr, encoding='utf-8')
    lines = ctl_logs.stdout.splitlines()
    probe_line = next((line for line in lines if line.startswith('{')), None)
    xwd_line = next((line for line in lines if line.startswith('XWD_BASE64:')), None)
    if probe_line is None or xwd_line is None:
        raise RuntimeError(f'STOP: controller output incomplete (exit={ctl_exit})')
    probe = json.loads(probe_line)
    (OUT / 'controller-probe.json').write_text(json.dumps(probe, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    (OUT / 'screen.xwd').write_bytes(base64.b64decode(xwd_line.partition(':')[2], validate=True))
    (OUT / 'controller-inspect.json').write_text(call(['docker', 'inspect', CTL]).stdout, encoding='utf-8')
    if ctl_exit != 0:
        raise RuntimeError(f'STOP: controller exited {ctl_exit}')
    report_ready = False
    for _ in range(100):
        if call(['docker', 'exec', EVAL, 'test', '-s', '/evidence/report.json'], check=False).returncode == 0:
            if call(['docker', 'cp', f'{EVAL}:/evidence/report.json', str(OUT / 'report.json')], check=False).returncode == 0:
                report_ready = True
                break
        if not json.loads(call(['docker', 'inspect', EVAL]).stdout)[0]['State']['Running']:
            break
        time.sleep(0.05)
    if not report_ready:
        raise RuntimeError('STOP: evaluator report unavailable before container exit')
    evlogs = call(['docker', 'logs', EVAL], check=False)
    (OUT / 'evaluator.stdout.log').write_text(evlogs.stdout, encoding='utf-8')
    (OUT / 'evaluator.stderr.log').write_text(evlogs.stderr, encoding='utf-8')
    (OUT / 'evaluator-inspect-after.json').write_text(call(['docker', 'inspect', EVAL]).stdout, encoding='utf-8')
    state.update({'status': 'CAPTURED', 'controller_exit': ctl_exit,
                  'report_sha256': hashlib.sha256((OUT / 'report.json').read_bytes()).hexdigest(),
                  'capture_sha256': hashlib.sha256((OUT / 'screen.xwd').read_bytes()).hexdigest(),
                  'completed_utc': datetime.now(timezone.utc).isoformat()})
except Exception as exc:
    state.update({'status': 'STOP', 'stop_reason': f'{type(exc).__name__}: {exc}', 'stopped_utc': datetime.now(timezone.utc).isoformat()})
    (OUT / 'STOP.json').write_text(json.dumps(state, indent=2, sort_keys=True) + '\n', encoding='utf-8')
finally:
    for container in containers:
        call(['docker', 'rm', '-f', container], check=False)
    if network_created:
        call(['docker', 'network', 'rm', NETWORK], check=False)
    state['ended_utc'] = datetime.now(timezone.utc).isoformat()
    (OUT / 'RUN_STATE.json').write_text(json.dumps(state, indent=2, sort_keys=True) + '\n', encoding='utf-8')

if state['status'] == 'CAPTURED':
    raw = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.iterdir()) if p.is_file() and p.name not in {'RAW_MANIFEST.json', 'audit.json'}}
    (OUT / 'RAW_MANIFEST.json').write_text(json.dumps({'schema': 'arena-isolation-raw-manifest-v1', 'files': raw}, indent=2, sort_keys=True) + '\n', encoding='utf-8')
print(json.dumps(state, indent=2, sort_keys=True))
if state['status'] != 'CAPTURED':
    raise SystemExit(2)

audit_rel = HERE.relative_to(REPO).as_posix() + '/audit.py'
cmd = ['docker', 'run', '--rm', '--platform', 'linux/amd64', '--network', 'none', '--read-only', '--cap-drop=ALL',
       '--security-opt=no-new-privileges', '--user=10000:10000', '--tmpfs', '/tmp:rw,noexec,nosuid,size=8m',
       '-v', f'{OUT}:/evidence:ro', '-v', f'{REPO}:/src:ro', BASE, 'python', f'/src/{audit_rel}']
audited = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, timeout=30)
(OUT / 'audit.stdout.log').write_text(audited.stdout, encoding='utf-8')
(OUT / 'audit.stderr.log').write_text(audited.stderr, encoding='utf-8')
try:
    audit = json.loads(audited.stdout.strip())
except json.JSONDecodeError:
    audit = {'disposition': 'STOP_AUDIT_OR_PROVENANCE_INCOMPLETE', 'errors': ['auditor output invalid JSON', audited.stderr]}
(OUT / 'audit.json').write_text(json.dumps(audit, indent=2, sort_keys=True) + '\n', encoding='utf-8')
print(json.dumps(audit, indent=2, sort_keys=True))
if audited.returncode or audit.get('disposition') != 'PASS_EVALUATOR_PROCESS_AND_SOURCE_ISOLATION_SCOPED':
    raise SystemExit(3)
