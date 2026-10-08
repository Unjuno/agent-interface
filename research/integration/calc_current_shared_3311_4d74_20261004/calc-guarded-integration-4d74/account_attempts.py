"""Read retained raw attempts; never execute native input or rewrite an earlier audit."""
import json
from pathlib import Path

root = Path(__file__).resolve().parent
attempts = []
for ordinal in (1, 2, 3):
    raw = json.loads((root / 'runs' / f'guarded0{ordinal}' / 'raw.json').read_text(encoding='utf-8'))
    for key in ('guarded_result', 'reuse_old_result', 'repair_result', 'warm_result'):
        if key in raw:
            receipt = raw[key]
            attempts.append({'ordinal': ordinal, 'key': key,
                             'status': receipt.get('status'),
                             'input_dispatched': receipt.get('input_dispatched'),
                             'guard_stages': [g['stage'] for g in receipt.get('guard_checks', [])]})
out = {'scope': 'retained raw receipt inventory; no replay', 'attempts': attempts,
       'accepted_programs': sum(a['status'] == 'completed' for a in attempts),
       'refused_programs': sum(a['status'] == 'refused' for a in attempts),
       'preinput_alias_failures': [1],
       'original_producer_counter_correction': 'G03 task_dispatches=1 undercounts three completed programs; original retained',
       'original_auditor_counter_limit': 'printed accepted/refused counts were constants; use this raw-derived inventory'}
target = root / 'ATTEMPT_ACCOUNTING.json'
if target.exists():
    raise RuntimeError('inventory already exists; do not overwrite')
target.write_text(json.dumps(out, indent=2) + '\n', encoding='utf-8')
print(json.dumps(out))
