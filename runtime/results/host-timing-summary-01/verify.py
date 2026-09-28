"""Recompute host timing from hash-bound original evidence; never execute archived code."""
import hashlib
import json
from pathlib import Path
import sys
import tarfile
import tempfile

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root.parents[2]))
from runtime.integration_checks.host_timing import summarize

source = root.parent / 'guarded-observation-refs-primary-01'
prefix = 'results-local/guarded-observation-refs-primary-01/transport/'
expected = json.loads((root / 'report.json').read_text())
manifest = json.loads((source / 'manifest.json').read_text())
checks_manifest = json.loads((root / 'checks-manifest.json').read_text())
checked = set()
with tarfile.open(root / 'checks.tar.gz') as archive:
    for member in archive.getmembers():
        if not member.isfile() or member.name not in checks_manifest or member.name in checked:
            raise ValueError('unexpected check archive member')
        data = archive.extractfile(member).read()
        identity = checks_manifest[member.name]
        if len(data) != identity['bytes'] or hashlib.sha256(data).hexdigest() != identity['sha256']:
            raise ValueError('check evidence identity')
        if member.name.endswith('/result.json'):
            checks = json.loads(data)
            if checks['status'] != 'PASS' or any(s['returncode'] != 0 for s in checks['suites']):
                raise ValueError('checks did not pass')
        checked.add(member.name)
if checked != set(checks_manifest):
    raise ValueError('missing check evidence')
with tempfile.TemporaryDirectory() as temporary, tarfile.open(source / 'raw.tar.gz') as archive:
    entries = {}
    for member in archive.getmembers():
        if member.name.startswith(prefix):
            name = member.name[len(prefix):]
            if name in expected['input_sha256']:
                if not member.isfile() or name in entries or Path(name).name != name:
                    raise ValueError('invalid or duplicate source member')
                data = archive.extractfile(member).read()
                digest = hashlib.sha256(data).hexdigest()
                if digest != expected['input_sha256'][name] or digest != manifest[member.name]['sha256']:
                    raise ValueError('source identity changed')
                entries[name] = data
                (Path(temporary) / name).write_bytes(data)
    if set(entries) != set(expected['input_sha256']):
        raise ValueError('missing source evidence')
    actual = summarize(temporary)
    if actual != expected:
        raise ValueError('timing report differs')
print(json.dumps({'status': 'PASS', 'calls': actual['call_count'],
                  'send_to_reply_total_ms': actual['send_to_reply_total_ms'],
                  'first_send_to_last_reply_ms': actual['first_send_to_last_reply_ms'],
                  'scope': actual['scope']}, indent=2))
