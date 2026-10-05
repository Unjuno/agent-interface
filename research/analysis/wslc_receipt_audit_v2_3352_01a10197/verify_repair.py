"""Raw-only repair-result checker; does not import or run either audit implementation."""
import hashlib
import json
from pathlib import Path

def verify(package: Path, matrix: dict) -> dict:
    pins = json.loads((package / 'SOURCE_PINS.json').read_text())
    source = package.parents[2] / pins['path']
    names = ['Dockerfile', 'payload.txt', 'probe.py', 'build.output.txt', 'run.output.txt', 'POSTRUN_CHECK.json', 'RUN.json']
    freeze = (source / 'AUDIT_FREEZE.md').read_text()
    for name, pin in pins['files'].items():
        data = (source / name).read_bytes()
        if not (len(data) == pin['bytes'] and hashlib.sha256(data).hexdigest() == pin['sha256']):
            raise ValueError(name)
        if name != 'AUDIT_FREEZE.md':
            if not f"`{pin['sha256']}`" in freeze:
                raise ValueError(name)
    expected = {'original', 'hash_run.output_inline'} | {'hash_' + n for n in names[3:]} | {'source_' + n for n in names[:3]} | {'missing_' + n for n in names} | {'image_build', 'image_postrun'}
    rows = matrix['rows']
    if not (len(rows) == len(expected) and {r['id'] for r in rows} == expected):
        raise ValueError('raw repair check failed')
    original_id = json.loads((source / 'POSTRUN_CHECK.json').read_text())['image_id']
    false_accepts = 0
    for row in rows:
        case = package / 'cases' / row['id']
        changed = []
        for name in names:
            path = case / name
            digest = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
            if not row['inputs'][name] == digest:
                raise ValueError('raw repair check failed')
            if digest != pins['files'][name]['sha256']:
                changed.append(name)
        if row['id'] == 'original':
            if not not changed:
                raise ValueError('raw repair check failed')
        elif row['id'] == 'hash_run.output_inline':
            if not changed == ['run.output.txt']:
                raise ValueError('raw repair check failed')
            if not (case / 'run.output.txt').read_bytes() == (source / 'run.output.txt').read_bytes().replace(b'{', b'{ ', 1):
                raise ValueError('raw repair check failed')
        elif row['id'].startswith(('hash_', 'source_', 'missing_')):
            name = row['id'].split('_', 1)[1]
            if not changed == [name]:
                raise ValueError('raw repair check failed')
            if row['id'].startswith('missing_'):
                if not not (case / name).exists():
                    raise ValueError('raw repair check failed')
            elif not (case / name).read_bytes() == (source / name).read_bytes() + b' ':
                raise ValueError('raw repair check failed')
        else:
            if not changed == ['RUN.json']:
                raise ValueError('raw repair check failed')
            actual = json.loads((case / 'RUN.json').read_text())
            wanted = json.loads((source / 'RUN.json').read_text())
            section, key = ('build', 'result_image_id') if row['id'] == 'image_build' else ('postrun_check', 'image_id')
            if not actual[section][key] != original_id:
                raise ValueError('raw repair check failed')
            actual[section][key] = original_id
            if not actual == wanted:
                raise ValueError('raw repair check failed')
        for version, receipt in row['audits'].items():
            if not version in ('legacy', 'v2'):
                raise ValueError('raw repair check failed')
            if not type(receipt['exit_code']) is int:
                raise ValueError('raw repair check failed')
            if not receipt['ended_utc'] >= receipt['started_utc']:
                raise ValueError('raw repair check failed')
            if not (type(receipt['pid']) is int and receipt['pid'] > 0):
                raise ValueError('raw repair check failed')
            if not receipt['stderr'] == '':
                raise ValueError('raw repair check failed')
            parsed = json.loads(receipt['stdout'])
            if version == 'v2':
                if not receipt['exit_code'] == (0 if row['id'] == 'original' else 1):
                    raise ValueError('raw repair check failed')
                if not parsed['status'] == ('PASS_RETAINED_RECEIPT_V2_ENGINEERING' if row['id'] == 'original' else 'STOP_RETAINED_RECEIPT_V2_INVALID'):
                    raise ValueError('raw repair check failed')
                if row['id'] == 'original':
                    if not parsed['frozen_inputs_checked'] == 7:
                        raise ValueError('raw repair check failed')
            else:
                if not (row['id'] == 'original' or row['id'].startswith('hash_') or row['id'].startswith('image_')):
                    raise ValueError('raw repair check failed')
                if row['id'] == 'hash_run.output.txt':
                    if not (receipt['exit_code'] == 1 and parsed['status'] == 'STOP_T0_RECEIPT_INVALID'):
                        raise ValueError('raw repair check failed')
                else:
                    if not (receipt['exit_code'] == 0 and parsed['status'] == 'PASS_T0_RECEIPT_AUDITED'):
                        raise ValueError('raw repair check failed')
                    false_accepts += row['id'] != 'original'
        if not 'v2' in row['audits']:
            raise ValueError('raw repair check failed')
        if not ('legacy' in row['audits']) == (row['id'] == 'original' or row['id'].startswith(('hash_', 'image_'))):
            raise ValueError('raw repair check failed')
    if not false_accepts == 6:
        raise ValueError('raw repair check failed')
    return {'status': 'PASS_SAVED_DATA_REPAIR_SCOPED', 'rows': len(rows), 'legacy_false_accepts': false_accepts, 'v2_negative_rejections': len(rows) - 1, 'candidate_imported': False}
if __name__ == '__main__':
    p = Path(__file__).resolve().parent
    matrix = json.loads((p / 'matrix.json').read_text())
    matrix['rows'].append(json.loads((p / 'additional_case.json').read_text()))
    print(json.dumps(verify(p, matrix), sort_keys=True))
