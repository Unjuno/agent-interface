"""Observe unchanged core/inspector APIs from one supplied checkout, no input."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from copy import deepcopy
from dataclasses import asdict

root, cases_path = map(Path, sys.argv[1:])
sys.path.insert(0, str(root))
from runtime.core_v1 import contract as c
from runtime.core_v1.sequence import expand_key_repeats, expand_text_gaps
spec = importlib.util.spec_from_file_location('static_inspector', root/'runtime/cli_v1/validate_program.py')
static = importlib.util.module_from_spec(spec)
spec.loader.exec_module(static)


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True)


def attempt(fn):
    try:
        value = fn()
        return {'kind': 'returned', 'value': value}
    except Exception as error:
        return {'kind': 'raised', 'type': type(error).__name__, 'detail': str(error),
                'operation_index': getattr(error, 'operation_index', None)}


rows = []
for case in json.loads(cases_path.read_text()):
    p = deepcopy(case['program']); before = encoded(p)
    expanded = deepcopy(p)
    if any('gap_ms' in x for x in p['ops']):
        expanded['ops'], _ = expand_text_gaps(p['ops'])
    elif any('repeat' in x for x in p['ops']):
        expanded['ops'] = expand_key_repeats(p['ops'], max_ops=128)
    e_before = encoded(expanded)
    m = c.capability_manifest('enum-check', 'linux', 'no-device', c.KNOWN_CAPABILITIES,
                              frames=sorted(c.COORDINATE_FRAMES))
    args = dict(now_ns=1, current_observation_seq=1, current_binding_revision=1)
    control = case['control']
    if control == 'expired': args['now_ns'] = 101
    elif control == 'stale_observation': args['current_observation_seq'] = 2
    elif control == 'stale_binding': args['current_binding_revision'] = 2
    elif control == 'unsupported': m['capabilities']['input.pointer']['state'] = 'unsupported'
    elif control == 'permission': m['capabilities']['input.pointer']['state'] = 'permission_required'
    elif control == 'coordinate': m['coordinate_frames'] = ['screen_physical_px']
    m_before = encoded(m)
    validation = attempt(lambda: c.validate_program(expanded) == expanded)
    admission = attempt(lambda: asdict(c.admit_program(expanded, m, **args)))
    inspection = attempt(lambda: static.inspect_program(p))
    rows.append({'id': case['id'], 'input_sha256': hashlib.sha256(before.encode()).hexdigest(),
                 'expanded_program': expanded, 'manifest': m, 'admission_arguments': args,
                 'validation': validation, 'admission': admission, 'inspection': inspection,
                 'input_unchanged': before == encoded(p), 'expanded_unchanged': e_before == encoded(expanded),
                 'manifest_unchanged': m_before == encoded(m)})
print(json.dumps({'rows': rows, 'imported_runtime_modules': sorted(x for x in sys.modules if x.startswith('runtime'))},
                 sort_keys=True, separators=(',', ':')))
