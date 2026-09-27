from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

GRID=tuple(range(0,1001,25)); ANCHORS=tuple(range(250,826,25))

def event(s,a): return any(a-100<=t<a for t in s) and any(a<t<=a+100 for t in s)
def rev(s,a): return any(a-150<=t<=a-25 for t in s) and any(a+25<=t<=a+150 for t in s)
def recent(s): return sum(900<=t<=1000 for t in s)>=4
def longb(s): return any(t<=300 for t in s) and any(t>=900 for t in s)
def windows(start,end,width):
    v=tuple(range(start,end+1,25)); return tuple(frozenset(v[i:i+width]) for i in range(len(v)-width+1))
def disjoint(regions): return all(not(regions[i]&regions[j]) for i in range(len(regions)) for j in range(i+1,len(regions)))
def valid_universal(s): return recent(s) and longb(s) and all(event(s,a) for a in ANCHORS) and all(rev(s,a) for a in ANCHORS)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--result',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();r=json.loads(Path(a.result).read_text());o=Path(a.output);assert not o.exists()
    ew=windows(150,925,4); rw=windows(100,975,6)
    ec=tuple(ew[i] for i in range(0,len(ew),4)); rc=tuple(rw[i] for i in range(0,len(rw),6))
    e_w=tuple(r['event']['witness']); r_w=tuple(r['reversal']['witness'])
    anchored_ok=all(len(x['event_witness'])==2 and event(tuple(x['event_witness']),x['anchor']) and len(x['reversal_witness'])==2 and rev(tuple(x['reversal_witness']),x['anchor']) for x in r['anchored_witnesses'])
    u=tuple(r['universal_parent_recheck']['witness'])
    checks={
      'decision':r['decision']=='PASS_TEMPORAL_REQUEST_SPECIFICITY_BUDGET_LATTICE_SCOPED',
      'formal':r['formal_invocations']==1 and r['reruns']==0 and r['replacements']==0 and r['tuning']==0,
      'class_only':r['class_only_minima']=={'RECENT_DENSE':4,'LONG_BASELINE':2,'EVENT_CENTERED':8,'REVERSAL_BRACKET':6},
      'specific':r['class_anchor_minima']=={'RECENT_DENSE':4,'LONG_BASELINE':2,'EVENT_CENTERED':2,'REVERSAL_BRACKET':2},
      'means':r['class_only_mean']=={'num':5,'den':1} and r['class_anchor_mean']=={'num':5,'den':2},
      'event_cert':len(ec)==8 and disjoint(ec),
      'event_witness':len(e_w)==8 and all(any(t in w for t in e_w) for w in ew) and all(event(e_w,x) for x in ANCHORS),
      'rev_cert':len(rc)==6 and disjoint(rc),
      'rev_witness':len(r_w)==6 and all(any(t in w for t in r_w) for w in rw) and all(rev(r_w,x) for x in ANCHORS),
      'anchored':anchored_ok and len(r['anchored_witnesses'])==24,
      'universal':r['universal_parent_recheck']['lower_bound']==11 and len(u)==11 and valid_universal(u),
      'corruptions':all(r['corruption_controls'].values()),
    }
    status='PASS' if all(checks.values()) else 'FAIL'; out={'status':status,'checks':checks,'result_sha256':hashlib.sha256(Path(a.result).read_bytes()).hexdigest()}
    o.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True));raise SystemExit(0 if status=='PASS' else 1)
if __name__=='__main__':main()
