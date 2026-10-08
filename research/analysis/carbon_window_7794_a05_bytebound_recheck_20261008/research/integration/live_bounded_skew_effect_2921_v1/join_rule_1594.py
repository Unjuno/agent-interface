SKEW_NS=2_000_000

def candidate(row):
    fs=row['fields']; ids=[(fs[k]['session'],fs[k]['surface'],fs[k]['generation']) for k in ('focus','target_binding','image','ui_context')]
    if len(set(ids))!=1: return False
    ts=[fs[k]['sample_ns'] for k in fs]
    if any(type(x) is not int for x in ts): return False
    anchor=max(ts)
    if anchor>row['now_ns']: return False
    if fs['focus']['valid_through_ns']<anchor or fs['target_binding']['valid_through_ns']<anchor: return False
    if anchor-fs['image']['sample_ns']>SKEW_NS or anchor-fs['ui_context']['sample_ns']>SKEW_NS: return False
    return True

def strict(row):
    if not candidate(row): return False
    return len({row['fields'][k]['sample_ns'] for k in row['fields']})==1
