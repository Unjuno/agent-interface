"""Re-audit saved Calc blocks and summarize task and launcher intervals.

This reads existing archives; it does not run Calc or a model.  Use normal
Python because the archived auditors deliberately use assertions.
"""
import argparse
import json
from pathlib import Path
import statistics
import subprocess
import sys

if not __debug__:
    raise RuntimeError('archived audits require normal Python, not -O')

parser = argparse.ArgumentParser()
parser.add_argument('integration_root', type=Path,
                    help='directory containing the four archived block directories')
args = parser.parse_args()
blocks = {
    'fixed': 'wslc_calc_three_arm_reverse_20261101',
    'temporary_obstruction': 'wslc_calc_three_arm_obstruction_reverse_20261101',
}
output = {}
for label, folder in blocks.items():
    comparison = args.integration_root / folder / 'compare.py'
    audited = json.loads(subprocess.check_output([sys.executable, str(comparison)]))
    if audited.get('status') != 'audited':
        raise RuntimeError('archived block audit did not complete: ' + label)
    routes = {}
    for name in ('direct', 'compiled', 'fresh'):
        rows = [row for row in audited['trials'] if row['route'] == name]
        if len(rows) != 2:
            raise RuntimeError('expected two archived samples for ' + label + '/' + name)
        routes[name] = {
            'n': len(rows),
            'task_seconds_median': statistics.median(row['task_seconds'] for row in rows),
            'launcher_seconds_median': statistics.median(row['launcher_seconds'] for row in rows),
            'input_tokens_median': statistics.median(row['input_tokens'] for row in rows),
            'output_tokens_median': statistics.median(row['output_tokens'] for row in rows),
            'model_calls': [row['calls'] for row in rows],
            'samples': rows,
        }
    compiled, fresh = routes['compiled'], routes['fresh']
    output[label] = {
        'routes': routes,
        'compiled_vs_fresh': {
            'task_interval_reduction_fraction': 1 - compiled['task_seconds_median'] / fresh['task_seconds_median'],
            'launcher_interval_reduction_fraction': 1 - compiled['launcher_seconds_median'] / fresh['launcher_seconds_median'],
            'input_token_reduction_fraction': 1 - compiled['input_tokens_median'] / fresh['input_tokens_median'],
        },
    }
print(json.dumps({'status':'audited', 'blocks':output}, indent=2))
