from itertools import product
import json

def optimal_makespan(durations, deps, resources):
    n=len(durations)
    horizon=sum(durations)
    best=horizon
    for starts in product(range(horizon+1), repeat=n):
        finish=[starts[i]+durations[i] for i in range(n)]
        m=max(finish, default=0)
        if m>=best:
            continue
        ok=True
        for j in range(n):
            for i in deps[j]:
                if finish[i] > starts[j]:
                    ok=False
                    break
            if not ok:
                break
        if not ok:
            continue
        for i in range(n):
            for j in range(i+1,n):
                if resources[i] & resources[j]:
                    if not (finish[i] <= starts[j] or finish[j] <= starts[i]):
                        ok=False
                        break
            if not ok:
                break
        if ok:
            best=m
    return best

def cp_lower_bound(durations,deps):
    longest=[0]*len(durations)
    for j in range(len(durations)):
        longest[j]=durations[j]+max((longest[i] for i in deps[j]), default=0)
    return max(longest, default=0)

def resource_lb(durations,resources):
    allr=set().union(*resources) if resources else set()
    return max((sum(durations[i] for i,r in enumerate(resources) if x in r) for x in allr), default=0)

cases=0
lb_viol=0
alias_counter=0
strict_speedups=0
max_speedup=1.0
witness=None
edge_opts=[(0,1),(0,2),(1,2)]
resource_opts=[frozenset({'P'}),frozenset({'K'}),frozenset({'P','K'})]

for durations in product([1,2], repeat=3):
    for bits in product([0,1], repeat=3):
        deps=[set() for _ in range(3)]
        for b,(a,c) in zip(bits,edge_opts):
            if b:
                deps[c].add(a)
        for resources in product(resource_opts, repeat=3):
            cases+=1
            opt=optimal_makespan(durations,deps,resources)
            lb=max(cp_lower_bound(durations,deps),resource_lb(durations,resources))
            if opt<lb:
                lb_viol+=1
            if all('P' in r for r in resources):
                if opt != sum(durations):
                    alias_counter+=1
            baseline=sum(durations)
            if opt < baseline:
                strict_speedups+=1
                sp=baseline/opt
                if sp>max_speedup:
                    max_speedup=sp
                    witness=(durations,bits,[sorted(r) for r in resources],baseline,opt)

examples=[]
for name,durations,deps,resources in [
    ('two_logical_cursors_same_pointer',(3,3),[set(),set()],[frozenset({'P'}),frozenset({'P'})]),
    ('two_independent_virtual_pointers',(3,3),[set(),set()],[frozenset({'P0'}),frozenset({'P1'})]),
    ('pointer_plus_keyboard',(3,3),[set(),set()],[frozenset({'P'}),frozenset({'K'})]),
    ('dependency_dominates',(3,3),[set(),{0}],[frozenset({'P0'}),frozenset({'P1'})]),
    ('atomic_two_contact_gesture',(4,),[set()],[frozenset({'TOUCH_PAIR'})]),
]:
    opt=optimal_makespan(durations,deps,resources)
    examples.append({
        'name':name,
        'serial_baseline':sum(durations),
        'optimal':opt,
        'speedup':sum(durations)/opt
    })

result={
    'enumerated_cases':cases,
    'lower_bound_violations':lb_viol,
    'aliased_pointer_counterexamples':alias_counter,
    'strict_speedup_cases_vs_global_serial_baseline':strict_speedups,
    'max_speedup_in_bounded_search':max_speedup,
    'max_speedup_witness':witness,
    'examples':examples
}
print(json.dumps(result,indent=2))
