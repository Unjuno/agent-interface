import hashlib
import json
import sys
from pathlib import Path


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    root = Path('/work/source')
    raw_path = Path('/work/raw/raw.json')
    raw_bytes = raw_path.read_bytes()
    raw = json.loads(raw_bytes)
    assert raw['schema'] == 'issue-3850-obstac-raw-v1'
    assert raw['source_commit'] == '4d51fccac55433570bc714cfaf21c88531fe325d'
    assert raw['formal'] is True
    assert len(raw['rows']) == 4
    expected = {
        'region_shape': 'observe x must be int',
        'width_height_shape': 'observe w must be int',
        'valid_program_backend_refusal': None,
        'unsupported_op_no_echo': 'unsupported operation',
    }
    errors = []
    for row in raw['rows']:
        name = row['case']
        result = row['returned']['result']
        if name not in expected:
            errors.append('unexpected_case:' + name)
            continue
        if row['dispatch_count'] != 1 or row['close_count'] != 1:
            errors.append('call_count:' + name)
        if row['backend_emissions'] != 0 or result.get('backend_emissions') != 0:
            errors.append('emission:' + name)
        if result.get('status') != 'refused' or result.get('error') != 'INVALID_PROGRAM':
            errors.append('refusal:' + name)
        if result.get('detail') != expected[name]:
            errors.append('detail:' + name)
        if (expected[name] is None) == ('detail_source' in result):
            errors.append('detail_source:' + name)
        if name == 'unsupported_op_no_echo' and 'untrusted-' in json.dumps(row):
            errors.append('untrusted_echo')
        if row['input_unchanged'] is not True:
            errors.append('input_mutated:' + name)
    if set(r['case'] for r in raw['rows']) != set(expected):
        errors.append('case_set')
    for rel, bound in raw['source_manifest'].items():
        data = (root / rel).read_bytes()
        if sha(data) != bound['sha256']:
            errors.append('source_sha256:' + rel)
        blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        if blob != bound['git_blob_sha']:
            errors.append('source_git_blob:' + rel)
    report = {'schema':'issue-3850-obstac-audit-v1',
              'classification':'PASS_SCOPED' if not errors else 'FAIL_AUDIT',
              'rows':len(raw['rows']), 'raw_sha256':sha(raw_bytes), 'errors':errors}
    out = Path('/work/audit')
    (out/'audit.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print(json.dumps(report,sort_keys=True))
    if errors:
        sys.exit(2)


if __name__ == '__main__':
    main()
