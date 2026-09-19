from fractions import Fraction
import json,hashlib
from pathlib import Path
DEN=40
BCLASS={'RECENT':4,'LONG':2,'EVENT':8,'REVERSAL':6}
BANCH={'RECENT':4,'LONG':2,'EVENT':2,'REVERSAL':2}
ORDER=('RECENT','LONG','EVENT','REVERSAL')

def all_counts():
 for a in range(41):
  for b in range(41-a):
   for c in range(41-a-b):
    yield a,b,c,40-a-b-c

def expect(counts,b):
 return sum(Fraction(counts[i],40)*b[ORDER[i]] for i in range(4))

def main():
 r=json.loads(Path('/tmp/ai1819/RESULT.json').read_text())
 errors=[]; n=0; cvals=[]; avals=[]; idbad=0; iff=0
 for counts in all_counts():
  n+=1; bc=expect(counts,BCLASS); ba=expect(counts,BANCH)
  cvals.append(bc); avals.append(ba)
  delta=bc-ba; expected=6*Fraction(counts[2],40)+4*Fraction(counts[3],40)
  idbad += delta!=expected
  iff += ((delta==0) != (counts[2]==0 and counts[3]==0))
 if n!=r['simplex_points']: errors.append('simplex_points')
 if (str(min(cvals)),str(max(cvals)))!=(r['class_budget_min'],r['class_budget_max']): errors.append('class_extrema')
 if (str(min(avals)),str(max(avals)))!=(r['anchor_budget_min'],r['anchor_budget_max']): errors.append('anchor_extrema')
 if idbad!=r['anchor_saving_identity_mismatches']: errors.append('identity')
 if iff!=r['zero_iff_no_event_reversal_mismatches']: errors.append('iff')
 eq=(10,10,10,10); bc=expect(eq,BCLASS); ba=expect(eq,BANCH)
 th={'fixed_to_class':str(11-bc),'class_to_anchor_increment':str(bc-ba),'fixed_to_anchor':str(11-ba)}
 if th!=r['equal_prior_thresholds']: errors.append('equal_thresholds')
 if not all(r['corruption_controls'].values()): errors.append('corruption_controls')
 if r['formal_invocations']!=1 or any(r[k]!=0 for k in ('reruns','replacements','tuning')): errors.append('invocation_discipline')
 audit={'pass':not errors,'errors':errors,'simplex_points':n,'identity_mismatches':idbad,'iff_mismatches':iff,'equal_prior_thresholds':th}
 audit['digest']=hashlib.sha256(json.dumps(audit,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 Path('/tmp/ai1819/AUDIT.json').write_text(json.dumps(audit,indent=2,sort_keys=True)+'\n')
 print(json.dumps(audit,indent=2,sort_keys=True))
if __name__=='__main__': main()
