"""Read-only evidence integrity verification; no producer/reference execution."""
import gzip
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
digest = lambda data: hashlib.sha256(data).hexdigest()
freeze = json.loads((root/'FREEZE.json').read_bytes())
for name, expected in freeze['source_sha256'].items():
    if digest((root/name).read_bytes()) != expected:
        raise SystemExit('source mismatch: '+name)
run = json.loads((root/'run_01/RUN.json').read_bytes())
if digest((root/'FREEZE.json').read_bytes()) != run['freeze_sha256']:
    raise SystemExit('freeze binding mismatch')
archive = json.loads((root/'run_01/ARCHIVE.json').read_bytes())
compressed = (root/'run_01/raw.jsonl.gz').read_bytes()
raw = gzip.decompress(compressed)
if digest(compressed)!=archive['gzip_sha256'] or len(compressed)!=archive['gzip_bytes']:
    raise SystemExit('compressed bytes mismatch')
if digest(raw)!=archive['raw_sha256'] or len(raw)!=archive['raw_bytes']:
    raise SystemExit('decompressed bytes mismatch')
for name, expected in run['output_sha256'].items():
    data = raw if name=='raw.jsonl' else (root/'run_01'/name).read_bytes()
    if digest(data)!=expected:
        raise SystemExit('original output mismatch: '+name)
audit = json.loads((root/'run_01/audit.json').read_bytes())
if audit['raw_sha256'] != digest(raw) or audit['rows']!=6561:
    raise SystemExit('audit binding mismatch')
if (run['candidate_invocations'],run['auditor_invocations'],run['retries']) != (1,1,0):
    raise SystemExit('invocation record mismatch')
if run['candidate']['exit_code'] or run['auditor']['exit_code']:
    raise SystemExit('recorded invocation failure')
print('PASS saved-source, freeze, archive, original-output and audit identity; producer/reference invocations=0')
