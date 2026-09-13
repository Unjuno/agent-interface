"""Correct the frozen calibration audit's summary-versus-full evaluation comparison."""
import hashlib
import json
from pathlib import Path

import audit_openttd_matched_v2 as shared

HERE = Path(__file__).resolve().parent
ROOT = HERE / 'results/openttd-drag-calibration-02'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    prereg = read(ROOT / 'preregistration.json')
    assert prereg['status'] == 'PREREGISTERED_BEFORE_EXECUTION'
    for name, digest in prereg['sources'].items():
        path = HERE.parent / name if name.startswith('openttd_task/') else HERE / name
        shared.source_with_hash(path, digest)
    overall = read(ROOT / 'result.json')
    assert overall['model_calls'] == 0
    assert overall['source_sha256'] == sha(HERE / 'probe_openttd_drag_calibration_v2.py')
    rows = []
    for offset in prereg['offsets_y']:
        trial = ROOT / f'offset-{offset:+03d}'
        result = read(trial / 'result.json')
        calls = read(trial / 'calls.json')
        assert result['offset_y'] == offset and result['model_calls'] == 0 and result['durable_calls'] == 4
        assert [c['request']['command']['op'] for c in calls] == ['clock', 'submit', 'clock', 'submit']
        expected = [
            {'op': 'pointer_click', 'x': 820, 'y': 51},
            {'op': 'pointer_click', 'x': 709, 'y': 90},
            {'op': 'pointer_drag', 'points': result['points'], 'duration_ms': 600},
            {'op': 'observe'},
        ]
        assert result['steps'] == expected and calls[3]['request']['command']['steps'] == expected
        summary = result['evaluation']
        evaluation = read(trial / 'runtime/evaluation.json')
        for field in ('success', 'checks', 'changed_surrounding_tiles', 'contract'):
            assert summary[field] == evaluation[field]
        assert evaluation['success'] is False and evaluation['checks']['forbidden_tiles_clear'] is True
        events = [json.loads(line) for line in (trial / 'runtime/events.jsonl').read_text().splitlines()]
        assert len([e for e in events if e.get('event') == 'step_started' and e.get('operation') == 'pointer_drag']) == 1
        terminals = [e for e in events if e.get('event') == 'terminal']
        assert terminals and all(e['release']['verified'] and not e['release']['keys_down'] and not e['release']['buttons_down'] for e in terminals)
        assert read(trial / 'runtime/cleanup.json')['all_owned_processes_exited'] and result['save_unchanged']
        observed = evaluation['observation']['tiles']
        rows.append({'offset_y': offset, 'points': result['points'],
                     'target_road_ids': [t['id'] for t in observed if t['id'] in prereg['target_tiles'] and t['road']],
                     'changed_surrounding_tiles': evaluation['changed_surrounding_tiles'],
                     'checks': evaluation['checks']})
    report = {'audit_passed': True, 'preregistered': True, 'episodes': rows,
              'model_calls': 0, 'task_input_calls': len(rows),
              'frozen_audit_failure': 'v2 audit compared summarized finish event to full runtime evaluation object',
              'scope': prereg['scope'], 'audit_sha256': sha(Path(__file__))}
    (ROOT / 'audit.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
