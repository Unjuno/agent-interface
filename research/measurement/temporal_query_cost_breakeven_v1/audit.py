from fractions import Fraction
import json,hashlib
from pathlib import Path
DEN=40; C={'RECENT':4,'LONG':2,'EVENT':8,'REVERSAL':6}; A={'RECENT':4,'LONG':2,'EVENT':2,'REVERSAL':2}; O=tuple(C)
def counts():
 for r in range(41):
  for l in range(41-r):
   for e in range(41-r-l): yield r,l,e,40-r-l-e
def ex(x,b): return sum(Fraction(x[i],40)*b[O[i]] for i in range(4))
def main():
 r=json.loads(Path('RESULT.json').read_text()); xs=list(counts()); cb=[ex(x,C) for x in xs]; ab=[ex(x,A) for x in xs]
 idbad=sum((cb[i]-ab[i]) != 6*Fraction(xs[i][2],40)+4*Fraction(xs[i][3],40) for i in range(len(xs)))
 iff=sum(((cb[i]-ab[i])==0)!=(xs[i][2]==0 and xs[i][3]==0) for i in range(len(xs)))
 eq=(10,10,10,10); bc=ex(eq,C); ba=ex(eq,A); th={'fixed_to_class':str(11-bc),'class_to_anchor_increment':str(bc-ba),'fixed_to_anchor':str(11-ba)}
 errors=[]
 if len(xs)!=r['simplex_points']: errors.append('simplex_points')
 if (str(min(cb)),str(max(cb)))!=(r['class_budget_min'],r['class_budget_max']): errors.append('class_extrema')
 if (str(min(ab)),str(max(ab)))!=(r['anchor_budget_min'],r['anchor_budget_max']): errors.append('anchor_extrema')
 if idbad or iff: errors.append('identity')
 if th!=r['equal_prior_thresholds']: errors.append('thresholds')
 if not all(r['corruption_controls'].values()): errors.append('controls')
 out={'pass':not errors,'errors':errors,'simplex_points':len(xs),'identity_mismatches':idbad,'iff_mismatches':iff,'equal_prior_thresholds':th}
 out['digest']=hashlib.sha256(json.dumps(out,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 Path('AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
if __name__=='__main__': main()
