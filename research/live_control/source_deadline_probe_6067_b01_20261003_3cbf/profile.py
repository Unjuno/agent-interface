"""Prospective source exposure decomposition and finite diagnostic decision."""
def integer(value):
    if type(value) is not int: raise ValueError('exact timing integer')
    return value

def decompose(event, draw_trace):
    onset, due, ds, de, cs, ce = [integer(event[k]) for k in
        ('onset_ns','due_clear_ns','draw_start_ns','draw_end_ns','clear_start_ns','clear_end_ns')]
    returned = integer(draw_trace['wait']['return_ns'])
    if not onset <= returned <= ds <= de <= cs <= ce or due < onset:
        raise ValueError('source/wait chronology')
    if integer(draw_trace['paint_start_ns']) != ds or integer(draw_trace['paint_end_ns']) != de:
        raise ValueError('typed paint join')
    return {'exposure_ns':cs-de,'shortfall_ns':due-onset-(cs-de),
            'draw_wait_lateness_ns':returned-onset,'post_wait_to_paint_ns':ds-returned,
            'draw_xsync_ns':de-ds,'clear_lateness_ns':cs-due}

def classify(rows):
    if not rows: raise ValueError('nonempty source denominator')
    for row in rows:
        integer(row['shortfall_ns'])
        if integer(row['draw_wait_lateness_ns']) < 0: raise ValueError('negative wait lateness')
    failures = [r for r in rows if r['shortfall_ns'] > 5_000_000]
    if any(r['draw_wait_lateness_ns'] <= 5_000_000 for r in failures):
        return 'COUNTEREXAMPLE_WAIT_NECESSITY'
    return 'ASSOCIATION_ONLY_WAIT_LATE' if failures else 'HOLD_NOT_REPRODUCED'
