"""Additive review candidate. Does not edit or replace the frozen upstream auditor."""

def deadline_errors(rows):
    errors = []
    if type(rows) is not list:
        return ['deadline_schema:rows']
    for i, row in enumerate(rows):
        if type(row) is not dict or type(row.get('samples')) is not list:
            errors.append(f'block{i}:deadline_schema'); continue
        for j, sample in enumerate(row['samples']):
            if type(sample) is not list or len(sample) != 3 or any(type(v) is not int for v in sample):
                errors.append(f'block{i}:sample{j}:deadline_schema'); continue
            due, wake, late = sample
            if wake < due:
                errors.append(f'block{i}:sample{j}:wake_before_due')
    return errors


def reconstruct_with_deadline_check(rows, upstream_reconstruct):
    # Existing checks are still run, not bypassed by successful local validation.
    result = upstream_reconstruct(rows)
    extra = deadline_errors(rows)
    if extra:
        result = dict(result)
        result['errors'] = list(result.get('errors', [])) + extra
        result['decision'] = 'FAIL_MEASUREMENT_BINDING'
    return result
