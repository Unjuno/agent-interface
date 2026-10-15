"""Independent raw-only audit: never imports the CLI or its projection code."""
import argparse
import json
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def audit(folder):
    summary = json.loads((folder / 'SUMMARY.json').read_text())
    expected_names = {f'v{v}-{m}-{s}' for v in (10, 15) for m in ('full', 'compact')
                      for s in ('healthy', 'broken')}
    require({r['case'] for r in summary['cases']} == expected_names and len(summary['cases']) == 8,
            'incomplete/duplicate case matrix')
    findings = []
    for name in sorted(expected_names):
        path = folder / name
        raw, selected, received, flush = (read(path / filename) for filename in (
            'events.jsonl', 'delivered.jsonl', 'captured-stdout.jsonl', 'delivery-flush.jsonl'))
        require([r['event'] for r in raw] == ['ready', 'step_started', 'observation', 'observation',
                'critical_signal', 'observation', 'settle_result', 'terminal', 'command',
                'independent_evaluation'], name + ': raw trace changed')
        require(raw[3]['synthetic_visual'] == 'warning' and raw[4]['token'] == 'explicit-negative-event',
                name + ': missing negative controls')
        expected = [raw[i] for i in (0, 2, 4, 5, 6, 7, 8, 9)] if '-compact-' in name else raw
        plain = [{k: v for k, v in row.items() if k not in ('delivery_id', 'review')} for row in selected]
        require(plain == expected, name + ': selected output disagrees with contract')
        broken = name.endswith('broken')
        require(received == ([] if broken else selected), name + ': stdout disagreement')
        v15 = name.startswith('v15-')
        if v15 and not broken:
            require(len(flush) == len(selected), name + ': missing flush receipt')
            for item, receipt in zip(selected, flush):
                require(receipt['delivery_id'] == item['delivery_id'], name + ': wrong flush association')
                require(receipt['utf8_bytes'] == len((json.dumps(item) + '\n').encode('utf-8')),
                        name + ': wrong byte count')
                require(receipt['started_ns'] <= receipt['flushed_ns'], name + ': reversed flush times')
        else:
            require(not flush, name + ': unexpected successful flush receipt')
        require(raw[-1]['synthetic'] is True and raw[-1]['success'] is False,
                name + ': synthetic fixture mislabeled as task success')
        findings.append(dict(case=name, raw_records=len(raw), selected_records=len(selected),
                             stdout_records=len(received), successful_flush_receipts=len(flush)))
    return dict(status='PASS_SCOPED_RAW_AUDIT', cases=findings,
                scope='synthetic CLI output only; no GUI, real Executor, task effect or model receipt')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('folder', type=Path)
    args = parser.parse_args()
    result = audit(args.folder)
    (args.folder / 'AUDIT.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
