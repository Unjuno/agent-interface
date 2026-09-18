FIELDS=('focus','target_binding','image','ui_context')
CRITICAL={'focus','target_binding'}
NONCRITICAL={'image','ui_context'}
SKEW=2

def _identity(field):
    return (field['session'],field['surface'],field['generation'])

def anchored_bounded_skew(row):
    fields=row.get('fields')
    now=row.get('now')
    if not isinstance(fields,dict) or set(fields)!=set(FIELDS) or not isinstance(now,int):
        return False
    times=[]
    identities=[]
    for name in FIELDS:
        f=fields.get(name)
        if not isinstance(f,dict): return False
        t=f.get('sample_time')
        if not isinstance(t,int) or t<0 or t>now: return False
        if not isinstance(f.get('session'),str) or not isinstance(f.get('surface'),str) or not isinstance(f.get('generation'),int): return False
        times.append(t); identities.append(_identity(f))
    if len(set(identities))!=1: return False
    anchor=max(times)
    if anchor>now: return False
    for name in CRITICAL:
        vu=fields[name].get('valid_through')
        if not isinstance(vu,int) or vu<anchor: return False
    for name in NONCRITICAL:
        if anchor-fields[name]['sample_time']>SKEW: return False
    return True

def pairwise_skew_only(row):
    fields=row.get('fields'); now=row.get('now')
    if not isinstance(fields,dict) or set(fields)!=set(FIELDS) or not isinstance(now,int): return False
    times=[]; ids=[]
    for name in FIELDS:
        f=fields.get(name)
        if not isinstance(f,dict): return False
        t=f.get('sample_time')
        if not isinstance(t,int) or t<0 or t>now: return False
        try: ids.append(_identity(f))
        except Exception: return False
        times.append(t)
    return len(set(ids))==1 and max(times)-min(times)<=SKEW

def strict_anchor(row):
    if not anchored_bounded_skew(row): return False
    times=[row['fields'][n]['sample_time'] for n in FIELDS]
    return len(set(times))==1
