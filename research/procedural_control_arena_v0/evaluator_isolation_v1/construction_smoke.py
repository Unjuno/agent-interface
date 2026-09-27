"""Disposable GUI/X11 smoke test. It must never be cited as the formal trial."""
import json
import secrets
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / 'construction' / 'smoke-02'
OUT.mkdir(exist_ok=True)
NETWORK = 'arena-isolation-construction'
EVAL = 'arena-isolation-construction-eval'
CTL = 'arena-isolation-construction-ctl'
SEED = '2002'
COOKIE = secrets.token_hex(16)

def call(args, *, check=True, **kwargs):
    result = subprocess.run(args, capture_output=True, text=True, **kwargs)
    if check and result.returncode:
        raise RuntimeError(f"command failed ({result.returncode}): {args}\n{result.stdout}\n{result.stderr}")
    return result

for name in (EVAL, CTL):
    call(['docker', 'rm', '-f', name], check=False)
call(['docker', 'network', 'rm', NETWORK], check=False)
call(['docker', 'network', 'create', '--internal', NETWORK])
network_inspect = call(['docker', 'network', 'inspect', NETWORK]).stdout
(OUT / 'smoke-network-inspect.json').write_text(network_inspect, encoding='utf-8')
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
    call(['docker', 'run', '-d', '--name', CTL, '--platform', 'linux/amd64', '--network', NETWORK,
                '-e', f'DISPLAY={display}', '-e', f'X11_COOKIE={COOKIE}',
                '--read-only', '--cap-drop=ALL', '--security-opt=no-new-privileges', '--user=10000:10000',
                '--tmpfs', '/tmp:rw,noexec,nosuid,size=8m', 'agent-arena-isolation-controller:20260927'])
    ctl_exit = int(call(['docker', 'wait', CTL]).stdout.strip())
    ctl_logs = call(['docker', 'logs', CTL], check=False)
    lines = ctl_logs.stdout.splitlines()
    probe_line = next(line for line in lines if line.startswith('{'))
    xwd_line = next(line for line in lines if line.startswith('XWD_BASE64:'))
    import base64
    (OUT / 'screen.xwd').write_bytes(base64.b64decode(xwd_line.partition(':')[2]))
    (OUT / 'controller-probe.json').write_text(json.dumps(json.loads(probe_line), indent=2, sort_keys=True) + '\n', encoding='utf-8')
    (OUT / 'smoke-controller.stdout').write_text(probe_line + '\n', encoding='utf-8')
    (OUT / 'smoke-controller.stderr').write_text(ctl_logs.stderr, encoding='utf-8')
    ctl_inspect = call(['docker', 'inspect', CTL]).stdout
    (OUT / 'smoke-controller-inspect.json').write_text(ctl_inspect, encoding='utf-8')
    if ctl_exit:
        raise RuntimeError(f'controller smoke failed: {ctl_exit}')
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
        'controller_exit': ctl_exit,
        'controller_output': json.loads((OUT / 'controller-probe.json').read_text(encoding='utf-8')),
        'network_inspect': json.loads(network_inspect)[0],
        'report': json.loads(report),
        'inspect': json.loads(inspected)[0],
        'controller_inspect': json.loads(ctl_inspect)[0],
    }
    (OUT / 'CONSTRUCTION_SMOKE.json').write_text(json.dumps(checks, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    ev = checks['report']['episode']
    assert ev['stages'][0]['kind'] == 'target'
    assert checks['report']['failure_reason'] == 'deadline_miss'
    assert any(e['event'] == 'key_down' and e['detail'].get('key') == 'w' for e in checks['report']['events'])
    assert checks['controller_output']['path_access']['/opt/arena/arena.py'] is False
    assert '2002' not in json.dumps(checks['controller_output']['proc_cmdlines'])
    assert checks['controller_output']['capture_sha256'] == __import__('hashlib').sha256((OUT / 'screen.xwd').read_bytes()).hexdigest()
    assert checks['network_inspect']['Internal'] is True
    assert checks['controller_inspect']['Config']['User'] == '10000:10000'
    assert checks['controller_inspect']['HostConfig']['ReadonlyRootfs'] is True
    assert checks['controller_inspect']['HostConfig']['CapDrop'] == ['ALL']
    assert checks['controller_inspect']['HostConfig']['Privileged'] is False
    assert checks['controller_inspect']['HostConfig']['PidMode'] in ('', None)
    assert checks['controller_inspect']['Mounts'] == []
    assert 'no-new-privileges' in checks['controller_inspect']['HostConfig']['SecurityOpt']
    print(json.dumps({'construction': 'PASS', 'seed': int(SEED), 'report_failure': checks['report']['failure_reason'], 'capture_bytes': checks['controller_output']['capture_bytes']}))
finally:
    call(['docker', 'rm', '-f', EVAL], check=False)
    call(['docker', 'rm', '-f', CTL], check=False)
    call(['docker', 'network', 'rm', NETWORK], check=False)
