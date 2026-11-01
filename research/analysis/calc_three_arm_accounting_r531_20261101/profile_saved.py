"""Read archived model-runner durations after re-auditing the Calc blocks."""
import argparse
import json
from pathlib import Path
import statistics
import subprocess
import sys
import zipfile

if not __debug__:
    raise RuntimeError('archived audits require normal Python, not -O')

parser = argparse.ArgumentParser()
parser.add_argument('integration_root', type=Path)
root = parser.parse_args().integration_root
blocks = {
    'fixed': ('wslc_calc_three_arm_20261101', 'wslc_calc_three_arm_reverse_20261101'),
    'temporary_obstruction': ('wslc_calc_three_arm_obstruction_20261101',
                              'wslc_calc_three_arm_obstruction_reverse_20261101'),
}
output = {}
for label, (forward, reverse) in blocks.items():
    audited = json.loads(subprocess.check_output([sys.executable, str(root/reverse/'compare.py')]))
    if audited.get('status') != 'audited':
        raise RuntimeError('block audit failed: '+label)
    samples = []
    for row in audited['trials']:
        allocation = row['allocation']
        folder = forward if allocation.startswith(('eo', 'eq')) else reverse
        with zipfile.ZipFile(root/folder/'raw.zip') as archive:
            conditions = json.loads(archive.read(allocation+'/conditions.json').decode('utf-8-sig'))
            responses = [json.loads(archive.read(f'{allocation}/exchange/response-{i}.json'))
                         for i in range(1, row['calls']+1)]
        durations = [response.get('runner_ns') for response in responses]
        if any(type(value) is not int or value <= 0 for value in durations):
            raise ValueError('invalid runner duration: '+allocation)
        model_seconds = sum(durations)/1_000_000_000
        remainder = row['task_seconds']-model_seconds
        if remainder < 0:
            raise ValueError('model duration exceeds task interval: '+allocation)
        samples.append({'allocation':allocation, 'route':row['route'],
            'task_seconds':row['task_seconds'], 'model_runner_seconds':model_seconds,
            'task_minus_runner_seconds':remainder, 'model_call_seconds':[v/1e9 for v in durations],
            'condition_values':conditions.get('values'), 'intervention':conditions.get('intervention')})
    routes = {}
    for name in ('direct', 'compiled', 'fresh'):
        rows = [row for row in samples if row['route']==name]
        if len(rows)!=2:raise ValueError('expected two samples: '+label+'/'+name)
        routes[name] = {'n':len(rows),
            'model_runner_seconds_median':statistics.median(r['model_runner_seconds'] for r in rows),
            'task_minus_runner_seconds_median':statistics.median(r['task_minus_runner_seconds'] for r in rows),
            'samples':rows}
    output[label] = routes
print(json.dumps({'status':'audited', 'blocks':output}, indent=2))
