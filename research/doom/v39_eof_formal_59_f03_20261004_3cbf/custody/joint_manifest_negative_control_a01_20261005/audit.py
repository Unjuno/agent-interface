from __future__ import annotations
import hashlib, json, re, sys
from pathlib import Path

root = Path(sys.argv[1])
manifest = root / 'SOURCE_SHA256SUMS.txt'
entries = {}
for line in manifest.read_text(encoding='utf-8').splitlines():
    digest, name = line.split('  ', 1)
    entries[name.replace('\\', '/')] = digest
checks = []
for line in (root / 'SHA256SUMS').read_text(encoding='utf-8').splitlines():
    digest, name = line.split('  ', 1)
    got = hashlib.sha256((root / name).read_bytes()).hexdigest()
    checks.append((name, digest == got))
assert checks and all(ok for _, ok in checks), checks
assert entries['f03-formal-freeze-6d8387caa8.tar'] == hashlib.sha256((root.parent / 'f03-formal-freeze-6d8387caa8.tar').read_bytes()).hexdigest()
raw = (root / 'TEST_OUTPUT.txt').read_text(encoding='utf-8')
assert 'Ran 5 tests' in raw and raw.rstrip().endswith('OK')
assert (root / 'test-exit-code.txt').read_text() == '0'
report = (root / 'REPORT.md').read_text(encoding='utf-8')
assert 'remains HOLD' in report and 'does not prove' in report
print(json.dumps({'status':'PASS_A01_EVIDENCE_AUDIT','manifest_entries':len(checks),'manifest_mismatches':0,'source_manifest_entries':len(entries),'test_count':5,'exit_code':0,'scope_limit_present':True}, indent=2))
