import argparse,hashlib,json
from pathlib import Path
GRID=tuple(range(0,1001,25)); ANCHORS=tuple(range(250,826,25))
RECENT=set(range(900,1001,25))
CERT=[
 ('REV_L_300',set(range(150,276,25))),
 ('EVENT_R_275',set(range(300,376,25))),
 ('EVENT_R_375',set(range(400,476,25))),
 ('EVENT_R_475',set(range(500,576,25))),
 ('EVENT_R_575',set(range(600,676,25))),
 ('EVENT_R_675',set(range(700,776,25))),
 ('EVENT_R_775',set(range(800,876,25))),
]
WITNESS=(225,325,425,500,600,700,800,900,925,950,975)
def recent(s): return sum(900<=t<=1000 for t in s)>=4
def longb(s): return any(t<=300 for t in s) and any(t>=900 for t in s)
def event(s,a): return any(a-100<=t<a for t in s) and any(a<t<=a+100 for t in s)
def rev(s,a): return any(a-150<=t<=a-25 for t in s) and any(a+25<=t<=a+150 for t in s)
def pairwise_disjoint(sets): return all(not sets[i]&sets[j] for i in range(len(sets)) for j in range(i+1,len(sets)))
def valid_witness(s): return len(set(s))==len(s) and all(t in GRID for t in s) and recent(s) and longb(s) and all(event(s,a) for a in ANCHORS) and all(rev(s,a) for a in ANCHORS)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();p=Path(a.output);assert not p.exists()
 regions=[RECENT]+[x[1] for x in CERT]
 cert_names=[x[0] for x in CERT]
 expected=['REV_L_300','EVENT_R_275','EVENT_R_375','EVENT_R_475','EVENT_R_575','EVENT_R_675','EVENT_R_775']
 lower=4+len(CERT)
 corrupt={
  'drop_recent':not valid_witness(tuple(x for x in WITNESS if x!=975)),
  'drop_certificate_hit':not valid_witness(tuple(x for x in WITNESS if x!=600)),
  'alter_anchor':not event(WITNESS,2500),
  'overlap_detected':not pairwise_disjoint([RECENT,set(range(875,926,25))]+[x[1] for x in CERT[1:]])
 }
 r={'grid':list(GRID),'anchors':list(ANCHORS),'certificate_names':cert_names,'certificate_expected':expected,'certificate_region_sizes':[len(x) for x in regions],
    'certificate_pairwise_disjoint':pairwise_disjoint(regions),'lower_bound':lower,'witness':list(WITNESS),'witness_size':len(WITNESS),'witness_valid':valid_witness(WITNESS),
    'event_anchors_passed':sum(event(WITNESS,a) for a in ANCHORS),'reversal_anchors_passed':sum(rev(WITNESS,a) for a in ANCHORS),'corruption_controls':corrupt,
    'formal_invocations':1,'reruns':0}
 r['decision']='PASS_TEMPORAL_FIXED_SCHEDULE_MIN_BUDGET_11_SCOPED' if lower==11 and r['certificate_pairwise_disjoint'] and cert_names==expected and r['witness_size']==11 and r['witness_valid'] and all(corrupt.values()) else 'FAIL_INTEGRITY'
 r['digest']=hashlib.sha256(json.dumps(r,sort_keys=True,separators=(',',':')).encode()).hexdigest();p.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps(r,indent=2,sort_keys=True))
if __name__=='__main__':main()
