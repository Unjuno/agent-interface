"""Recorded success/interruption/stale cases and exceptional event surfacing."""
import copy
import json
from pathlib import Path
from decision_receipt_v1 import build
from report_pages_v2 import digest

HERE = Path(__file__).resolve().parent


def main():
    paths = [HERE / 'results/paged-live-01/move/original-report.json',
             HERE / 'results/recovery-pair1-01/B/move/move-save-report.json',
             HERE / 'results/recovery-pair3-01/B/prepare/stale-right-report.json']
    rows = []
    for path in paths:
        data = path.read_bytes()
        receipt = build(data)
        report = json.loads(data)
        indexed = [p for group in receipt['event_index'].values() for p in group['paths']]
        assert len(indexed) == sum(len(e.get('reply', {}).get('records', [])) for e in report['exchanges'])
        for ref in indexed:
            value = report
            for key in ref:
                value = value[key]
            assert value['event'] in receipt['event_index']
        assert receipt['source']['sha256'] == digest(data)
        if 'recovery-pair' in str(path):
            assert receipt['detail_review_required']
        rows.append({'path': str(path.relative_to(HERE)), 'source_bytes': len(data),
                     'receipt_bytes': len(json.dumps(receipt).encode()), 'receipt': receipt})
    base = json.loads(paths[0].read_bytes())
    mutations = [{'event': 'future_event', 'critical': True},
                 {'event': 'observation', 'future_critical_field': True},
                 {'event': 'observation', 'error': 'capture failed'},
                 {'event': 'observation', 'focus_samples_match': False}]
    for event in mutations:
        changed = copy.deepcopy(base)
        changed['exchanges'][-1]['reply']['records'].append(event)
        changed['exchanges'][-1]['reply']['cursor'] += 1
        receipt = build(json.dumps(changed).encode())
        assert receipt['detail_review_required'] and receipt['attention']
    result = {'sources': {p.name: digest(p.read_bytes()) for p in (Path(__file__), HERE / 'decision_receipt_v1.py')},
              'cases': rows, 'injected_exception_cases': len(mutations),
              'scope': 'Offline index and explicit exceptions; not full schema validation or permission to act.'}
    out = HERE / 'results/decision-receipt-01'
    out.mkdir(exist_ok=True)
    (out / 'report.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'cases': [{k: v for k, v in r.items() if k != 'receipt'} for r in rows], 'injected_exception_cases': len(mutations)}, indent=2))


if __name__ == '__main__':
    main()
