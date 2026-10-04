import itertools, json
from fractions import Fraction as F
from pathlib import Path

D=Path(__file__).parent
# Independent transcription of the preregistered fixtures.
T={
 'dominance': {'A':[[1,2,1],[2,1,2],[1,1,1]],'B':[[2,3,2],[3,2,3],[2,2,2]]},
 'crossed_tradeoff': {'A':[[1,4,3],[4,1,3],[3,3,3]],'B':[[3,2,3],[2,3,3],[3,3,3]]},
 'task_mix_reversal': {'A':[[1,4,3],[4,1,3],[3,3,3]],'B':[[3,2,3],[2,3,3],[3,3,3]]},
 'value_weight_reversal': {'A':[[1,4,3],[1,4,3],[1,4,3]],'B':[[3,2,3],[3,2,3],[3,2,3]]},
 'missing_stratum': {'A':[[1,2,1],[2,None,2],[1,1,1]],'B':[[2,3,2],[3,2,3],[2,2,2]]},
 'hard_gate': {'A':[[1,1,1],[1,1,1],[1,1,1]],'B':[[2,2,2],[2,2,2],[2,2,2]]},
}
G={n:{'correct_effect':True,'safe_release':True,'evidence_integrity':True} for n in ['A','B']}
G['A']['safe_release']=False

def compositions(n=6):
    return [(F(a,n),F(b,n),F(n-a-b,n)) for a in range(n+1) for b in range(n-a+1)]
P=compositions(); W=compositions()
def calc(row,p,w):
    # Direct numerator/denominator arithmetic; do not call rank.py.
    z=F(0)
    for s in range(3):
        for k in range(3):
            x=row[s][k]
            if x is None:
                if p[s] and w[k]: return None
            else: z += p[s]*w[k]*x
    return z
def region(tab, ps, ws, gates):
    elig=[r for r in tab if all(gates[r].values())]
    if len(elig)<2:return ('HOLD_FEWER_THAN_TWO_ELIGIBLE_ROUTES',elig,{},0,0)
    counts={};missing=0; done=0
    for p,w in itertools.product(ps,ws):
        a,b=(calc(tab[r],p,w) for r in elig[:2])
        if a is None or b is None:missing+=1;continue
        done+=1
        label='TIE' if a==b else elig[0] if a<b else elig[1]
        counts[label]=counts.get(label,0)+1
    if missing:return ('HOLD_UNIDENTIFIED_OUTCOME',elig,{},missing,done)
    label='ROBUST_'+next(iter(counts)) if len(counts)==1 and 'TIE' not in counts else 'MIXED_OR_TIED_REGION'
    return (label,elig,counts,0,done)

def ordinary(tab,gates,mix=(F(1,3),)*3,weights=(F(1,3),)*3):
    elig=[r for r in tab if all(gates[r].values())]
    if len(elig)<2:return {'disposition':'HOLD_FEWER_THAN_TWO_ELIGIBLE_ROUTES','eligible':elig}
    vals={r:calc(tab[r],mix,weights) for r in elig}
    if any(v is None for v in vals.values()):return {'disposition':'HOLD_UNIDENTIFIED_OUTCOME','eligible':elig}
    win='TIE' if len(set(vals.values()))==1 else min(vals,key=vals.get)
    return {'disposition':win,'scores':{r:str(v) for r,v in vals.items()},'eligible':elig}

spec={k:(P,W) for k in T}
spec['task_mix_reversal']=(P,[(F(1),F(0),F(0))])
spec['value_weight_reversal']=([(F(1),F(0),F(0))],W)
summary={}
for k,tab in T.items():
    lab,elig,counts,n,done=region(tab,*spec[k],G if k=='hard_gate' else {r:{x:True for x in G[r]} for r in G})
    summary[k]={'disposition':lab,'eligible':elig,'winner_counts':counts,'evaluated_pairs':done,'missing_pairs':n,
                'fixed_equal_aggregate':ordinary(tab,G if k=='hard_gate' else {r:{x:True for x in G[r]} for r in G})}
# Exact predefined mutation checks.
mut={}
x=json.loads(json.dumps(T));x['dominance']['A'][0][0]=10
mut['dominance_cell_reversal']=region(x['dominance'],P,W,{r:{z:True for z in G[r]} for r in G})[0] != 'ROBUST_A'
x=json.loads(json.dumps(T));x['task_mix_reversal']['A'][0][0]=5
mut['task_stratum_latency_flip']=region(x['task_mix_reversal'],P,[(F(1),F(0),F(0))],{r:{z:True for z in G[r]} for r in G})[2] != region(T['task_mix_reversal'],P,[(F(1),F(0),F(0))],{r:{z:True for z in G[r]} for r in G})[2]
x=json.loads(json.dumps(T));x['value_weight_reversal']['A']=[[1,4,3]]*3
mut['weight_domain_restriction']=region(x['value_weight_reversal'],[(F(1),F(0),F(0))],[(F(1),F(0),F(0))],{r:{z:True for z in G[r]} for r in G})[0] == 'ROBUST_A'
x=json.loads(json.dumps(T));g={r:{z:True for z in G[r]} for r in G}
mut['hard_gate_passed']=region(x['hard_gate'],P,W,g)[0]=='ROBUST_A'
x=json.loads(json.dumps(T));x['missing_stratum']['A'][1][1]=2
mut['missing_cell_filled']=region(x['missing_stratum'],P,W,{r:{z:True for z in G[r]} for r in G})[0] != 'HOLD_UNIDENTIFIED_OUTCOME'
assert all(mut.values()),mut
# Check exact candidate outcome counts/dispositions independently.
cand=json.loads((D/'candidate.json').read_text(encoding='utf-8-sig'))
for k,v in summary.items():
    assert cand[k]['disposition']==v['disposition'],(k,cand[k]['disposition'],v['disposition'])
    if 'winner_counts' in cand[k]: assert cand[k]['winner_counts']==v['winner_counts'],(k,cand[k]['winner_counts'],v['winner_counts'])
    if 'evaluated_pairs' in cand[k]: assert cand[k]['evaluated_pairs']==v['evaluated_pairs'],(k,cand[k],v)
    if 'missing_pairs' in cand[k]: assert cand[k]['missing_pairs']==v['missing_pairs'],(k,cand[k],v)
result={'status':'PASS_METHOD_SCOPED','grid_denominator':6,'simplex_points_per_domain':len(P),
        'candidate_comparison':'all fixture dispositions and exact winner counts agree',
        'fixture_audit':summary,'mutation_checks':mut}
(D/'independent-audit.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'status':result['status'],'simplex_points':len(P),'fixtures':{k:(v['disposition'],v['winner_counts']) for k,v in summary.items()},'mutations':mut},indent=2))
