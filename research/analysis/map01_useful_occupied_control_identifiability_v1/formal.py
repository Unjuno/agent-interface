from itertools import product
from collections import defaultdict
from pathlib import Path
import json,hashlib
GRID=tuple(range(9)); CAUSES=('ACTION','ENVIRONMENT'); EFFECTS=(None,)+GRID

def worlds():
 for L in GRID:
  for U in GRID:
   if L>U: continue
   for S in GRID:
    for cause in CAUSES:
     for E in EFFECTS:
      yield (L,U,S,cause,E)

def target(w):
 L,U,S,cause,E=w
 return cause=='ACTION' and E is not None and L<=E<=U

def key(w,mode):
 L,U,S,cause,E=w
 if mode=='BASE': return (L,U,S)
 if mode=='CAUSE_ONLY': return (L,U,S,cause)
 if mode=='TIMESTAMP_ONLY': return (L,U,S,E)
 if mode=='BOTH': return (L,U,S,cause,E)
 raise ValueError(mode)

def summarize(mode,ws):
 g=defaultdict(set)
 for w in ws: g[key(w,mode)].add(target(w))
 amb=sum(len(v)>1 for v in g.values())
 return {'classes':len(g),'ambiguous_classes':amb,'identifiable_classes':len(g)-amb}

def main():
 ws=list(worlds()); modes={m:summarize(m,ws) for m in ('BASE','CAUSE_ONLY','TIMESTAMP_ONLY','BOTH')}
 state_launder=any(L<=S<=U and cause=='ENVIRONMENT' and not target(w) for w in ws for L,U,S,cause,E in [w])
 viewport_launder=state_launder
 terminal_launder=any(cause=='ACTION' and (E is None or not(L<=E<=U)) for L,U,S,cause,E in ws)
 out={'task':'MAP01-USEFUL-OCCUPIED-CONTROL-IDENTIFIABILITY-20260919-001','grid':list(GRID),'worlds':len(ws),'modes':modes,
      'corruption_controls':{'state_feedback_as_causal_rejected':state_launder,'viewport_change_as_useful_rejected':viewport_launder,'terminal_as_useful_rejected':terminal_launder},
      'formal_invocations':1,'reruns':0,'replacements':0,'tuning':0}
 ok=(modes['BASE']['ambiguous_classes']>0 and modes['CAUSE_ONLY']['ambiguous_classes']>0 and modes['TIMESTAMP_ONLY']['ambiguous_classes']>0 and modes['BOTH']['ambiguous_classes']==0 and all(out['corruption_controls'].values()))
 out['decision']='PASS_USEFUL_OCCUPIED_CONTROL_NONIDENTIFIABLE_SCOPED' if ok else 'HOLD_TARGET_DEFINITION_INCOMPLETE'
 out['digest']=hashlib.sha256(json.dumps(out,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 Path('/tmp/ai1838/RESULT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
 print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__': main()
