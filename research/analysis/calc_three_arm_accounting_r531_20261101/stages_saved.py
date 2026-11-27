"""Re-audit saved Calc trials and expose their nested monotonic intervals."""
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


def ordered(*values):
    if any(type(v) is not int for v in values) or any(a > b for a, b in zip(values, values[1:])):
        raise ValueError('invalid or unordered monotonic timestamps')


output = {}
for label, (forward, reverse) in blocks.items():
    audit = json.loads(subprocess.check_output([sys.executable, str(root / reverse / 'compare.py')]))
    if audit.get('status') != 'audited':
        raise RuntimeError('block audit failed: ' + label)
    samples = []
    for row in audit['trials']:
        allocation = row['allocation']
        folder = forward if allocation.startswith(('eo', 'eq')) else reverse
        with zipfile.ZipFile(root / folder / 'raw.zip') as archive:
            def read(path):
                return json.loads(archive.read(allocation + '/' + path).decode('utf-8-sig'))
            result = read('output/result.json')
            ocr = read('output/ocr-attempts.json')
            timing = read('output/method/call/owner-attempt-timing.json') if row['route'] == 'compiled' else None
        start, ms, me, end = (result[k] for k in ('task_start_ns', 'method_start_ns', 'method_end_ns', 'task_end_ns'))
        ordered(start, ms, me, end)
        if abs((end - start) / 1e9 - row['task_seconds']) > 1e-8:
            raise ValueError('task duration mismatch: ' + allocation)
        for attempt in ocr:
            ordered(ms, attempt['started_ns'], attempt['ended_ns'], me)
            if attempt['status'] != 'returned' or attempt['returncode'] != 0:
                raise ValueError('OCR did not return successfully: ' + allocation)
        sample = {'allocation': allocation, 'route': row['route'],
                  'pre_method_seconds': (ms-start)/1e9, 'method_seconds': (me-ms)/1e9,
                  'post_method_seconds': (end-me)/1e9,
                  'recorded_tesseract_seconds': sum(x['ended_ns']-x['started_ns'] for x in ocr)/1e9}
        if timing is not None:
            recovery = result['recovery']
            cs, ce = timing['started_ns'], timing['completed_ns']
            rs, re = recovery['recovery_started_ns'], recovery['recovery_ended_ns']
            ordered(ms, cs, ce, rs, re, me)
            if timing['clock'] != 'time.monotonic_ns' or timing['status'] != 'returned' or timing['elapsed_ns'] != ce-cs:
                raise ValueError('invalid compiled timing: ' + allocation)
            sample.update(compiled_owner_attempt_seconds=(ce-cs)/1e9, recovery_seconds=(re-rs)/1e9)
        samples.append(sample)
    routes = {}
    for name in ('direct', 'compiled', 'fresh'):
        rows = [r for r in samples if r['route'] == name]
        if len(rows) != 2:
            raise ValueError('expected two samples: ' + label + '/' + name)
        fields = ('pre_method_seconds', 'method_seconds', 'post_method_seconds', 'recorded_tesseract_seconds')
        if name == 'compiled':
            fields += ('compiled_owner_attempt_seconds', 'recovery_seconds')
        routes[name] = {'n': len(rows), 'medians': {k: statistics.median(r[k] for r in rows) for k in fields}, 'samples': rows}
    output[label] = routes
print(json.dumps({'status': 'audited', 'blocks': output}, indent=2))
