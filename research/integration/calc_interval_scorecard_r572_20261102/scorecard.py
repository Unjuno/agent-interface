"""Descriptive interval summary from the existing two-block comparison audit."""
import json
from pathlib import Path
import statistics

root = Path(__file__).resolve().parent
report = json.loads((root / 'comparison-audit.json').read_text(encoding='utf-8-sig'))
if report.get('status') != 'audited':
    raise ValueError('comparison audit did not pass')
rows = report['trials']
if len(rows) != 6 or len({row['allocation'] for row in rows}) != 6:
    raise ValueError('expected six distinct retained attempts')
summary = {}
for route in ('direct', 'compiled', 'fresh'):
    selected = [row for row in rows if row['route'] == route]
    if len(selected) != 2:
        raise ValueError('expected two attempts for each route')
    summary[route] = {
        'task_seconds': statistics.median(row['task_seconds'] for row in selected),
        'launcher_seconds': statistics.median(row['launcher_seconds'] for row in selected),
        'input_tokens': statistics.median(row['input_tokens'] for row in selected),
    }
print(json.dumps({'scope':'descriptive_two_per_route', 'medians':summary}, indent=2))
