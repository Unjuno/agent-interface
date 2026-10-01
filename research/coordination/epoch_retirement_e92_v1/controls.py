"""Effective, well-formed record changes; preserve originals and mutation inputs."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
from audit import audit


def change_reader(record: dict, field: str) -> None:
    output = json.loads(record['reader']['stdout'])
    if field == 'old':
        output['probes'][0]['reason'] = 'ELIGIBLE'
    elif field == 'future':
        output['probes'][3]['reason'] = 'ELIGIBLE'
    elif field == 'authority':
        output['authority_granted'] = True
    elif field == 'history':
        output['excluded'] = []
    record['reader']['stdout'] = json.dumps(output, sort_keys=True) + '\n'


def run(source: Path, root: Path, indices: list[int], phase: str, out: Path) -> dict:
    baseline = audit(source, root, indices, phase)
    if baseline['errors']:
        raise RuntimeError('baseline must pass before copied-evidence controls')
    out.mkdir(parents=True, exist_ok=False)
    names = ('identity', 'phase', 'writer_exit', 'fresh_pid', 'old', 'future',
             'authority', 'history', 'snapshot', 'commit_log', 'argv', 'completion')
    summary = []
    for name in names:
        case = '2-FENCE_FIRST-0' if name in ('writer_exit', 'commit_log') else '0-FENCE_FIRST-0'
        original = (root / (case + '.json')).read_bytes()
        record = json.loads(original)
        if name == 'identity':
            record['id'] = 'not-the-same-case'
        elif name == 'phase':
            record['phase'] = 'not-' + phase
        elif name == 'writer_exit':
            record['writer']['exit'] = 0
        elif name == 'fresh_pid':
            record['reader']['pid'] = record['writer']['pid']
        elif name in ('old', 'future', 'authority', 'history'):
            change_reader(record, name)
        elif name == 'snapshot':
            other = json.loads((root / '4-FENCE_FIRST-0.json').read_text())
            record['after_reopen'] = copy.deepcopy(other['after_reopen'])
        elif name == 'commit_log':
            lines = [json.loads(x) for x in record['writer']['stdout'].splitlines()]
            lines = [x for x in lines if not (x['kind'] == 'sql' and x['sql'] == 'COMMIT')]
            record['writer']['stdout'] = ''.join(json.dumps(x, sort_keys=True) + '\n' for x in lines)
        elif name == 'argv':
            record['reader']['argv'][4] = 'writer'
        elif name == 'completion':
            record['writer']['stdout'] += '{"kind":"maintenance_complete"}\n'
        changed = (json.dumps(record, sort_keys=True, separators=(',', ':')) + '\n').encode()
        effective = json.loads(original) != record
        (out / (name + '.case.json')).write_bytes(changed)
        with tempfile.TemporaryDirectory(prefix='e92-controls-') as temporary:
            copied = Path(temporary)
            for item in root.glob('*.json'):
                shutil.copyfile(item, copied / item.name)
            (copied / (case + '.json')).write_bytes(changed)
            result = audit(source, copied, indices, phase)
        (out / (name + '.audit.json')).write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
        rejected = bool(result['errors']) and not any(':invalid_record:' in x for x in result['errors'])
        summary.append({'name': name, 'case': case, 'effective': effective, 'rejected': rejected,
                        'original_sha256': hashlib.sha256(original).hexdigest(),
                        'changed_sha256': hashlib.sha256(changed).hexdigest(), 'errors': result['errors']})
    result = {'passed': all(x['effective'] and x['rejected'] for x in summary), 'controls': summary}
    (out / 'SUMMARY.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    return result


if __name__ == '__main__':
    result = run(Path(sys.argv[1]), Path(sys.argv[2]), [int(x) for x in sys.argv[3].split(',')],
                 sys.argv[4], Path(sys.argv[5]))
    print(json.dumps({'passed': result['passed'], 'controls': len(result['controls'])}, sort_keys=True))
    raise SystemExit(not result['passed'])
