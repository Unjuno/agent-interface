"""Audit OpenTTD road-tool state across program and time boundaries."""
import hashlib
import json
from pathlib import Path

import audit_openttd_matched_v2 as shared

HERE = Path(__file__).resolve().parent
ROOT = HERE / 'results/openttd-tool-boundary-01'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    prereg = read(ROOT / 'preregistration.json')
    for name, digest in prereg['sources'].items():
        path = HERE.parent / name if name.startswith('openttd_task/') else HERE / name
        shared.source_with_hash(path, digest)
    overall = read(ROOT / 'result.json')
    assert overall['model_calls'] == 0 and overall['source_sha256'] == sha(HERE / 'probe_openttd_tool_boundary_v1.py')
    rows = []
    for spec in prereg['modes']:
        trial = ROOT / spec['mode']
        result = read(trial / 'result.json')
        evaluation = result['evaluation']
        assert result['mode'] == spec['mode'] and result['delay_seconds'] == spec['delay_seconds']
        assert evaluation['success'] is False and evaluation['checks']['forbidden_tiles_clear']
        events = [json.loads(line) for line in (trial / 'runtime/events.jsonl').read_text().splitlines()]
        assert len([e for e in events if e.get('event') == 'step_started' and e.get('operation') == 'pointer_drag']) == 1
        terminals = [e for e in events if e.get('event') == 'terminal']
        assert terminals and all(e['release']['verified'] and not e['release']['keys_down'] and not e['release']['buttons_down'] for e in terminals)
        target = [t['id'] for t in evaluation['observation']['tiles'] if t['id'] in prereg['target_tiles'] and t['road']]
        rows.append({'mode': spec['mode'], 'delay_seconds': spec['delay_seconds'], 'target_road_ids': target,
                     'changed_surrounding_tiles': evaluation['changed_surrounding_tiles'], 'durable_calls': result['durable_calls']})
    report = {'audit_passed': True, 'preregistered': True, 'episodes': rows, 'model_calls': 0,
              'same_effect': len({json.dumps([r['target_road_ids'], r['changed_surrounding_tiles']]) for r in rows}) == 1,
              'scope': prereg['scope'], 'audit_sha256': sha(Path(__file__))}
    (ROOT / 'audit.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
