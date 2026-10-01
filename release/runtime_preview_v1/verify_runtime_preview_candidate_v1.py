from __future__ import annotations
import argparse, hashlib, json, stat, subprocess, sys
from pathlib import Path

LAUNCHERS = [Path('runtime/setup-golden-demo-v3.sh'), Path('runtime/golden-demo-v3.sh')]
REQUIRED = [
    *LAUNCHERS,
    Path('runtime/golden_desktop_demo_v3.py'),
    Path('runtime/requirements-golden.txt'),
    Path('runtime/README.md'),
    Path('release/golden_artifact_closure_v1/check_golden_artifact_closure.py'),
]
SUPPORT = Path('release/runtime_preview_v1/support.json')
CHECKSUMS = Path('SHA256SUMS')

def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()

def parse_checksums(path: Path) -> dict[str, str]:
    out = {}
    for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        if not line.strip():
            continue
        try:
            sha, rel = line.split('  ', 1)
        except ValueError:
            raise ValueError(f'invalid SHA256SUMS line {number}')
        if len(sha) != 64 or any(c not in '0123456789abcdef' for c in sha):
            raise ValueError(f'invalid sha line {number}')
        if rel.startswith('/') or '..' in Path(rel).parts:
            raise ValueError(f'unsafe path line {number}')
        if rel in out:
            raise ValueError(f'duplicate path {rel}')
        out[rel] = sha
    return out

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('root', type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    result = {'schema': 'runtime-preview-candidate-verification-v1', 'root': str(root), 'passed': False, 'checks': {}, 'failures': []}

    missing = [str(path) for path in REQUIRED + [SUPPORT, CHECKSUMS] if not (root / path).is_file()]
    result['checks']['required_files'] = {'missing': missing, 'passed': not missing}
    if missing:
        result['failures'].append('required_files')

    bad_modes = []
    for rel in LAUNCHERS:
        path = root / rel
        if path.is_file() and not (path.stat().st_mode & stat.S_IXUSR):
            bad_modes.append(str(rel))
    result['checks']['launcher_executable'] = {'bad': bad_modes, 'passed': not bad_modes}
    if bad_modes:
        result['failures'].append('launcher_executable')

    support_ok = False
    support_error = None
    if (root / SUPPORT).is_file():
        try:
            support = json.loads((root / SUPPORT).read_text(encoding='utf-8'))
            support_ok = (
                support.get('schema') == 'agent-interface-runtime-preview-support-v1'
                and support.get('tested_host') == 'WSLg'
                and isinstance(support.get('release_candidate_sha'), str)
                and len(support['release_candidate_sha']) == 40
                and support.get('research_preview') is True
            )
            if not support_ok:
                support_error = 'required support fields missing/invalid'
        except Exception as error:
            support_error = f'{type(error).__name__}: {error}'
    result['checks']['support_metadata'] = {'passed': support_ok, 'error': support_error}
    if not support_ok:
        result['failures'].append('support_metadata')

    checksum_ok = False
    checksum_errors = []
    checksum_entries = 0
    if (root / CHECKSUMS).is_file():
        try:
            entries = parse_checksums(root / CHECKSUMS)
            checksum_entries = len(entries)
            required_for_sum = [str(path) for path in REQUIRED + [SUPPORT]]
            absent = [path for path in required_for_sum if path not in entries]
            if absent:
                checksum_errors.append({'missing_entries': absent})
            for rel, expected in entries.items():
                path = root / rel
                if not path.is_file():
                    checksum_errors.append({'missing_file': rel})
                    continue
                actual = digest(path)
                if actual != expected:
                    checksum_errors.append({'hash_mismatch': rel, 'expected': expected, 'actual': actual})
            checksum_ok = not checksum_errors
        except Exception as error:
            checksum_errors.append({'parse_error': f'{type(error).__name__}: {error}'})
    result['checks']['checksums'] = {'passed': checksum_ok, 'entries': checksum_entries, 'errors': checksum_errors}
    if not checksum_ok:
        result['failures'].append('checksums')

    closure_ok = False
    closure_rc = None
    closure_json = None
    checker = root / 'release/golden_artifact_closure_v1/check_golden_artifact_closure.py'
    if checker.is_file():
        process = subprocess.run([sys.executable, str(checker), str(root)], capture_output=True, text=True)
        closure_rc = process.returncode
        try:
            closure_json = json.loads(process.stdout)
        except Exception:
            closure_json = {'stdout': process.stdout, 'stderr': process.stderr}
        closure_ok = process.returncode == 0 and closure_json.get('passed') is True
    result['checks']['golden_retained_closure'] = {'passed': closure_ok, 'returncode': closure_rc, 'result': closure_json}
    if not closure_ok:
        result['failures'].append('golden_retained_closure')

    result['passed'] = not result['failures']
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result['passed'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
