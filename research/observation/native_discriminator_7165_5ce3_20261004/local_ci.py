"""Local applicable checks and saved-only replay; never spend native allocation."""
import hashlib, json, subprocess, sys
from pathlib import Path
from auditor import check, controls
ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
def verify():
    freeze = json.loads((ROOT/'FREEZE.json').read_text())
    for path, digest in freeze['sha256'].items():
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == digest, path
    result = json.loads((ROOT/'RESULT.json').read_text()); rows = []; truth = []
    for name, key, target in [('raw.jsonl', 'raw_sha256', rows), ('oracle.jsonl', 'oracle_sha256', truth)]:
        path = ROOT/'runs/candidate'/name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == result[key]
        target.extend(json.loads(s) for s in path.read_text().splitlines())
    derived = check(rows, truth); assert derived['first_status'] == result['first_status'] and len(controls(rows, truth)) == 8
    audit = json.loads((ROOT/'runs/auditor/AUDIT.json').read_text())
    assert audit['first_status'] == result['first_status'] and audit['metrics'] == derived['metrics']
    assert hashlib.sha256((ROOT/'FREEZE.json').read_bytes()).hexdigest() == result['freeze_sha256']
    for stage in ('candidate', 'auditor'):
        r = json.loads((ROOT/f'runs/{stage}/receipt.json').read_text())
        assert r['freeze_sha256'] == result['freeze_sha256'] and r['run']['returncode'] == 0
        assert r['terminal']['Running'] is False and r['terminal']['ExitCode'] == 0 and r['terminal']['OOMKilled'] is False
    if (ROOT/'FILES.json').exists():
        for path, digest in json.loads((ROOT/'FILES.json').read_text()).items():
            assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == digest, path
    return {'first_scientific_status': result['first_status'], 'rows': len(rows), 'frozen_files': len(freeze['sha256']), 'manifest_checked': (ROOT/'FILES.json').exists()}
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
    return int(any(r['exit'] for r in results))
if __name__ == '__main__': sys.exit(main())
