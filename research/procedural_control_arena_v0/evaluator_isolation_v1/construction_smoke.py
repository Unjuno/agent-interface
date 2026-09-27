"""Disposable GUI/X11 smoke test. It must never be cited as the formal trial."""
import json
import secrets
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / 'construction'
OUT.mkdir(exist_ok=True)
NETWORK = 'arena-isolation-construction'
EVAL = 'arena-isolation-construction-eval'
SEED = '2002'
COOKIE = secrets.token_hex(16)

def call(args, *, check=True, **kwargs):
    result = subprocess.run(args, capture_output=True, text=True, **kwargs)
    if check and result.returncode:
        raise RuntimeError(f"command failed ({result.returncode}): {args}\n{result.stdout}\n{result.stderr}")
    return result

for name in (EVAL, NETWORK):
    call(['docker', 'rm', '-f', name], check=False) if name == EVAL else call(['docker', 'network', 'rm', name], check=False)
call(['docker', 'network', 'create', '--internal', NETWORK])
call(['docker', 'run', '-d', '--name', EVAL, '--platform', 'linux/amd64', '--network', NETWORK,
      '-e', f'ARENA_SEED={SEED}', '-e', f'X11_COOKIE={COOKIE}',
      '--tmpfs', '/evidence:rw,noexec,nosuid,size=8m', '--tmpfs', '/tmp:rw,noexec,nosuid,size=8m',
      'agent-arena-isolation-evaluator:20260927'])
try:
    ready = False
    for _ in range(100):
        tree = call(['docker', 'exec', '-e', 'XAUTHORITY=/tmp/Xauthority', EVAL, 'xwininfo', '-display', ':0', '-root', '-tree'], check=False)
        if 'Procedural Control Arena v0' in tree.stdout:
            ready = True
            break
        time.sleep(0.1)
    if not ready:
        logs = call(['docker', 'logs', EVAL], check=False)
        (OUT / 'smoke-evaluator.log').write_text(logs.stdout + logs.stderr, encoding='utf-8')
        raise RuntimeError('STOP: GUI window did not become ready; see construction/smoke-evaluator.log')
    display = f'{EVAL}:0'
    ctl = call(['docker', 'run', '--rm', '--platform', 'linux/amd64', '--network', NETWORK,
                '-e', f'DISPLAY={display}', '-e', f'X11_COOKIE={COOKIE}',
                '--read-only', '--cap-drop=ALL', '--security-opt=no-new-privileges', '--user=10000:10000',
                '--tmpfs', '/tmp:rw,noexec,nosuid,size=8m', 'agent-arena-isolation-controller:20260927'], check=False)
    (OUT / 'smoke-controller.stdout').write_text(ctl.stdout, encoding='utf-8')
    (OUT / 'smoke-controller.stderr').write_text(ctl.stderr, encoding='utf-8')
    if ctl.returncode:
        raise RuntimeError(f'controller smoke failed: {ctl.returncode}')
    for _ in range(100):
        report_ready = call(['docker', 'exec', EVAL, 'test', '-s', '/evidence/report.json'], check=False).returncode == 0
        if report_ready:
            break
        time.sleep(0.1)
    if not report_ready:
        raise RuntimeError('STOP: evaluator report not produced')
    report = call(['docker', 'exec', EVAL, 'cat', '/evidence/report.json']).stdout
    (OUT / 'smoke-report.json').write_text(report, encoding='utf-8')
    inspected = call(['docker', 'inspect', EVAL]).stdout
    (OUT / 'smoke-evaluator-inspect.json').write_text(inspected, encoding='utf-8')
    checks = {
        'construction_only_seed': int(SEED),
        'controller_exit': ctl.returncode,
        'controller_output': json.loads(ctl.stdout),
        'report': json.loads(report),
        'inspect': json.loads(inspected)[0],
    }
    (OUT / 'CONSTRUCTION_SMOKE.json').write_text(json.dumps(checks, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    ev = checks['report']['episode']
    assert ev['stages'][0]['kind'] == 'target'
    assert checks['report']['failure_reason'] == 'deadline_miss'
    assert any(e['event'] == 'key_down' and e['detail'].get('key') == 'w' for e in checks['report']['events'])
    assert checks['controller_output']['path_access']['/opt/arena/arena.py'] is False
    print(json.dumps({'construction': 'PASS', 'seed': int(SEED), 'report_failure': checks['report']['failure_reason'], 'capture_bytes': checks['controller_output']['capture_bytes']}))
finally:
    call(['docker', 'rm', '-f', EVAL], check=False)
    call(['docker', 'network', 'rm', NETWORK], check=False)
