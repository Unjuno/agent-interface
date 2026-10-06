"""Finite diagnostic gate, no phase-effect or causal-rootcause promotion."""
from statistics import median

def contrast(cells):
    grouped = {}
    for cell in cells:
        pair, treatment, values = cell['pair'], cell['treatment'], cell['delays_ns']
        if (type(pair) is not int or pair not in range(6) or treatment not in ('full', 'minimal')
                or len(values) != 8 or any(type(v) is not int or v < 0 for v in values)
                or (pair, treatment) in grouped):
            raise ValueError('complete typed paired observations required')
        grouped[pair, treatment] = values
    if set(grouped) != {(p, t) for p in range(6) for t in ('full', 'minimal')}:
        raise ValueError('all six matched pairs required')
    paired = [median(grouped[p, 'full']) - median(grouped[p, 'minimal']) for p in range(6)]
    pooled = median([v for (p, t), vs in grouped.items() if t == 'full' for v in vs]) - median(
        [v for (p, t), vs in grouped.items() if t == 'minimal' for v in vs])
    status = ('SUPPORTED_FINITE_CONTRAST' if pooled >= 500_000 and
              sum(v >= 500_000 for v in paired) >= 5 else 'HOLD_NOT_REPRODUCED')
    return {'status': status, 'paired_reductions_ns': paired, 'pooled_reduction_ns': pooled}
