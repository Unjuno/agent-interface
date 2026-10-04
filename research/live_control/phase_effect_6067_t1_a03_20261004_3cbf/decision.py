"""Closed full-family aggregate; never a task/model/safety claim."""
from reference import check_fixture_plan, join


def evaluate(fixture, rows, historical_status):
    check_fixture_plan(fixture)
    if type(rows) is not list or len(rows) != 114:
        raise ValueError('complete 114-cell qualification required')
    counts = {name: 0 for name in ('fixed', 'irregular', 'rotated')}
    fixed_blind = set()
    boundary = unknown = 0
    for spec, row in zip(fixture['cases'], rows):
        if type(row) is not dict or any(type(row.get(k)) is not type(v) or row.get(k) != v
                                        for k, v in spec.items()):
            raise ValueError('ordered typed case join')
        join({k:row[k] for k in spec},spec,'recursively typed case join')
        ids = row.get('stable_ids')
        if (type(ids) is not list or any(type(i) is not int or not 1 <= i <= 8 for i in ids)
                or len(set(ids)) != len(ids)):
            raise ValueError('stable ID domain')
        for key in ('boundary_hits', 'unknown_frames'):
            if type(row.get(key)) is not int or not 0 <= row[key] <= 8:
                raise ValueError('typed bounded frame count')
        if len(ids)+row['boundary_hits']+row['unknown_frames'] > 8:
            raise ValueError('eight-frame accounting')
        if spec['kind'] == 'dark' and ids:
            raise ValueError('dark false positive')
        if spec['kind'] == 'persistent' and ids != [1]:
            raise ValueError('persistent control not qualified')
        boundary += row['boundary_hits']
        unknown += row['unknown_frames']
        if spec['kind'] == 'pulse' and not ids:
            counts[spec['schedule']] += 1
            if spec['schedule'] == 'fixed':
                fixed_blind.add(spec['width_ms'])
    benefit = (historical_status == 'PASS_TRANSFER_SCOPED'
               and fixed_blind == {10, 20, 30}
               and counts['irregular'] < counts['fixed']
               and counts['rotated'] < counts['fixed'])
    status = ('HOLD_SOURCE_BOUNDARY_AMBIGUITY' if boundary or unknown else
              'PASS_NATIVE_PHASE_EFFECT_SCOPED' if benefit else
              'HOLD_BENEFIT_NOT_ESTABLISHED')
    return {'status': status, 'qualified_all_miss_episodes': counts,
            'boundary_hits': boundary, 'unknown_frames': unknown,
            'cells': 114, 'captures': 912,
            'fixed_blind_widths_ms': sorted(fixed_blind)}
