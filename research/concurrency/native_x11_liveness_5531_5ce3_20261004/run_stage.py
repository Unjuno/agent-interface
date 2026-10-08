"""Owned digest-pinned stages; x-create output dirs prohibit stage reruns."""
import datetime, hashlib, json, subprocess, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent
def call(args, timeout=60):
    t = time.monotonic_ns(); p = subprocess.run(args, capture_output=True, timeout=timeout)
    return {'command': args, 'returncode': p.returncode, 'stdout': p.stdout.decode(errors='replace'), 'stderr': p.stderr.decode(errors='replace'), 'elapsed_ns': time.monotonic_ns()-t}
def main():
    stage = sys.argv[1]; assert stage in ('preflight', 'candidate', 'auditor', 'tests')
    plan = json.loads((ROOT/'PLAN.json').read_text())
    if stage in ('candidate', 'auditor'):
        freeze = json.loads((ROOT/'FREEZE.json').read_text())
        for path, digest in freeze['sha256'].items():
            assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == digest, ('SOURCE_DRIFT', path)
    if stage == 'auditor':
        prior = json.loads((ROOT/'runs/candidate/receipt.json').read_text())
        assert prior['run']['returncode'] == 0 and prior['terminal']['Running'] is False and prior['terminal']['ExitCode'] == 0
    out = ROOT/'runs'/stage; out.mkdir(parents=True, exist_ok=False)
    engine = ['orbctl', 'run', '-m', plan['vm'], '-u', 'root', 'docker']
    name = 'liveness-5531-n01-5ce3-' + stage
    args = engine + ['create', '--name', name, '--pull', 'never', '--entrypoint', 'python3', '--network', 'none', '--read-only', '--cpus', '1', '--memory', '512m', '--memory-swap', '512m', '--pids-limit', '128', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges', '--tmpfs', '/tmp:rw,nosuid,nodev,size=64m', '--label', 'research.owner=01a0b98b-5ce3-7f53-82f3-e09294f24d57', '--mount', f'type=bind,src={ROOT},dst=/study,readonly', '--mount', f'type=bind,src={out},dst=/out', '--workdir', '/study', plan['image'], '-B']
    if stage == 'auditor': args += ['/study/auditor.py', '/study/runs/candidate/raw.jsonl', '/out/AUDIT.json']
    elif stage == 'tests': args += ['-m', 'unittest', 'test_policy', 'test_auditor']
    else:
        args += ['/study/candidate.py', '/out']
        if stage == 'preflight': args += ['--preflight']
    receipt = {'stage': stage, 'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'freeze_sha256': hashlib.sha256((ROOT/'FREEZE.json').read_bytes()).hexdigest() if stage in ('candidate', 'auditor') else None, 'create': call(args)}
    try:
        assert receipt['create']['returncode'] == 0
        receipt['run'] = call(engine + ['start', '-a', name])
        receipt['after'] = call(engine + ['inspect', name])
        receipt['terminal'] = json.loads(receipt['after']['stdout'])[0]['State']
        assert receipt['terminal']['Running'] is False and receipt['terminal']['ExitCode'] == 0 and not receipt['terminal']['OOMKilled'] and receipt['run']['returncode'] == 0
    finally:
        receipt['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with (out/'receipt.json').open('x') as f: json.dump(receipt, f, indent=2); f.write('\n')
    print(json.dumps({'stage': stage, 'terminal': receipt['terminal']}))
if __name__ == '__main__': main()
