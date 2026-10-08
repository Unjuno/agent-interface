import itertools, json
RES=('S','X','Y')

def op_defs():
    out=[]
    for r in RES:
        out += [
            (f'read_{r}', frozenset({r}), frozenset(), ('read',r,None)),
            (f'write0_{r}', frozenset(), frozenset({r}), ('write',r,0)),
            (f'write1_{r}', frozenset(), frozenset({r}), ('write',r,1)),
            (f'toggle_{r}', frozenset({r}), frozenset({r}), ('toggle',r,None)),
        ]
    return out
OPS=op_defs()

def runop(st, op):
    name,R,W,t=op; kind,r,v=t; s=dict(st); obs=[]
    if kind=='read': obs.append((r,s[r]))
    elif kind=='write': s[r]=v
    elif kind=='toggle': obs.append((r,s[r])); s[r]=1-s[r]
    return s, tuple(obs)

def prepare(st):
    return st['S'], (('S',st['S']),)

def a_tail(st):
    s=dict(st); sv=s['S']; target='X' if sv==0 else 'Y'
    obs=(('S',sv),(target,s[target]))
    s[target]=1-s[target]
    return s, obs

def conflict(fp1,fp2):
    r1,w1=fp1; r2,w2=fp2
    return bool((w1 & (r2|w2)) or (w2 & r1))

def fp(op): return (op[1],op[2])

def execute(init, bi, bt, overlap):
    s=dict(init); A=[]; B=[]
    sel,o=prepare(s); A.append(('prepare',o))
    if overlap:
        s,o=runop(s,bi); B.append(('input',o))
        s,o=a_tail(s); A.append(('tail',o))
    else:
        s,o=a_tail(s); A.append(('tail',o))
        s,o=runop(s,bi); B.append(('input',o))
    s,o=runop(s,bt); B.append(('tail',o))
    return (tuple((k,s[k]) for k in RES), tuple(A), tuple(B)), sel

def decl_static(sel): return (frozenset({'S'}), frozenset({'X','Y'}))
def decl_bound(sel): return (frozenset({'S'}), frozenset({'X' if sel==0 else 'Y'}))
def decl_unbound(sel): return (frozenset(), frozenset({'X' if sel==0 else 'Y'}))

def admit(decl,bi,bt): return not conflict(decl,fp(bi)) and not conflict(decl,fp(bt))

counts={k:0 for k in [
 'cases','static_admitted','static_mismatch','bound_admitted','bound_mismatch',
 'unbound_admitted','unbound_mismatch','unknown_admitted','bound_selector_write_admitted',
 'bound_extra_over_static','bound_extra_safe','bound_extra_mismatch'
]}
witness={}
for vals in itertools.product((0,1), repeat=3):
    init=dict(zip(RES,vals))
    for bi,bt in itertools.product(OPS, repeat=2):
        counts['cases']+=1
        serial,sel=execute(init,bi,bt,False)
        over,_=execute(init,bi,bt,True)
        policies={
          'static':admit(decl_static(sel),bi,bt),
          'bound':admit(decl_bound(sel),bi,bt),
          'unbound':admit(decl_unbound(sel),bi,bt),
          'unknown':False,
        }
        for p in ('static','bound','unbound'):
            if policies[p]:
                counts[p+'_admitted']+=1
                if over!=serial:
                    counts[p+'_mismatch']+=1
                    witness.setdefault(p+'_mismatch', {'init':init,'bi':bi[0],'bt':bt[0],'overlap':over,'serial':serial,'prepared_selector':sel})
        if policies['unknown']: counts['unknown_admitted']+=1
        writes_selector=bool((fp(bi)[1]|fp(bt)[1]) & {'S'})
        if policies['bound'] and writes_selector:
            counts['bound_selector_write_admitted']+=1
            witness.setdefault('bound_selector_write_admitted', {'init':init,'bi':bi[0],'bt':bt[0]})
        if policies['bound'] and not policies['static']:
            counts['bound_extra_over_static']+=1
            if over==serial: counts['bound_extra_safe']+=1
            else:
                counts['bound_extra_mismatch']+=1
                witness.setdefault('bound_extra_mismatch', {'init':init,'bi':bi[0],'bt':bt[0]})

passed=(counts['bound_mismatch']==0 and counts['static_mismatch']==0 and counts['unknown_admitted']==0 and
        counts['bound_extra_over_static']>0 and counts['bound_extra_safe']==counts['bound_extra_over_static'] and
        counts['unbound_mismatch']>0 and counts['bound_selector_write_admitted']==0)
decision='PASS_DYNAMIC_FOOTPRINT_BINDING_SERIALIZABILITY_SCOPED' if passed else ('HOLD_NO_CONCURRENCY_GAIN' if counts['bound_extra_over_static']==0 and counts['bound_mismatch']==0 else 'FAIL_DYNAMIC_FOOTPRINT_BINDING')
out={'decision':decision,'counts':counts,'witness':witness,'ops':len(OPS),'initial_states':8}
print(json.dumps(out,indent=2,sort_keys=True))
