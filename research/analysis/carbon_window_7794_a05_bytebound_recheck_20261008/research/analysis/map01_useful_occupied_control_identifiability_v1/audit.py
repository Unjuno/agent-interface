from pathlib import Path
import json,hashlib
GRID=range(9); EFF=(None,)+tuple(GRID)

def val(L,U,c,e): return c==1 and e is not None and L<=e<=U

def counts(mode):
 d={}
 for L in GRID:
  for U in GRID:
   if L>U: continue
   for S in GRID:
    for c in (0,1):
     for e in EFF:
      if mode==0:k=(L,U,S)
      elif mode==1:k=(L,U,S,c)
      elif mode==2:k=(L,U,S,e)
      else:k=(L,U,S,c,e)
      mask=d.get(k,0); mask |= 2 if val(L,U,c,e) else 1; d[k]=mask
 return len(d),sum(v==3 for v in d.values())

def main():
 r=json.loads(Path('/tmp/ai1838/RESULT.json').read_text()); names=('BASE','CAUSE_ONLY','TIMESTAMP_ONLY','BOTH'); errors=[]; observed={}
 for i,n in enumerate(names):
  cls,amb=counts(i); observed[n]={'classes':cls,'ambiguous_classes':amb,'identifiable_classes':cls-amb}
  if observed[n]!=r['modes'][n]: errors.append(n)
 if r['worlds']!=8100: errors.append('worlds')
 if not all(r['corruption_controls'].values()): errors.append('controls')
 if r['formal_invocations']!=1 or any(r[x]!=0 for x in ('reruns','replacements','tuning')): errors.append('discipline')
 out={'pass':not errors,'errors':errors,'modes':observed,'worlds':8100}
 out['digest']=hashlib.sha256(json.dumps(out,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 Path('/tmp/ai1838/AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
