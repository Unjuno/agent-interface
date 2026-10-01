from itertools import product, permutations
import itertools, json

RES=(0,1,2)
OPS=[]
for r in RES:
    OPS.append((f'read{r}', frozenset({r}), frozenset(), ('read',r,None)))
    for v in (0,1):
        OPS.append((f'write{r}={v}', frozenset(), frozenset({r}), ('write',r,v)))
    OPS.append((f'inc{r}', frozenset({r}), frozenset({r}), ('inc',r,None)))
for a,b in permutations(RES,2):
    OPS.append((f'copy{a}->{b}', frozenset({a}), frozenset({b}), ('copy',a,b)))

INIT_STATES=list(product((0,1), repeat=3))

def conflict(fp1, fp2):
    r1,w1=fp1; r2,w2=fp2
    return bool((w1 & (r2|w2)) or (w2 & r1))

def runop(state, op):
    name,R,W,t=op
    s=list(state); obs=[]
    kind,a,b=t
    if kind=='read': obs.append((a,s[a]))
    elif kind=='write': s[a]=b
    elif kind=='inc': obs.append((a,s[a])); s[a]=(s[a]+1)%2
    elif kind=='copy': obs.append((a,s[a])); s[b]=s[a]
    return tuple(s),tuple(obs)

def execute(init, seq):
    s=init; observations={"A":[],"B":[]}
    for owner,phase,op in seq:
        s,obs=runop(s,op)
        observations[owner].append((phase,obs))
    return s,observations

def fp(op): return (op[1],op[2])

def complete_policy(a_tail,b_in,b_tail, unknown=False):
    if unknown: return False
    return not conflict(fp(a_tail),fp(b_in)) and not conflict(fp(a_tail),fp(b_tail))

def declared_policy(a_tail,b_in,b_tail, decls, unknown=False):
    if unknown: return False
    return not conflict(decls['a_tail'],decls['b_in']) and not conflict(decls['a_tail'],decls['b_tail'])

def candidate_seq(ai,at,bi,bt): return [('A','input',ai),('B','input',bi),('A','tail',at),('B','tail',bt)]
def oracle_seq(ai,at,bi,bt): return [('A','input',ai),('A','tail',at),('B','input',bi),('B','tail',bt)]

counts={
 'cases':0,'complete_admitted':0,'complete_mismatch':0,'declared_conflicts_serialized':0,
 'declared_conflicts_total':0,'unknown_parallel_admissions':0,
 'surface_only_mismatches':0,'surface_only_cases':0,
 'omitted_dependency_mismatches':0,'omitted_dependency_admitted':0,
 'reverse_predicate_mismatches':0,'reverse_predicate_admitted':0,
 'both_serial_orders_exercised':2,
}
witness={}
AIN=OPS[:4]

for init in INIT_STATES:
  for ai in AIN:
   for at,bi,bt in itertools.product(OPS, repeat=3):
    counts['cases']+=1
    cand=execute(init,candidate_seq(ai,at,bi,bt))
    ora=execute(init,oracle_seq(ai,at,bi,bt))
    safe=complete_policy(at,bi,bt)
    if safe:
        counts['complete_admitted']+=1
        if cand!=ora:
            counts['complete_mismatch']+=1
            witness.setdefault('complete_mismatch',(init,ai[0],at[0],bi[0],bt[0],cand,ora))
    else:
        counts['declared_conflicts_total']+=1
        counts['declared_conflicts_serialized']+=1

    if complete_policy(at,bi,bt,unknown=True):
        counts['unknown_parallel_admissions']+=1

    counts['surface_only_cases']+=1
    if cand!=ora:
        counts['surface_only_mismatches']+=1
        witness.setdefault('surface_only',(init,ai[0],at[0],bi[0],bt[0],cand,ora))

    R,W=fp(at)
    if W:
        omitted=frozenset({next(iter(W))})
        decl_at=(R, W-omitted)
        decls={'a_tail':decl_at,'b_in':fp(bi),'b_tail':fp(bt)}
        if declared_policy(at,bi,bt,decls):
            counts['omitted_dependency_admitted']+=1
            if cand!=ora:
                counts['omitted_dependency_mismatches']+=1
                witness.setdefault('omitted_dependency',(init,ai[0],at[0],bi[0],bt[0],cand,ora))

    wrong = conflict(fp(at),fp(bi)) or conflict(fp(at),fp(bt))
    if wrong:
        counts['reverse_predicate_admitted']+=1
        if cand!=ora:
            counts['reverse_predicate_mismatches']+=1
            witness.setdefault('reverse_predicate',(init,ai[0],at[0],bi[0],bt[0],cand,ora))

result={'counts':counts,'witness':witness,'ops':len(OPS),'initial_states':len(INIT_STATES),'decision':None}
pass_gate=(counts['complete_mismatch']==0 and counts['complete_admitted']>0 and
           counts['declared_conflicts_serialized']==counts['declared_conflicts_total'] and
           counts['unknown_parallel_admissions']==0 and counts['surface_only_mismatches']>0 and
           counts['omitted_dependency_mismatches']>0 and counts['reverse_predicate_mismatches']>0 and
           counts['both_serial_orders_exercised']==2)
result['decision']='PASS_PHASE_OVERLAP_RESOURCE_FOOTPRINT_SERIALIZABILITY_SCOPED' if pass_gate else 'FAIL_OR_HOLD'
print(json.dumps(result,indent=2,sort_keys=True,default=str))
