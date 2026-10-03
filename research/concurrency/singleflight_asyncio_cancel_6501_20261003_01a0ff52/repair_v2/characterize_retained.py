"""Ordinary retained-data repair check; no candidate/asyncio/runtime import."""
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import subprocess
import sys

from audit_v2 import check
from mutations import mutations

ROOT = Path(__file__).resolve().parent
PARENT = ROOT.parent


def load_v1():
    spec = importlib.util.spec_from_file_location('retained_v1_auditor', PARENT / 'audit.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    freeze = json.loads((ROOT / 'FREEZE.json').read_bytes())
    for filename, digest in freeze['source_sha256'].items():
        if hashlib.sha256((ROOT / filename).read_bytes()).hexdigest() != digest:
            raise ValueError('v2 source mismatch: ' + filename)
    checked = []
    for line in (PARENT / 'SHA256SUMS').read_text().splitlines():
        digest, filename = line.split(None, 1)
        filename = filename.strip()
        if hashlib.sha256((PARENT / filename).read_bytes()).hexdigest() != digest:
            raise ValueError('original manifest mismatch: ' + filename)
        checked.append(filename)
    blob = (PARENT / 'execution/raw.json').read_bytes()
    digest = hashlib.sha256(blob).hexdigest()
    if digest != freeze['original_raw_sha256'] or len(checked) != 27:
        raise ValueError('original identity mismatch')
    raw = json.loads(blob)
    v1 = load_v1()
    cases = []
    for name, altered in mutations(raw):
        encoded = json.dumps(altered, sort_keys=True, separators=(',', ':')).encode()
        cases.append({'name': name, 'variant_sha256': hashlib.sha256(encoded).hexdigest(),
                      'v1_errors': v1.check(altered), 'v2_errors': check(altered)})
    result = {'status': 'PASS_RETAINED_TRACE_V2_SCOPED' if not check(raw)
              and len(cases) == 25 and all(c['v2_errors'] for c in cases)
              and all(not c['v1_errors'] for c in cases[:7]) else 'FAIL_REPAIR_CHECK',
              'raw_sha256': digest, 'original_manifest_files': len(checked),
              'original_v1_errors': v1.check(raw), 'original_v2_errors': check(raw),
              'rows': len(raw['rows']), 'caller_outcomes': sum(len(r['outcomes']) for r in raw['rows']),
              'controls': cases, 'python': platform.python_version(), 'platform': platform.platform(),
              'started_utc': started, 'ended_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'source_sha256': freeze['source_sha256'],
              'characterizer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'source_freeze_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip(),
              'candidate_invocations': 0, 'v2_audit_kind': 'ordinary-retained-data-engineering-check'}
    output = ROOT / 'execution/controls.json'
    with output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
        stream.write('\n')
    print(json.dumps({'status': result['status'], 'rows': result['rows'], 'caller_outcomes': result['caller_outcomes'],
                      'reviewer_controls_v1_accepted': sum(not c['v1_errors'] for c in cases[:7]),
                      'v2_controls_rejected': sum(bool(c['v2_errors']) for c in cases)}))
    return int(result['status'] != 'PASS_RETAINED_TRACE_V2_SCOPED')


if __name__ == '__main__':
    raise SystemExit(main())
