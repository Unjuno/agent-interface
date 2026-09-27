from __future__ import annotations
import json, math
from collections import defaultdict

PRED_COST={'A':1.0,'B':2.0,'C':5.0,'D':10.0}
NAIVE=['D','C','B','A']
VALS=('T','F','U')

# Development rows used only to freeze ordering.
DEV=[]
def d(expr,w,a,b,c,d): DEV.append({'expr':expr,'w':w,'v':{'A':a,'B':b,'C':c,'D':d}})
# AND decisive-false frequencies favor cheap predicates.
d('AND',40,'F','T','T','T'); d('AND',20,'T','F','T','T'); d('AND',10,'T','T','F','T'); d('AND',5,'T','T','T','F'); d('AND',15,'T','T','T','T'); d('AND',5,'U','T','T','T'); d('AND',5,'T','T','T','U')
# OR decisive-true frequencies favor cheap predicates.
d('OR',40,'T','F','F','F'); d('OR',20,'F','T','F','F'); d('OR',10,'F','F','T','F'); d('OR',5,'F','F','F','T'); d('OR',15,'F','F','F','F'); d('OR',5,'U','F','F','F'); d('OR',5,'F','F','F','U')

# Held-out evaluation with selectivity shift and UNKNOWN interactions.
EVAL=[]
def e(id,expr,w,a,b,c,d,block): EVAL.append({'id':id,'expr':expr,'w':w,'v':{'A':a,'B':b,'C':c,'D':d},'block':block})
# AND
for args in [
 ('and_A_false','AND',25,'F','T','T','T','cheap'),('and_B_false','AND',22,'T','F','T','T','shift'),
 ('and_C_false','AND',10,'T','T','F','T','mid'),('and_D_false','AND',10,'T','T','T','F','expensive_required'),
 ('and_all_true','AND',12,'T','T','T','T','expensive_required'),('and_U_only','AND',8,'U','T','T','T','unknown'),
 ('and_U_then_F','AND',7,'U','F','T','T','unknown_shortcircuit'),('and_late_U','AND',6,'T','T','T','U','unknown')]: e(*args)
# OR
for args in [
 ('or_A_true','OR',25,'T','F','F','F','cheap'),('or_B_true','OR',22,'F','T','F','F','shift'),
 ('or_C_true','OR',10,'F','F','T','F','mid'),('or_D_true','OR',10,'F','F','F','T','expensive_required'),
 ('or_all_false','OR',12,'F','F','F','F','expensive_required'),('or_U_only','OR',8,'U','F','F','F','unknown'),
 ('or_U_then_T','OR',7,'U','T','F','F','unknown_shortcircuit'),('or_late_U','OR',6,'F','F','F','U','unknown')]: e(*args)

def full_truth(expr, values):
    vals=[values[p] for p in ['A','B','C','D']]
    if expr=='AND':
        if 'F' in vals: return 'F'
        if 'U' in vals: return 'U'
        return 'T'
    if 'T' in vals: return 'T'
    if 'U' in vals: return 'U'
    return 'F'

def eval_order(row, order):
    cost=0.0; seen_u=False; used=[]
    for p in order:
        v=row['v'][p]; cost+=PRED_COST[p]; used.append(p)
        if v=='U': seen_u=True; continue
        if row['expr']=='AND' and v=='F': return 'F',cost,used
        if row['expr']=='OR' and v=='T': return 'T',cost,used
    # no decisive short-circuit observed
    if seen_u: return 'U',cost,used
    return ('T' if row['expr']=='AND' else 'F'),cost,used

def freeze_order(expr):
    rows=[r for r in DEV if r['expr']==expr]
    total=sum(r['w'] for r in rows)
    decisive='F' if expr=='AND' else 'T'
    stats={}
    for p in PRED_COST:
        freq=sum(r['w'] for r in rows if r['v'][p]==decisive)/total
        stats[p]={'decisive_freq':freq,'cost':PRED_COST[p],'score':freq/PRED_COST[p]}
    order=sorted(PRED_COST,key=lambda p:(-stats[p]['score'],PRED_COST[p],p))
    return order,stats

ORDERS={}; DEV_STATS={}
for expr in ('AND','OR'):
    ORDERS[expr],DEV_STATS[expr]=freeze_order(expr)

def quantile(expanded,q):
    xs=sorted(expanded)
    if not xs:return 0.0
    idx=max(0,min(len(xs)-1,math.ceil(q*len(xs))-1))
    return xs[idx]

def score(policy):
    rows=[]; expanded=[]; wrong=unknown_mismatch=0; totalw=sum(r['w'] for r in EVAL); totalcost=0
    for r in EVAL:
        order=NAIVE if policy=='NAIVE_ORDER' else ORDERS[r['expr']]
        out,cost,used=eval_order(r,order); truth=full_truth(r['expr'],r['v'])
        ok=out==truth
        wrong += 0 if ok else r['w']
        if (out=='U')!=(truth=='U'): unknown_mismatch+=r['w']
        totalcost += r['w']*cost; expanded.extend([cost]*r['w'])
        rows.append({'id':r['id'],'expr':r['expr'],'block':r['block'],'w':r['w'],'truth':truth,'decision':out,'cost':cost,'used':used,'correct':ok})
    return {'rows':rows,'metrics':{'weighted_cost':totalcost/totalw,'p50':quantile(expanded,.50),'p95':quantile(expanded,.95),'p99':quantile(expanded,.99),'wrong':wrong/totalw,'unknown_mismatch':unknown_mismatch/totalw,'predicate_evals_weighted':sum(r['w']*len(rr['used']) for r,rr in zip(EVAL,rows))/totalw}}

res={'NAIVE_ORDER':score('NAIVE_ORDER'),'COST_SELECTIVITY_ORDER':score('COST_SELECTIVITY_ORDER')}
n=res['NAIVE_ORDER']['metrics']; o=res['COST_SELECTIVITY_ORDER']['metrics']
if o['wrong']>0: decision='FAIL_SHORT_CIRCUIT_SEMANTICS'
elif o['unknown_mismatch']>0: decision='FAIL_UNKNOWN_MISHANDLING'
elif not (o['weighted_cost']<n['weighted_cost'] and o['p95']<=n['p95']): decision='HOLD_NO_COST_ADVANTAGE'
else: decision='PASS_COST_BASED_PREDICATE_ORDERING_SCOPED'
print(json.dumps({'decision':decision,'naive_order':NAIVE,'frozen_orders':ORDERS,'development_stats':DEV_STATS,'results':res},sort_keys=True,separators=(',',':')))
