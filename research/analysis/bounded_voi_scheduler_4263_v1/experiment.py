from __future__ import annotations
import json, math, hashlib
from dataclasses import dataclass
from collections import defaultdict

ACTIONS = {
    'CHEAP': {'cost':1.0,'latency':1.0},
    'ROI': {'cost':3.0,'latency':3.0},
    'SPECIALIST': {'cost':5.0,'latency':6.0},
    'RICH': {'cost':12.0,'latency':10.0},
}
TERMINALS=('L','R','YIELD')
WRONG_LOSS=100.0
YIELD_LOSS=8.0
MISS_LOSS=30.0

DEV=[
 {'id':'easyL','w':24,'truth':'L','deadline':12,'obs':{'CHEAP':'L','ROI':'L','SPECIALIST':'L','RICH':'L'}},
 {'id':'easyR','w':24,'truth':'R','deadline':12,'obs':{'CHEAP':'R','ROI':'R','SPECIALIST':'R','RICH':'R'}},
 {'id':'roiL','w':14,'truth':'L','deadline':12,'obs':{'CHEAP':'A','ROI':'L','SPECIALIST':'A','RICH':'L'}},
 {'id':'roiR','w':14,'truth':'R','deadline':12,'obs':{'CHEAP':'A','ROI':'R','SPECIALIST':'A','RICH':'R'}},
 {'id':'specL','w':8,'truth':'L','deadline':12,'obs':{'CHEAP':'B','ROI':'B','SPECIALIST':'L','RICH':'L'}},
 {'id':'specR','w':8,'truth':'R','deadline':12,'obs':{'CHEAP':'B','ROI':'B','SPECIALIST':'R','RICH':'R'}},
 {'id':'lateL','w':2,'truth':'L','deadline':6,'obs':{'CHEAP':'C','ROI':'C','SPECIALIST':'L','RICH':'L'}},
 {'id':'lateR','w':2,'truth':'R','deadline':6,'obs':{'CHEAP':'C','ROI':'C','SPECIALIST':'R','RICH':'R'}},
 {'id':'ambL','w':2,'truth':'YIELD','deadline':12,'obs':{'CHEAP':'D','ROI':'D','SPECIALIST':'D','RICH':'D'}},
 {'id':'ambR','w':2,'truth':'YIELD','deadline':12,'obs':{'CHEAP':'D','ROI':'D','SPECIALIST':'D','RICH':'D'}},
]

EVAL=[]
def add(id,w,truth,deadline,cheap,roi,spec,rich,block):
    EVAL.append({'id':id,'w':w,'truth':truth,'deadline':deadline,'block':block,'obs':{'CHEAP':cheap,'ROI':roi,'SPECIALIST':spec,'RICH':rich}})
add('easyL',18,'L',12,'L','L','L','L','easy')
add('easyR',18,'R',12,'R','R','R','R','easy')
add('roiL',10,'L',12,'A','L','A','L','roi')
add('roiR',10,'R',12,'A','R','A','R','roi')
add('shiftL',5,'YIELD',12,'A','A','L','L','shift')
add('shiftR',5,'YIELD',12,'A','A','R','R','shift')
add('specL',8,'L',12,'B','B','L','L','specialist')
add('specR',8,'R',12,'B','B','R','R','specialist')
add('lateL',3,'YIELD',6,'C','C','L','L','late')
add('lateR',3,'YIELD',6,'C','C','R','R','late')
add('amb1',6,'YIELD',12,'D','D','D','D','ambiguous')
add('amb2',6,'YIELD',12,'D','D','D','D','ambiguous')

DEVW=sum(s['w'] for s in DEV)

def compatible(state, hist):
    return all(state['obs'][a]==o for a,o in hist)

def posterior(hist):
    xs=[s for s in DEV if compatible(s,hist)]
    z=sum(s['w'] for s in xs)
    return [(s,s['w']/z) for s in xs] if z else []

def terminal_risk(hist, choice):
    post=posterior(hist)
    if not post: return float('inf')
    if choice=='YIELD': return YIELD_LOSS
    return sum(p*(0 if s['truth']==choice else WRONG_LOSS) for s,p in post)

def best_terminal(hist):
    post=posterior(hist)
    if hist and not post:
        return 'YIELD', {'L':float('inf'),'R':float('inf'),'YIELD':0.0}
    vals={t:terminal_risk(hist,t) for t in TERMINALS}
    return min(vals,key=lambda k:(vals[k],k)),vals

def expected_action_value(hist, elapsed, action, deadline):
    meta=ACTIONS[action]
    if elapsed+meta['latency']>deadline: return None
    post=posterior(hist)
    by=defaultdict(list)
    for s,p in post: by[s['obs'][action]].append((s,p))
    er=0.0
    for o,rows in by.items():
        mass=sum(p for _,p in rows)
        nh=hist+[(action,o)]
        term,_=best_terminal(nh)
        er += mass*terminal_risk(nh,term)
    return meta['cost']+er

def voi_policy(state):
    hist=[]; elapsed=0.0; cost=0.0; acts=[]
    for step in range(4):
        term, risks=best_terminal(hist)
        base=risk=risks[term]
        if step>0 and base<=0.0:
            return term,cost,elapsed,acts,False
        cands=[]
        for a,m in ACTIONS.items():
            if a in acts: continue
            if step==0 and a!='CHEAP': continue
            ev=expected_action_value(hist,elapsed,a,state['deadline'])
            if ev is None: continue
            gain=base-ev
            ratio=gain/m['cost']
            cands.append((ratio,gain,-m['cost'],a,ev))
        if not cands:
            return term,cost,elapsed,acts,False
        cands.sort(reverse=True)
        ratio,gain,_,a,ev=cands[0]
        if step>0 and gain<=0:
            return term,cost,elapsed,acts,False
        elapsed+=ACTIONS[a]['latency']; cost+=ACTIONS[a]['cost']; acts.append(a)
        hist.append((a,state['obs'][a]))
    term,_=best_terminal(hist)
    return term,cost,elapsed,acts,False

FIXED=['CHEAP','ROI','SPECIALIST','RICH']
CHEAPEST=sorted(ACTIONS,key=lambda a:(ACTIONS[a]['cost'],a))

def baseline(state, order):
    hist=[];elapsed=0.;cost=0.;acts=[]
    for a in order:
        term,risks=best_terminal(hist)
        if hist and risks[term]<=0: return term,cost,elapsed,acts,False
        if elapsed+ACTIONS[a]['latency']>state['deadline']: continue
        elapsed+=ACTIONS[a]['latency'];cost+=ACTIONS[a]['cost'];acts.append(a);hist.append((a,state['obs'][a]))
    term,_=best_terminal(hist)
    return term,cost,elapsed,acts,False

def score(policy_name, fn):
    rows=[]
    totalw=sum(s['w'] for s in EVAL)
    agg={'weighted_cost':0,'weighted_latency':0,'wrong':0,'yield_errors':0,'deadline_miss':0,'unnecessary_expensive':0}
    for s in EVAL:
        d,c,l,acts,_=fn(s)
        miss=l>s['deadline']
        correct=(d==s['truth'])
        if s['truth']=='YIELD': ye=(d!='YIELD')
        else: ye=False
        wrong=(not correct)
        unnecessary=('RICH' in acts and any(a in acts for a in ['CHEAP','ROI','SPECIALIST']) and d==s['truth'])
        w=s['w']/totalw
        agg['weighted_cost']+=w*c;agg['weighted_latency']+=w*l
        agg['wrong']+=s['w'] if wrong else 0
        agg['yield_errors']+=s['w'] if ye else 0
        agg['deadline_miss']+=s['w'] if miss else 0
        agg['unnecessary_expensive']+=s['w'] if unnecessary else 0
        rows.append({'id':s['id'],'block':s['block'],'w':s['w'],'truth':s['truth'],'decision':d,'cost':c,'latency':l,'actions':acts,'correct':correct,'deadline_miss':miss})
    for k in ['wrong','yield_errors','deadline_miss','unnecessary_expensive']:
        agg[k]/=totalw
    return rows,agg

policies={
 'FIXED_CASCADE':lambda s:baseline(s,FIXED),
 'CHEAPEST_FIRST':lambda s:baseline(s,CHEAPEST),
 'FROZEN_VOI_POLICY':voi_policy,
}
allres={}
for name,fn in policies.items():
    rows,agg=score(name,fn);allres[name]={'rows':rows,'metrics':agg}

v=allres['FROZEN_VOI_POLICY']['metrics']; b1=allres['FIXED_CASCADE']['metrics']; b2=allres['CHEAPEST_FIRST']['metrics']
correct_gate=v['wrong']==0 and v['yield_errors']==0
deadline_gate=v['deadline_miss']<=b1['deadline_miss'] and v['deadline_miss']<=b2['deadline_miss']
primary_gate=v['weighted_cost']<b1['weighted_cost'] and v['weighted_cost']<b2['weighted_cost']
if not correct_gate: decision='FAIL_VOI_CORRECTNESS_REGRESSION'
elif not deadline_gate: decision='FAIL_DEADLINE_MISS_INCREASE'
elif primary_gate: decision='PASS_BOUNDED_VOI_SCHEDULER_SCOPED'
elif v['weighted_cost']>=min(b1['weighted_cost'],b2['weighted_cost']): decision='HOLD_FIXED_CASCADE_SUFFICIENT'
else: decision='HOLD_ESTIMATES_NOT_TRANSFERABLE'

out={'decision':decision,'dev_weight':DEVW,'evaluation_weight':sum(s['w'] for s in EVAL),'actions':ACTIONS,'fixed_order':FIXED,'cheapest_order':CHEAPEST,'metrics':{k:v['metrics'] for k,v in allres.items()},'results':allres}
print(json.dumps(out,sort_keys=True,separators=(',',':')))
