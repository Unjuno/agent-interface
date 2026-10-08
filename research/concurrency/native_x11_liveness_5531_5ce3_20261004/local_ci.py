"""Local applicable CI and read-only saved evidence checks, no native calls."""
import hashlib, json, subprocess, sys
from pathlib import Path
from auditor import check, negatives
ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]

def verify():
    freeze = json.loads((ROOT/'FREEZE.json').read_text())
    for path, digest in freeze['sha256'].items():
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == digest, path
    result = json.loads((ROOT/'RESULT.json').read_text())
    raw = ROOT/'runs/candidate/raw.jsonl'
    assert hashlib.sha256(raw.read_bytes()).hexdigest() == result['raw_sha256']
    assert hashlib.sha256((ROOT/'FREEZE.json').read_bytes()).hexdigest() == result['freeze_sha256']
    rows = [json.loads(line) for line in raw.read_text().splitlines()]
    assert check(rows) == result['first_status'] and len(negatives(rows)) == 8
    audit = json.loads((ROOT/'runs/auditor/AUDIT.json').read_text())
    assert audit['status'] == result['first_status'] and audit['raw_sha256'] == result['raw_sha256']
    for stage in ('candidate', 'auditor'):
        receipt = json.loads((ROOT/f'runs/{stage}/receipt.json').read_text())
        assert receipt['freeze_sha256'] == result['freeze_sha256'] and receipt['run']['returncode'] == 0
        assert receipt['terminal']['Running'] is False and receipt['terminal']['ExitCode'] == 0 and receipt['terminal']['OOMKilled'] is False
    if (ROOT/'FILES.json').exists():
        manifest = json.loads((ROOT/'FILES.json').read_text())
        for path, digest in manifest.items():
            assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == digest, path
    return {'frozen_files': len(freeze['sha256']), 'raw_rows': len(rows), 'saved_replay_status': result['first_status'], 'manifest_checked': (ROOT/'FILES.json').exists()}

def main():
    results = []
    commands = [(ROOT, ['-m', 'unittest', 'test_policy', 'test_auditor']), (REPO, ['-m', 'unittest', 'discover', '-s', 'research', '-p', 'test_*workspace*.py', '-v']), (REPO, ['-m', 'unittest', '-v', 'research/doom/test_map01_scorer_scheduler_replay_3270.py']), (REPO, ['research/check_workspace_index.py', '--git-tree'])]
    for cwd, args in commands:
        p = subprocess.run([sys.executable, '-B', *args], cwd=cwd, capture_output=True, text=True, timeout=60)
        results.append({'cwd': str(cwd), 'args': args, 'exit': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr})
    result = {'checks': results, 'evidence': verify()}
    if len(sys.argv) > 1:
        with (ROOT/sys.argv[1]).open('x') as f: json.dump(result, f, indent=2); f.write('\n')
    print(json.dumps(result, indent=2))
    return int(any(x['exit'] != 0 for x in results))
if __name__ == '__main__': sys.exit(main())
