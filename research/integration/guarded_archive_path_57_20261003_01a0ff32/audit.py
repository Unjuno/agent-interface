"""Separate retained-raw oracle; never imports the candidate or rebuilds its archive."""
import copy
import json
from pathlib import Path
import sys

def audit(raw):
    errors = []
    if raw.get('schema') != 'archive-origin-probe-v1' or raw.get('platform') != 'win32':
        errors.append('schema/platform')
    accepted = {'actual', 'alternate_separator', 'inside_subdirectory'}
    refused = {'sibling_archive', 'prefix_adjacent', 'external'}
    wanted = {(module, case) for module in ('bridge', 'compiled') for case in accepted | refused}
    seen = set()
    for row in raw.get('rows', []):
        key = (row.get('module'), row.get('case'))
        if key not in wanted or key in seen:
            errors.append('unknown/duplicate case')
            continue
        seen.add(key)
        code = row.get('exit_code')
        stdout, stderr = row.get('stdout'), row.get('stderr')
        if type(code) is not int or type(stdout) is not str or type(stderr) is not str:
            errors.append('wrong raw type')
            continue
        lines = stdout.splitlines()
        try:
            paths = json.loads(lines[0])
            if set(paths) != {'archive', 'original', 'candidate'} or not all(type(v) is str for v in paths.values()):
                raise ValueError('path record')
        except (IndexError, ValueError, TypeError):
            errors.append('missing path evidence')
            continue
        # Pure string/component reference, independent of pathlib implementation.
        origin = paths['archive'].replace('\\', '/').rstrip('/').split('/')
        original = paths['original'].replace('\\', '/').split('/')
        candidate = paths['candidate'].replace('\\', '/').split('/')
        original_inside = original[:len(origin)] == origin and len(original) > len(origin)
        candidate_inside = candidate[:len(origin)] == origin and len(candidate) > len(origin)
        if not original_inside or candidate_inside != (row['case'] in accepted):
            errors.append('wrong path scenario')
        if row['case'] in accepted:
            if code != 0 or lines[-1:] != ['origin accepted'] or stderr:
                errors.append('positive refused')
        elif code != 1 or 'AssertionError' not in stderr or 'origin accepted' in stdout:
            errors.append('negative admitted/setup failure')
    if seen != wanted:
        errors.append('missing case')
    return errors

raw_path = Path(sys.argv[1])
raw = json.loads(raw_path.read_text(encoding='utf-8'))
errors = audit(raw)
controls = {}
mutations = {
    'accept_sibling': lambda data: data['rows'][3].update(exit_code=0, stderr='', stdout=data['rows'][3]['stdout']+'origin accepted\n'),
    'drop_row': lambda data: data['rows'].pop(),
    'duplicate_row': lambda data: data['rows'].append(copy.deepcopy(data['rows'][0])),
    'bool_exit': lambda data: data['rows'][0].update(exit_code=False),
    'float_exit': lambda data: data['rows'][0].update(exit_code=0.0),
    'erase_path': lambda data: data['rows'][0].update(stdout='origin accepted\n'),
}
for label, mutation in mutations.items():
    changed = copy.deepcopy(raw)
    mutation(changed)
    controls[label] = audit(changed)
result = {'schema': 'archive-origin-audit-v1', 'rows': len(raw['rows']), 'errors': errors,
          'corruption_controls': controls,
          'pass': not errors and all(bool(value) for value in controls.values())}
Path(sys.argv[2]).write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result))
raise SystemExit(0 if result['pass'] else 1)
