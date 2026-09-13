"""Recorded bindings and contradictory/missing/nested evidence mutations."""
import copy
import json
from pathlib import Path
from decision_receipt_v2 import build
from report_pages_v2 import digest

HERE = Path(__file__).resolve().parent


def main():
    paths = ['results/paged-live-01/move/original-report.json',
             'results/recovery-pair1-01/B/move/move-save-report.json',
             'results/recovery-pair3-01/B/prepare/stale-right-report.json']
    rows = []
    for name in paths:
        result = build((HERE / name).read_bytes())
        rows.append({'source': name, 'binding_present': result['program_binding'] is not None,
                     'detail_review_required': result['detail_review_required']})
    assert rows[0]['binding_present'] and not rows[0]['detail_review_required']
    assert rows[1]['binding_present'] and rows[1]['detail_review_required']
    assert not rows[2]['binding_present'] and rows[2]['detail_review_required']
    base = json.loads((HERE / paths[0]).read_bytes())
    changes = [(['terminal', 'id'], 'wrong'),
               (['exchanges', 1, 'request', 'request_id'], 'stale'),
               (['exchanges', 1, 'request', 'command', 'expected_sequence'], 99),
               (['exchanges', 1, 'reply', 'records', -1, 'id'], 'wrong'),
               (['exchanges', 1, 'reply', 'records', 1, 'id'], 'wrong'),
               (['continuation_batch'], None),
               (['exchanges', 1, 'reply', 'status'], 'timeout'),
               (['source_image', 'sequence'], 999)]
    for path, value in changes:
        item = copy.deepcopy(base)
        target = item
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value
        result = build(json.dumps(item).encode())
        assert result['program_binding'] is None and result['detail_review_required'], path
    nested = copy.deepcopy(base)
    nested['source_image']['diagnostics'] = {'error': 'decoder failure'}
    result = build(json.dumps(nested).encode())
    assert result['detail_review_required']
    assert any(a['path'] == ['source_image', 'diagnostics', 'error'] for a in result['attention'])
    out = HERE / 'results/decision-receipt-v2-01'
    out.mkdir(exist_ok=True)
    summary = {'sources': {p.name: digest(p.read_bytes()) for p in (Path(__file__), HERE / 'decision_receipt_v1.py', HERE / 'decision_receipt_v2.py')},
               'recorded': rows, 'binding_mutations_rejected': len(changes), 'nested_error_surfaced': True,
               'scope': 'Offline recorded consistency; no live integration or input authority.'}
    (out / 'report.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
