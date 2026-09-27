from itertools import product
import json, hashlib
PHASES=('PREPARE','EFFECT_PENDING','TERMINAL')
DOMS=('T','D','E','S')
SUPPORT={
 'PREPARE': frozenset('TDS'),
 'EFFECT_PENDING': frozenset('TDES'),
 'TERMINAL': frozenset('ES'),
}
PRES=frozenset('TD')

def dec(phase, st):
    T,D,E,S=st
    if phase=='PREPARE':
        if S:return 'ABORT'
        if T and D:return 'READY'
        return 'WAIT'
    if phase=='EFFECT_PENDING':
        if S:return 'ABORT'
        if E:return 'COMPLETE'
        if T and D:return 'CONTINUE'
        return 'WAIT'
    if S:return 'ABORT'
    if E:return 'COMPLETE'
    return 'TERMINAL_UNRESOLVED'

def suppress(mask, changed): return not bool(mask & changed)
rows=[]
metrics={k:0 for k in ['rows','baseline_false_suppress','candidate_false_suppress','candidate_safe_suppress','global_false_suppress','global_false_forward','candidate_false_forward']}
phase_metrics={p:{k:0 for k in ['rows','baseline_false_suppress','candidate_false_suppress','candidate_safe_suppress','global_false_forward','candidate_false_forward']} for p in PHASES}
escapes=[]
for phase in PHASES:
  for a in product((0,1), repeat=4):
    for b in product((0,1), repeat=4):
      changed=frozenset(d for d,x,y in zip(DOMS,a,b) if x!=y)
      must=dec(phase,a)!=dec(phase,b)
      bs=suppress(PRES,changed)
      cs=suppress(SUPPORT[phase],changed)
      gs=not bool(changed)
      metrics['rows']+=1; phase_metrics[phase]['rows']+=1
      if bs and must:
        metrics['baseline_false_suppress']+=1; phase_metrics[phase]['baseline_false_suppress']+=1
        if len(escapes)<20: escapes.append((phase,a,b,sorted(changed),dec(phase,a),dec(phase,b)))
      if cs and must: metrics['candidate_false_suppress']+=1; phase_metrics[phase]['candidate_false_suppress']+=1
      if cs and not must: metrics['candidate_safe_suppress']+=1; phase_metrics[phase]['candidate_safe_suppress']+=1
      if gs and must: metrics['global_false_suppress']+=1
      if (not gs) and (not must): metrics['global_false_forward']+=1; phase_metrics[phase]['global_false_forward']+=1
      if (not cs) and (not must): metrics['candidate_false_forward']+=1; phase_metrics[phase]['candidate_false_forward']+=1
removal={}
for phase in PHASES:
  removal[phase]={}
  for d in sorted(SUPPORT[phase]):
    mask=SUPPORT[phase]-{d}; n=0
    for a in product((0,1), repeat=4):
      for b in product((0,1), repeat=4):
        changed=frozenset(q for q,x,y in zip(DOMS,a,b) if x!=y)
        if suppress(mask,changed) and dec(phase,a)!=dec(phase,b): n+=1
    removal[phase][d]=n
out={'metrics':metrics,'phase_metrics':phase_metrics,'removal':removal,'escapes':escapes}
raw=json.dumps(out,sort_keys=True,separators=(',',':')).encode(); out['digest']=hashlib.sha256(raw).hexdigest()
print(json.dumps(out,indent=2,sort_keys=True))
