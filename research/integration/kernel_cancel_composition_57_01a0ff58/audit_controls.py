"""Ordinary post-assay copied-output integrity controls; primary files read only."""
import copy
import json
from pathlib import Path
from raw_audit import audit

HERE = Path(__file__).resolve().parent
raw = json.loads((HERE / 'run-01/raw.json').read_bytes())
controls = []


def check(name, change):
    value = copy.deepcopy(raw)
    change(value)
    errors = audit(value)
    controls.append({'case': name, 'errors': errors, 'rejected': bool(errors)})


check('missing_arm', lambda r: r['arms'].pop())
check('duplicate_arm', lambda r: r['arms'][1].update(arm='000'))
check('source_hash', lambda r: r['arms'][7]['source_sha256'].update(**{'lifecycle.py': '0' * 64}))
check('uncertainty_removed', lambda r: r['arms'][7]['rows'][1]['outcome'].update(effect_occurred=False))
check('bool_int_alias', lambda r: r['arms'][7]['rows'][1]['outcome'].update(effect_occurred=1))
check('equality_rejected', lambda r: r['arms'][7]['rows'][2]['events'][1].update(accepted=False))
check('duplicate_begin_hidden', lambda r: r['arms'][7]['rows'][9]['events'].pop(1))
check('fresh_stop_hidden', lambda r: r['arms'][7]['rows'][11]['events'].pop())
result = {'ordinary_post_assay': True, 'control_errors': audit(raw), 'controls': controls,
          'rejected': sum(c['rejected'] for c in controls)}
with (HERE / 'run-01/controls.json').open('x', encoding='utf-8', newline='\n') as handle:
    handle.write(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps({'control_errors': result['control_errors'], 'rejected': result['rejected']}))
raise SystemExit(bool(result['control_errors']) or result['rejected'] != 8)
