"""Retained failure/custody verifier, NOT the consumed frozen science audit."""
import hashlib
import json
from pathlib import Path


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def inventory(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*')) if p.is_file()}


def check_retention(root):
    native = root / 'raw/native'; exported = root / 'raw/export'
    require(inventory(native) == inventory(exported) and bool(inventory(native)), 'export custody')
    require({p.name for p in native.iterdir() if p.is_dir()} == {'original_fault'}, 'later cells')
    require(not (native / 'SUMMARY.json').exists() and not (native / 'original_fault/RESULT.json').exists(), 'missing result boundary changed')
    manifest = root / 'NATIVE_MANIFEST.sha256'
    require(hashlib.sha256(manifest.read_bytes()).hexdigest() ==
            '37f0ded4ae7dec8ae7e1944144f26954eea5dbc600c392e8b3f760faca7332e9', 'committed native inventory anchor')
    expected = {}
    for line in manifest.read_text().splitlines():
        digest, name = line.split('  ', 1)
        name = name.removeprefix('./')
        require(name not in expected, 'committed native inventory duplicate')
        expected[name] = digest
    require(len(expected) == 25 and inventory(native) == expected, 'committed native inventory')
    freeze = json.loads((root / 'FREEZE.json').read_text())
    runtime = json.loads((native / 'RUNTIME.json').read_text())
    require(runtime['freeze'] == freeze and runtime['uid'] == 501
            and type(runtime['uid']) is int and runtime['execution_pins'] == 10
            and runtime['source_pins'] == 1917, 'runtime identity')
    require(runtime['limits'] == {'cpu.max': '100000 100000', 'memory.max': '1073741824',
            'memory.swap.max': '0', 'pids.max': '128'}, 'runtime limits')
    pins = {}
    for line in (root / 'EXECUTION_PINS.sha256').read_text().splitlines():
        digest, path = line.split('  ', 1)
        require(path not in pins and (root / path).resolve().is_relative_to(root.resolve()), 'execution path')
        require(hashlib.sha256((root / path).read_bytes()).hexdigest() == digest, 'execution hash')
        pins[path] = digest
    require(set(pins) == {'runner.py', 'gate.py', 'audit.py', 'session_entry.py', 'partial_stop.py',
        'PROTOCOL.md', 'FREEZE.json', 'SOURCE_PINS.sha256', 'source-closure.tar.gz', 'COMMANDS.md'}, 'execution closure')
    for name in ('native', 'audit'):
        receipt = json.loads((root / f'raw/{name}-container-inspect.json').read_text())
        require(len(receipt) == 1 and receipt[0]['Config']['Image'] == freeze['image'], 'container image')
        state = receipt[0]['State']
        require(state['Running'] is False and state['OOMKilled'] is False and type(state['ExitCode']) is int
                and state['ExitCode'] == 1 and type(state['Pid']) is int and state['Pid'] == 0, 'failed terminal')
    require('Xlib.error.ConnectionClosedError: Display connection closed by server' in
            (root / 'raw/native-command.log').read_text(), 'native failure identity')
    require('FileNotFoundError' in (root / 'raw/audit-command.log').read_text()
            and '/native/record/SUMMARY.json' in (root / 'raw/audit-command.log').read_text(), 'audit failure identity')
    require(not list((root / 'raw').rglob('AUDIT.json')), 'unexpected official PASS artifact')
    return {'disposition': 'STOP_RESULT_RETENTION_X11_CLOSE', 'scientific_pass': False,
            'formal_runs': 1, 'official_auditor_runs': 1, 'later_cells': 0,
            'producer_reruns': 0, 'retained_native_files': len(inventory(native)),
            'scope': 'saved failure/custody only; run counts describe retained protocol receipts, not all external execution history; no physical snapshot or reader outcome recovery'}


if __name__ == '__main__':
    print(json.dumps(check_retention(Path(__file__).resolve().parent), sort_keys=True))
