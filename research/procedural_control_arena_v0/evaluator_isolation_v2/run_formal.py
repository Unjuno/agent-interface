"""One-shot successor allocation formal/002. Never retry this path."""
import base64
import hashlib
import json
import secrets
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from inspection import inspect_to_file

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
BASE = 'python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9'
OUT = HERE / 'formal/002'
NETWORK, EVAL, CTL = 'arena-isolation-v2-formal-002', 'arena-isolation-v2-formal-002-eval', 'arena-isolation-v2-formal-002-controller'

def call(args, *, check=True, timeout=30):
    p = subprocess.run(args, cwd=REPO, capture_output=True, text=True, timeout=timeout)
    if check and p.returncode:
        raise RuntimeError(f"command failed ({p.returncode}): {args}\n{p.stdout}\n{p.stderr}")
    return p

if OUT.exists():
    raise SystemExit('STOP: formal/002 already exists; no retry allowed')
freeze_path = HERE / 'FREEZE.json'
if not freeze_path.is_file():
    raise SystemExit('STOP: missing committed FREEZE.json')
freeze = json.loads(freeze_path.read_text(encoding='utf-8'))
head = call(['git', 'rev-parse', 'HEAD']).stdout.strip()
parents = call(['git', 'rev-list', '--parents', '-n', '1', 'HEAD']).stdout.split()
if len(parents) != 2 or parents[1] != freeze.get('freeze_commit_parent_must_equal') or freeze.get('source_commit') != parents[1]:
    raise SystemExit('STOP: HEAD is not the exact freeze-manifest child')
if call(['git', 'status', '--porcelain']).stdout.strip():
    raise SystemExit('STOP: working tree is not clean')
for rel, item in freeze['source_hashes'].items():
    if not (REPO / rel).is_file() or hashlib.sha256((REPO / rel).read_bytes()).hexdigest() != item['sha256_worktree_bytes']:
        raise SystemExit(f'STOP: frozen source hash mismatch: {rel}')
for name, image in freeze['images'].items():
    actual = json.loads(call(['docker', 'image', 'inspect', image['tag']]).stdout)[0]['Id']
    if actual != image['id']:
        raise SystemExit(f'STOP: frozen image id mismatch: {name}')
expected = {'seed': 2003, 'difficulty': 1.0, 'clock': 'fixed', 'first_stage': 'target', 'deadline_seconds': 2.6,
            'controller_action': 'send exactly one w key-down/key-up', 'allocation': 'formal/002 only; one attempt',
            'evaluator_report_persistence': 'evaluator-only host bind at /evidence', 'auto_close_seconds_after_terminal': 30}
if freeze.get('trial') != expected:
    raise SystemExit('STOP: trial differs from preregistered successor')

# This exclusive create is the single-attempt barrier.
OUT.mkdir(parents=True, exist_ok=False)
result_dir = OUT / 'evaluator-result'
result_dir.mkdir()
state = {'schema': 'arena-isolation-v2-formal-run-v1', 'status': 'RUNNING', 'head_commit': head,
         'freeze_sha256': hashlib.sha256(freeze_path.read_bytes()).hexdigest(), 'started_utc': datetime.now(timezone.utc).isoformat(),
         'seed': 2003, 'network': NETWORK, 'evidence_bind_path': 'evaluator-result'}
(OUT / 'RUN_STATE.json').write_text(json.dumps(state, indent=2, sort_keys=True) + '\n', encoding='utf-8')
cookie = secrets.token_hex(16)
network_created = False
containers = []
try:
    call(['docker', 'network', 'create', '--internal', NETWORK])
    network_created = True
    (OUT / 'network-inspect.json').write_text(call(['docker', 'network', 'inspect', NETWORK]).stdout, encoding='utf-8')
    ev_image = freeze['images']['evaluator']['id']
    ctl_image = freeze['images']['controller']['id']
    call(['docker', 'run', '-d', '--name', EVAL, '--platform', 'linux/amd64', '--network', NETWORK,
          '-e', 'ARENA_SEED=2003', '-e', f'X11_COOKIE={cookie}', '-e', 'ARENA_AUTOCLOSE=30', '--read-only', '--cap-drop=ALL',
          '--security-opt=no-new-privileges', '--tmpfs', '/tmp:rw,noexec,nosuid,size=8m', '-v', f'{result_dir}:/evidence:rw', ev_image])
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
        raise RuntimeError('STOP: evaluator GUI window not ready')
    inspect_to_file(EVAL, OUT / 'evaluator-inspect-before.json')
    argv = call(['docker', 'exec', '-e', 'XAUTHORITY=/tmp/Xauthority', EVAL, 'python', '-c',
                 "import pathlib;print(pathlib.Path('/proc/1/cmdline').read_bytes().replace(b'\\0',b' ').decode())"])
    (OUT / 'evaluator-proc-1-cmdline.txt').write_text(argv.stdout, encoding='utf-8')
    call(['docker', 'run', '-d', '--name', CTL, '--platform', 'linux/amd64', '--network', NETWORK,
          '-e', f'DISPLAY={EVAL}:0', '-e', f'X11_COOKIE={cookie}', '--read-only', '--cap-drop=ALL',
          '--security-opt=no-new-privileges', '--user=10000:10000', '--tmpfs', '/tmp:rw,noexec,nosuid,size=8m', ctl_image])
    containers.append(CTL)
    ctl_exit = int(call(['docker', 'wait', CTL], timeout=30).stdout.strip())
    ctl_logs = call(['docker', 'logs', CTL], check=False)
    (OUT / 'controller.stdout.log').write_text(ctl_logs.stdout, encoding='utf-8')
    (OUT / 'controller.stderr.log').write_text(ctl_logs.stderr, encoding='utf-8')
    probe_line = next((line for line in ctl_logs.stdout.splitlines() if line.startswith('{')), None)
    xwd_line = next((line for line in ctl_logs.stdout.splitlines() if line.startswith('XWD_BASE64:')), None)
    if probe_line is None or xwd_line is None:
        raise RuntimeError(f'STOP: controller output incomplete (exit={ctl_exit})')
    probe = json.loads(probe_line)
    (OUT / 'controller-probe.json').write_text(json.dumps(probe, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    (OUT / 'screen.xwd').write_bytes(base64.b64decode(xwd_line.partition(':')[2], validate=True))
    inspect_to_file(CTL, OUT / 'controller-inspect.json')
    if ctl_exit:
        raise RuntimeError(f'STOP: controller exited {ctl_exit}')

    report_in_evidence = result_dir / 'report.json'
    for _ in range(100):
        if report_in_evidence.is_file() and report_in_evidence.stat().st_size:
            shutil.copyfile(report_in_evidence, OUT / 'report.json')
            break
        if not json.loads(call(['docker', 'inspect', EVAL]).stdout)[0]['State']['Running']:
            break
        time.sleep(0.05)
    if not (OUT / 'report.json').is_file():
        raise RuntimeError('STOP: evaluator did not persist report into its host evidence bind')
    call(['docker', 'stop', EVAL], check=False)
    evlogs = call(['docker', 'logs', EVAL], check=False)
    (OUT / 'evaluator.stdout.log').write_text(evlogs.stdout, encoding='utf-8')
    (OUT / 'evaluator.stderr.log').write_text(evlogs.stderr, encoding='utf-8')
    inspect_to_file(EVAL, OUT / 'evaluator-inspect-after.json')
    state.update({'status': 'CAPTURED', 'controller_exit': ctl_exit, 'report_sha256': hashlib.sha256((OUT / 'report.json').read_bytes()).hexdigest(),
                  'capture_sha256': hashlib.sha256((OUT / 'screen.xwd').read_bytes()).hexdigest(), 'completed_utc': datetime.now(timezone.utc).isoformat()})
except Exception as exc:
    state.update({'status': 'STOP', 'stop_reason': f'{type(exc).__name__}: {exc}', 'stopped_utc': datetime.now(timezone.utc).isoformat()})
    (OUT / 'STOP.json').write_text(json.dumps(state, indent=2, sort_keys=True) + '\n', encoding='utf-8')
finally:
    for name in containers:
        inspect = call(['docker', 'inspect', name], check=False)
        if inspect.returncode == 0:
            path = OUT / ('evaluator-inspect-cleanup.json' if name == EVAL else 'controller-inspect-cleanup.json')
            if not path.exists():
                inspect_to_file(name, path)
            logs = call(['docker', 'logs', name], check=False)
            path = OUT / ('evaluator-cleanup.log' if name == EVAL else 'controller-cleanup.log')
            if not path.exists():
                path.write_text(logs.stdout + logs.stderr, encoding='utf-8')
        call(['docker', 'rm', '-f', name], check=False)
    if network_created:
        net = call(['docker', 'network', 'inspect', NETWORK], check=False)
        if net.returncode == 0:
            (OUT / 'network-inspect-final.json').write_text(net.stdout, encoding='utf-8')
        call(['docker', 'network', 'rm', NETWORK], check=False)
    state['ended_utc'] = datetime.now(timezone.utc).isoformat()
    (OUT / 'RUN_STATE.json').write_text(json.dumps(state, indent=2, sort_keys=True) + '\n', encoding='utf-8')

if state['status'] == 'CAPTURED':
    raw = {p.relative_to(OUT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.rglob('*')
           if p.is_file() and p.name not in {'RAW_MANIFEST.json', 'audit.json'}}
    (OUT / 'RAW_MANIFEST.json').write_text(json.dumps({'schema': 'arena-isolation-v2-raw-manifest-v1', 'files': raw}, indent=2, sort_keys=True) + '\n', encoding='utf-8')
print(json.dumps(state, indent=2, sort_keys=True))
if state['status'] != 'CAPTURED':
    raise SystemExit(2)

audit_rel = HERE.relative_to(REPO).as_posix() + '/audit.py'
cmd = ['docker', 'run', '--rm', '--platform', 'linux/amd64', '--network', 'none', '--read-only', '--cap-drop=ALL', '--security-opt=no-new-privileges',
       '--user=10000:10000', '--tmpfs', '/tmp:rw,noexec,nosuid,size=8m', '-v', f'{OUT}:/evidence:ro', '-v', f'{REPO}:/src:ro', BASE, 'python', f'/src/{audit_rel}']
aud = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, timeout=30)
(OUT / 'audit.stdout.log').write_text(aud.stdout, encoding='utf-8')
(OUT / 'audit.stderr.log').write_text(aud.stderr, encoding='utf-8')
try:
    audit = json.loads(aud.stdout.strip())
except json.JSONDecodeError:
    audit = {'disposition': 'STOP_AUDIT_OR_PROVENANCE_INCOMPLETE', 'errors': ['auditor output invalid JSON', aud.stderr]}
(OUT / 'audit.json').write_text(json.dumps(audit, indent=2, sort_keys=True) + '\n', encoding='utf-8')
print(json.dumps(audit, indent=2, sort_keys=True))
if aud.returncode or audit.get('disposition') != 'PASS_EVALUATOR_PROCESS_AND_SOURCE_ISOLATION_SCOPED':
    raise SystemExit(3)
