"""Delivery hashes and retained STOP consistency, NOT the frozen semantic auditor."""
import hashlib
import json
from pathlib import Path
import tarfile


def check_manifest(root, manifest):
    seen = set()
    for line in manifest.read_text().splitlines():
        digest, relative = line.split('  ', 1)
        path = (root / relative).resolve()
        require(path.is_relative_to(root.resolve()), 'manifest path escaped root')
        require(relative not in seen, 'duplicate manifest path')
        require(hashlib.sha256(path.read_bytes()).hexdigest() == digest, 'payload hash mismatch: ' + relative)
        seen.add(relative)
    require(bool(seen), 'empty manifest')
    return len(seen)


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def check_stop(root):
    native = root / 'raw/native'; exported = root / 'raw/export'
    native_files = {str(p.relative_to(native)): p.read_bytes() for p in native.rglob('*') if p.is_file()}
    exported_files = {str(p.relative_to(exported)): p.read_bytes() for p in exported.rglob('*') if p.is_file()}
    require(native_files == exported_files and len(native_files) == 5, 'native/export custody')
    summary = json.loads((native / 'SUMMARY.json').read_text())
    wanted = {'cases': ['original_fault'], 'cells': 1, 'formal_runs': 1,
              'gameplay_success_claim': False, 'model_calls': 0, 'retries': 0, 'verdict': 'STOP_NATIVE_GATE'}
    require(json.dumps(summary, sort_keys=True) == json.dumps(wanted, sort_keys=True), 'retained summary')
    row = json.loads((native / 'original_fault/RESULT.json').read_text())
    require(row['case'] == 'original_fault' and row['release_gate'] is False and row['outcome_gate'] is False,
            'zero-exposure disposition')
    require(type(row['child_exit']) is int and row['child_exit'] == 1 and row['cleanup_faults'] == [], 'owned child terminal')
    require(not any(k in row for k in ('held', 'accepted', 'injected_ns', 'wait_outcome')), 'unexpected formal exposure')
    require((native / 'original_fault/native-stdout.jsonl').read_bytes() == b'', 'native stdout not empty')
    require("ModuleNotFoundError: No module named 'doom_typed_release_backend_v1'" in
            (native / 'original_fault/session.stderr.log').read_text(), 'actual startup failure')
    require('FileNotFoundError' in (root / 'raw/audit-command.log').read_text() and
            'imports.json' in (root / 'raw/audit-command.log').read_text(), 'official audit failure missing')
    require(not list((root / 'raw').rglob('AUDIT.json')), 'no official semantic audit pass')
    for name in ('native', 'audit'):
        receipt = json.loads((root / f'raw/{name}-container-inspect.json').read_text())
        require(len(receipt) == 1, 'container receipt cardinality')
        state = receipt[0]['State']
        require(type(state['ExitCode']) is int and state['ExitCode'] == 1 and state['Running'] is False and state['Pid'] == 0
                and state['OOMKilled'] is False, 'terminal container state')
    runtime = json.loads((native / 'RUNTIME.json').read_text())
    require(runtime['uid'] == 501 and runtime['source_pins'] == 1917 and runtime['execution_pins'] == 9, 'runtime/source pins')
    require(runtime['limits'] == {'cpu.max': '100000 100000', 'memory.max': '1073741824',
             'memory.swap.max': '0', 'pids.max': '128'}, 'actual native cgroup sample')
    require(runtime['freeze'] == json.loads((root / 'FREEZE.json').read_text()), 'runtime freeze changed')
    check_manifest(root, root / 'EXECUTION_PINS.sha256')
    with tarfile.open(root / 'source-closure.tar.gz', 'r:gz') as archive:
        actual = {m.name: hashlib.sha256(archive.extractfile(m).read()).hexdigest()
                  for m in archive.getmembers() if m.isfile()}
    expected = {line.split('  ', 1)[1]: line.split('  ', 1)[0]
                for line in (root / 'SOURCE_PINS.sha256').read_text().splitlines()}
    require(actual == expected and len(actual) == 1917, 'archive/source pin closure')
    return {'retention': 'PASS_HASH_AND_STOP_CONSISTENCY', 'semantic_auditor': 'FAILED_NO_PASS',
            'native': 'STOP_NATIVE_GATE', 'formal_native_reruns': 0}


if __name__ == '__main__':
    root = Path(__file__).resolve().parent
    count = check_manifest(root, root / 'DELIVERY_MANIFEST.sha256')
    print(json.dumps({**check_stop(root), 'manifest_files': count}, sort_keys=True))
