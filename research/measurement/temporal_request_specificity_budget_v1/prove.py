from __future__ import annotations
from fractions import Fraction
import argparse, hashlib, json
from pathlib import Path

TASK='TEMPORAL-REQUEST-SPECIFICITY-BUDGET-LATTICE-20260918-001'
GRID=tuple(range(0,1001,25))
ANCHORS=tuple(range(250,826,25))
RECENT=tuple(range(900,1001,25))
UNIVERSAL_WITNESS=(225,325,425,500,600,700,800,900,925,950,975)
EVENT_CLASS_WITNESS=(225,325,425,525,625,725,825,925)
REV_CLASS_WITNESS=(225,375,525,675,825,975)


def recent(s): return sum(900<=t<=1000 for t in s)>=4
def longb(s): return any(t<=300 for t in s) and any(t>=900 for t in s)
def event(s,a): return any(a-100<=t<a for t in s) and any(a<t<=a+100 for t in s)
def rev(s,a): return any(a-150<=t<=a-25 for t in s) and any(a+25<=t<=a+150 for t in s)
def event_left(a): return frozenset(range(a-100,a,25))
def event_right(a): return frozenset(range(a+25,a+101,25))
def rev_left(a): return frozenset(range(a-150,a,25))
def rev_right(a): return frozenset(range(a+25,a+151,25))
def hit(s, region): return bool(set(s)&set(region))
def pairwise_disjoint(regions): return all(not (regions[i]&regions[j]) for i in range(len(regions)) for j in range(i+1,len(regions)))

def all_windows(start,end,width):
    vals=tuple(range(start,end+1,25))
    return tuple(frozenset(vals[i:i+width]) for i in range(len(vals)-width+1))

EVENT_WINDOWS=all_windows(150,925,4)
REV_WINDOWS=all_windows(100,975,6)
EVENT_CERT=tuple(EVENT_WINDOWS[i] for i in range(0,len(EVENT_WINDOWS),4))
REV_CERT=tuple(REV_WINDOWS[i] for i in range(0,len(REV_WINDOWS),6))

UNIVERSAL_CERT=(
    frozenset(range(900,1001,25)),
    frozenset(range(150,276,25)),
    frozenset(range(300,376,25)),
    frozenset(range(400,476,25)),
    frozenset(range(500,576,25)),
    frozenset(range(600,676,25)),
    frozenset(range(700,776,25)),
    frozenset(range(800,876,25)),
)

def event_class_valid(s): return all(event(s,a) for a in ANCHORS)
def rev_class_valid(s): return all(rev(s,a) for a in ANCHORS)
def universal_valid(s): return recent(s) and longb(s) and event_class_valid(s) and rev_class_valid(s)

def anchored_event_witness(a): return (a-25,a+25)
def anchored_rev_witness(a): return (a-25,a+25)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',required=True); a=ap.parse_args(); out=Path(a.output); assert not out.exists()

    event_regions={event_left(x) for x in ANCHORS}|{event_right(x) for x in ANCHORS}
    rev_regions={rev_left(x) for x in ANCHORS}|{rev_right(x) for x in ANCHORS}
    event_equiv=event_regions==set(EVENT_WINDOWS)
    rev_equiv=rev_regions==set(REV_WINDOWS)

    event_lower=len(EVENT_CERT) if pairwise_disjoint(EVENT_CERT) else -1
    rev_lower=len(REV_CERT) if pairwise_disjoint(REV_CERT) else -1
    event_cert_genuine=all(x in event_regions for x in EVENT_CERT)
    rev_cert_genuine=all(x in rev_regions for x in REV_CERT)

    event_upper_ok=len(EVENT_CLASS_WITNESS)==8 and all(hit(EVENT_CLASS_WITNESS,w) for w in EVENT_WINDOWS) and event_class_valid(EVENT_CLASS_WITNESS)
    rev_upper_ok=len(REV_CLASS_WITNESS)==6 and all(hit(REV_CLASS_WITNESS,w) for w in REV_WINDOWS) and rev_class_valid(REV_CLASS_WITNESS)

    anchored=[]
    anchored_ok=True
    for anchor in ANCHORS:
        ew=anchored_event_witness(anchor); rw=anchored_rev_witness(anchor)
        er_disjoint=not (event_left(anchor)&event_right(anchor))
        rr_disjoint=not (rev_left(anchor)&rev_right(anchor))
        eok=len(ew)==2 and all(t in GRID for t in ew) and event(ew,anchor) and er_disjoint
        rok=len(rw)==2 and all(t in GRID for t in rw) and rev(rw,anchor) and rr_disjoint
        anchored_ok &= eok and rok
        anchored.append({'anchor':anchor,'event_witness':list(ew),'event_pass':eok,'reversal_witness':list(rw),'reversal_pass':rok})

    recent_min=4
    long_regions=(frozenset(t for t in GRID if t<=300),frozenset(t for t in GRID if t>=900))
    long_min=2 if pairwise_disjoint(long_regions) and longb((300,900)) else -1

    universal_cert_disjoint=pairwise_disjoint(UNIVERSAL_CERT)
    universal_lower=4+(len(UNIVERSAL_CERT)-1) if universal_cert_disjoint else -1
    universal_upper_ok=len(UNIVERSAL_WITNESS)==11 and universal_valid(UNIVERSAL_WITNESS)

    class_only={'RECENT_DENSE':recent_min,'LONG_BASELINE':long_min,'EVENT_CENTERED':event_lower,'REVERSAL_BRACKET':rev_lower}
    full_specific={'RECENT_DENSE':4,'LONG_BASELINE':2,'EVENT_CENTERED':2,'REVERSAL_BRACKET':2}
    mean_class=sum(Fraction(v,1) for v in class_only.values())/4
    mean_specific=sum(Fraction(v,1) for v in full_specific.values())/4

    corrupt={}
    bad=list(EVENT_CERT); bad[-1]=bad[-2]; corrupt['event_certificate_overlap']=not pairwise_disjoint(tuple(bad))
    bad=list(REV_CERT); bad[-1]=bad[-2]; corrupt['reversal_certificate_overlap']=not pairwise_disjoint(tuple(bad))
    corrupt['event_witness_miss']=not all(hit(EVENT_CLASS_WITNESS[:-1],w) for w in EVENT_WINDOWS)
    corrupt['reversal_witness_miss']=not all(hit(REV_CLASS_WITNESS[:-1],w) for w in REV_WINDOWS)
    a0=ANCHORS[0]; corrupt['anchored_event_side_missing']=not event((a0-25,),a0)
    corrupt['anchored_reversal_side_missing']=not rev((a0+25,),a0)
    corrupt['mean_arithmetic']=Fraction(4+2+8+6,4)==5 and Fraction(4+2+2+2,4)==Fraction(5,2)

    checks={
      'event_relation_window_equivalence':event_equiv,
      'reversal_relation_window_equivalence':rev_equiv,
      'event_certificate_disjoint':pairwise_disjoint(EVENT_CERT),
      'event_certificate_genuine':event_cert_genuine,
      'event_lower_8':event_lower==8,
      'event_witness_8':event_upper_ok,
      'reversal_certificate_disjoint':pairwise_disjoint(REV_CERT),
      'reversal_certificate_genuine':rev_cert_genuine,
      'reversal_lower_6':rev_lower==6,
      'reversal_witness_6':rev_upper_ok,
      'anchored_all_48':anchored_ok,
      'recent_min_4':recent_min==4 and recent((900,925,950,975)) and not recent((900,925,950)),
      'long_min_2':long_min==2,
      'universal_parent_lower_11':universal_lower==11,
      'universal_parent_witness_11':universal_upper_ok,
      'means':mean_class==5 and mean_specific==Fraction(5,2),
      'corruptions':all(corrupt.values())
    }
    decision='PASS_TEMPORAL_REQUEST_SPECIFICITY_BUDGET_LATTICE_SCOPED' if all(checks.values()) else 'FAIL_INTEGRITY'
    result={
      'task':TASK,'decision':decision,'formal_invocations':1,'reruns':0,'replacements':0,'tuning':0,
      'grid':list(GRID),'anchors':list(ANCHORS),
      'class_only_minima':class_only,'class_anchor_minima':full_specific,
      'class_only_mean':{'num':mean_class.numerator,'den':mean_class.denominator},
      'class_anchor_mean':{'num':mean_specific.numerator,'den':mean_specific.denominator},
      'event':{'window_count':len(EVENT_WINDOWS),'certificate_count':len(EVENT_CERT),'certificate_regions':[sorted(x) for x in EVENT_CERT],'witness':list(EVENT_CLASS_WITNESS)},
      'reversal':{'window_count':len(REV_WINDOWS),'certificate_count':len(REV_CERT),'certificate_regions':[sorted(x) for x in REV_CERT],'witness':list(REV_CLASS_WITNESS)},
      'anchored_witnesses':anchored,'universal_parent_recheck':{'lower_bound':universal_lower,'witness':list(UNIVERSAL_WITNESS),'valid':universal_upper_ok},
      'corruption_controls':corrupt,'checks':checks
    }
    raw=json.dumps(result,sort_keys=True,separators=(',',':')).encode(); result['digest']=hashlib.sha256(raw).hexdigest()
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2,sort_keys=True))
    raise SystemExit(0 if decision.startswith('PASS_') else 1)

if __name__=='__main__': main()
