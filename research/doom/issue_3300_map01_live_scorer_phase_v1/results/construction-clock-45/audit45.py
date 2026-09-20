from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path


def audit(path: Path) -> dict:
    rows = [json.loads(line) for line in path.read_text().splitlines() if line]
    errors = []
    reports = []
    for row in rows:
        records = row.get('tic_entry_records', [])
        api_reads = row.get('passive_reads', [])
        getters = row.get('scorer_getter_trace', [])
        source_ns = [record[1] for record in records]
        viz_time = [record[3] for record in records]
        periods = [b - a for a, b in zip(source_ns, source_ns[1:])]
        api_tics = [item['episode_tic'] for item in api_reads if item.get('status') == 'ok']
        tic_getters = [event for event in getters if event['name'] == 'get_episode_time']
        passive_duration = api_reads[-1]['start_ns'] - api_reads[0]['start_ns'] if api_reads else 0
        trace_overlap = max(0, min(api_reads[-1]['start_ns'], source_ns[-1]) - max(api_reads[0]['start_ns'], source_ns[0])) if source_ns and api_reads else 0
        expected = [
            ('setup_status', row.get('setup_status') == 'ok'),
            ('scorer_returned', row.get('scorer_status') == 'returned'),
            ('cleanup', row.get('cleanup', {}).get('game_closed') is True),
            ('contiguous_source_viz_time', len(viz_time) >= 2 and all(b - a == 1 for a, b in zip(viz_time, viz_time[1:]))),
            ('passive_api_static_tic_1', len(api_tics) >= 100 and set(api_tics) == {1}),
            ('exact_one_coherent_attempt', len(getters) == 8 and len(tic_getters) == 2 and [e.get('result') for e in tic_getters] == [1, 1]),
            ('source_trace_overlaps_at_least_98pct_passive_window', passive_duration > 0 and trace_overlap / passive_duration >= 0.98),
        ]
        for name, passed in expected:
            if not passed:
                errors.append({'index': row.get('index'), 'check': name})
        reports.append({
            'index': row.get('index'), 'api_reads': len(api_tics),
            'api_tic_unique': sorted(set(api_tics)), 'engine_records': len(records),
            'engine_viz_time_range': [min(viz_time), max(viz_time)] if viz_time else None,
            'engine_viz_time_contiguous': bool(viz_time) and all(b-a == 1 for a, b in zip(viz_time, viz_time[1:])),
            'engine_median_period_ns': int(statistics.median(periods)) if periods else None,
            'engine_median_hz': 1e9 / statistics.median(periods) if periods else None,
            'scorer_getter_count': len(getters), 'scorer_tic_values': [event.get('result') for event in tic_getters],
            'scorer_start_after_last_entry_sample_ns': getters[0]['start_ns'] - source_ns[-1] if getters and source_ns else None,
            'source_trace_passive_overlap_ns': trace_overlap,
            'passive_window_ns': passive_duration,
            'source_trace_passive_overlap_fraction': trace_overlap / passive_duration if passive_duration else None,
            'phase_interval_identified': False,
            'cleanup': row.get('cleanup'), 'checks': {name: passed for name, passed in expected},
        })
    result = {
        'schema': 'issue3453-construction-clock45-independent-audit-v1',
        'input': str(path), 'rows': len(rows), 'errors': errors,
        'decision': 'PASS_CONSTRUCTION_ONLY_ENGINE_PROGRESS_API_TIC_STALE' if rows and not errors else 'FAIL_AUDIT',
        'formal_allocation': False, 'reports': reports,
        'limitations': [
            'VIZ_Tic source sampling is instrumented and function-entry latency is unbounded.',
            'The exact scorer phase is not reconstructed: its final getter occurs after the final captured tic-entry sample, with no following edge.',
            'Three construction sessions do not fill or authorize the frozen 120-row allocation.',
        ],
    }
    return result


if __name__ == '__main__':
    report = audit(Path(sys.argv[1]))
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(bool(report['errors']))
