"""Check the frozen revision and retained first controls without producer replay."""
import hashlib
import json
from pathlib import Path
import auditor

ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT.parent

def sha(data):
    return hashlib.sha256(data).hexdigest()

def require(condition, message):
    if not condition:
        raise ValueError(message)

def main():
    frozen = json.loads((ROOT / 'FREEZE.json').read_text())
    for name, record in frozen['files'].items():
        data = (PACKAGE / name).read_bytes()
        require(len(data) == record['bytes'] and sha(data) == record['sha256'], 'frozen bytes: ' + name)
    for line in (PACKAGE / 'SHA256SUMS').read_text().splitlines():
        digest, name = line.split('  ', 1)
        require(sha((PACKAGE / name).read_bytes()) == digest, 'original manifest: ' + name)
    for label in ('baseline', 'combined', 'controls'):
        directory = ROOT / 'execution' / label
        receipt = json.loads((directory / 'receipt.json').read_text())
        require(receipt['returncode'] == 0, 'first exit: ' + label)
        for channel, record in receipt['logs'].items():
            data = (directory / (channel + '.txt')).read_bytes()
            require(sha(data) == record['sha256'] and len(data) == record['bytes'], 'log identity')
    for arm, wanted in (('baseline', 2164), ('combined', 0)):
        data = (PACKAGE / 'evidence' / (arm + '.jsonl')).read_bytes()
        result = auditor.check([json.loads(line) for line in data.decode().splitlines()], arm)
        retained = json.loads((ROOT / 'execution' / arm / 'stdout.txt').read_text())
        require(result['rows'] == 3072 and not result['errors'] and result['identity_error_count'] == 0
            and result['mismatch_count'] == wanted, 'raw audit')
        require(all(retained[k] == value for k, value in result.items())
            and retained['raw_sha256'] == sha(data), 'retained audit identity')
    raw = (PACKAGE / 'evidence/combined.jsonl').read_bytes()
    lines = raw.splitlines(keepends=True)
    controls = json.loads((ROOT / 'controls-result.json').read_text())
    require(controls['control_count'] == 16 and len(controls['controls']) == 16
        and controls['first_four_v1_accept'] and controls['all_v2_reject'], 'control result')
    require(controls['original_raw_sha256'] == sha(raw), 'original control binding')
    names = set()
    for ordinal, record in enumerate(controls['controls']):
        require(record['control'] not in names, 'duplicate control')
        names.add(record['control'])
        row_number = record['ordinal']
        original, changed = record['original_row'], record['changed_row']
        original_data = lines[row_number]
        changed_data = (json.dumps(changed, sort_keys=True, allow_nan=False) + '\n').encode()
        require(auditor.same_json(json.loads(original_data), original), 'original witness')
        require(sha(original_data) == record['original_row_sha256']
            and sha(changed_data) == record['changed_row_sha256'], 'row hashes')
        require(sha(b''.join(lines[:row_number] + lines[row_number+1:])) == record['unchanged_other_rows_sha256']
            and sha(b''.join(lines[:row_number] + [changed_data] + lines[row_number+1:]))
            == record['changed_full_copy_sha256'], 'copied raw binding')
        require(auditor.identity_errors(changed) and record['v2_rejected']
            and record['identity_error_count'] == 1, 'changed row refusal')
        if ordinal < 4:
            require(record['v1_passed'] is True, 'first v1 escape')
    print(json.dumps({'original_manifest_hashes': 115, 'frozen_inputs': len(frozen['files']),
        'raw_rows': 6144, 'controls': len(names), 'original_raw_unchanged': True,
        'disposition': 'PASS_TYPED_RAW_IDENTITY_SCOPED'}, sort_keys=True))

if __name__ == '__main__':
    main()
