from fractions import Fraction

DISPOSITIONS = {
    'REBUILD_REQUIRED','REUSE','DROP_EXPIRED',
    'CANCEL_STALE','CANCEL_TARDY','RUN','WAIT','TIE'
}

def expected_selector(p_num, p_den, g_ns, w_ns):
    p = Fraction(int(p_num), int(p_den))
    run = p * int(w_ns)
    wait = (1 - p) * int(g_ns)
    if run < wait:
        return 'RUN'
    if run > wait:
        return 'WAIT'
    return 'TIE'

def decide_cached(source_versions, current_versions, t_ns, deadline_ns):
    if tuple(source_versions) != tuple(current_versions):
        return 'REBUILD_REQUIRED'
    if int(t_ns) > int(deadline_ns):
        return 'DROP_EXPIRED'
    return 'REUSE'

def decide_active(source_versions, current_versions, t_ns, remaining_cost_ns, deadline_ns,
                  p_num, p_den, g_ns, w_ns):
    if tuple(source_versions) != tuple(current_versions):
        return 'CANCEL_STALE'
    if int(t_ns) + int(remaining_cost_ns) > int(deadline_ns):
        return 'CANCEL_TARDY'
    return expected_selector(p_num, p_den, g_ns, w_ns)
