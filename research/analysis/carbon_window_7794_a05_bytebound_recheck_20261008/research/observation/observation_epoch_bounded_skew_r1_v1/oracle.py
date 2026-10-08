REQUIRED=('focus','target_binding','image','ui_context')
CRIT=('focus','target_binding')
NON=('image','ui_context')

def oracle_join(row,delta=2):
    fs=row.get('fields'); now=row.get('now')
    if type(now) is not int or type(fs) is not dict: return False
    if sorted(fs.keys())!=sorted(REQUIRED): return False
    identity=None; stamp=[]
    for key in REQUIRED:
        item=fs[key]
        if type(item) is not dict: return False
        t=item.get('sample_time')
        if type(t) is not int or t<0 or t>now: return False
        s=item.get('session'); u=item.get('surface'); g=item.get('generation')
        if type(s) is not str or type(u) is not str or type(g) is not int: return False
        ident=(s,u,g)
        if identity is None: identity=ident
        elif ident!=identity: return False
        stamp.append(t)
    a=max(stamp)
    for key in CRIT:
        until=fs[key].get('valid_through')
        if type(until) is not int or until<a: return False
    for key in NON:
        if a-fs[key]['sample_time']>delta: return False
    return True
