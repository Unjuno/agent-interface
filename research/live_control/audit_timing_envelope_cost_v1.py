"""Audit synchronous v1 versus buffered v2 record-cost measurements."""
import hashlib
import json
import statistics
from pathlib import Path


H = Path(__file__).resolve().parent
cases = [
    ('windows-v1', H / 'results/timing-envelope-cost-windows-01', 'v1'),
    ('linux-v1', H / 'results/timing-envelope-cost-linux-01', 'v1'),
    ('windows-v2', H / 'results/timing-envelope-v2-cost-windows-01', 'v2'),
    ('linux-v2', H / 'results/timing-envelope-v2-cost-linux-01', 'v2'),
]


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


rows = {}
for name, root, version in cases:
    plan = read(root / 'plan.json')
    for source, digest in plan['sources'].items():
        assert sha(H / source) == digest
    samples = read(root / 'samples.json')
    result = read(root / 'result.json')
    assert len(samples) == result['samples'] == plan['samples'] == 200
    ordered = sorted(samples)
    if version == 'v1':
        assert result['median_us'] == statistics.median(samples) / 1000
        assert result['p95_us'] == ordered[189] / 1000
        assert result['total_ms'] == sum(samples) / 1e6
        median = result['median_us']
    else:
        assert result['record_median_us'] == statistics.median(samples) / 1000
        assert result['record_p95_us'] == ordered[189] / 1000
        assert result['record_total_ms'] == sum(samples) / 1e6
        assert result['single_close_fsync_ms'] >= 0
        median = result['record_median_us']
    rows[name] = {'median_us': median,
                  'p95_us': result.get('p95_us', result.get('record_p95_us')),
                  'total_ms': result.get('total_ms', result.get('record_total_ms'))}

report = {
    'rows': rows,
    'windows_record_median_ratio_v1_over_v2':
        rows['windows-v1']['median_us'] / rows['windows-v2']['median_us'],
    'linux_record_median_ratio_v1_over_v2':
        rows['linux-v1']['median_us'] / rows['linux-v2']['median_us'],
    'decision': 'reject per-event fsync from critical path; use buffered v2 candidate',
    'limits': ('isolated 200-record runs on different durability semantics; '
               'not paired randomized trials or measured application slowdown; '
               'v2 can lose buffered timing records before close'),
}
(H / 'results/timing-envelope-cost-audit-01.json').write_text(
    json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
