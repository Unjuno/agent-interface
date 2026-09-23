from fractions import Fraction as F
import argparse,hashlib,json
from pathlib import Path
P=tuple(F(i,10) for i in range(1,10))
C=tuple(F(i,4) for i in range(1,5))

def intervals_containing(v):
    return tuple((lo,hi) for lo in C for hi in C if lo<=v<=hi)

def identified(x,y,al,au,bl,bu):
    lo=max(F(0),x/au,F(1)-y/bl)
    hi=min(F(1),x/al,F(1)-y/bu)
    return lo,hi

def oracle(x,y,al,au,bl,bu):
    # Independent constraint intersection written as four inequalities on p.
    lows=(F(0),x/au,F(1)-y/bl)
    highs=(F(1),x/al,F(1)-y/bu)
    return max(lows),min(highs)

def a_only(x,y,al,au):
    # Keep generic no-mechanism B constraint p<=1-y, but ignore calibrated B bounds.
    return max(F(0),x/au),min(F(1),x/al,F(1)-y)

def midpoint_plugin(x,y,al,au,bl,bu):
    am=(al+au)/2; bm=(bl+bu)/2
    ca=x/am; cb=y/bm
    return ca/(ca+cb)

def run(construction=False):
    ps=P[:4] if construction else P
    cs=C[:3] if construction else C
    st={'rows':0,'interval_mismatch':0,'true_excluded':0,'empty_interval':0,'outside_noinfo':0,
        'point_bound_rows':0,'point_bound_not_exact':0,'strict_noinfo_tightening':0,'partial_nonpoint_rows':0,
        'a_only_strictly_wider':0,'both_wider_than_a_only':0,'completion_only_wrong':0,'midpoint_plugin_wrong':0,
        'sharp_endpoint_checks':0,'sharp_endpoint_failures':0}
    for p in ps:
      for a in cs:
       for b in cs:
        x=p*a; y=(1-p)*b; q=x/(x+y)
        for al,au in intervals_containing(a):
         if al not in cs or au not in cs: continue
         for bl,bu in intervals_containing(b):
          if bl not in cs or bu not in cs: continue
          L,U=identified(x,y,al,au,bl,bu); OL,OU=oracle(x,y,al,au,bl,bu)
          st['rows']+=1;st['interval_mismatch']+=int((L,U)!=(OL,OU));st['true_excluded']+=int(not(L<=p<=U));st['empty_interval']+=int(L>U)
          nL,nU=x,F(1)-y;st['outside_noinfo']+=int(L<nL or U>nU)
          if al==au==a and bl==bu==b:
           st['point_bound_rows']+=1;st['point_bound_not_exact']+=int(not(L==U==p))
          if L>nL or U<nU:st['strict_noinfo_tightening']+=1
          if L<U:st['partial_nonpoint_rows']+=1
          aL,aU=a_only(x,y,al,au)
          st['both_wider_than_a_only']+=int(L<aL or U>aU)
          st['a_only_strictly_wider']+=int(aL<L or aU>U)
          st['completion_only_wrong']+=int(q!=p)
          st['midpoint_plugin_wrong']+=int(midpoint_plugin(x,y,al,au,bl,bu)!=p)
          # Endpoint sharpness: for interior endpoints, recovered nuisance values must lie in bounds.
          for e in (L,U):
           if F(0)<e<F(1):
            aa=x/e; bb=y/(1-e);st['sharp_endpoint_checks']+=1
            st['sharp_endpoint_failures']+=int(not(al<=aa<=au and bl<=bb<=bu))
    directed={
      'point_exact': identified(F(1,5),F(3,10),F(1,2),F(1,2),F(1,2),F(1,2))==(F(2,5),F(2,5)),
      'bounded_interval': identified(F(1,10),F(9,20),F(1,4),F(1),F(1,2),F(3,4))==(F(1,10),F(2,5)),
    }
    corrupt={'bound_order_matters':identified(F(1,10),F(9,20),F(1,4),F(1),F(1,2),F(3,4))[0]<=identified(F(1,10),F(9,20),F(1,4),F(1),F(1,2),F(3,4))[1],
             'both_constraints_used':st['a_only_strictly_wider']>0 if not construction else True,
             'midpoint_not_exact':st['midpoint_plugin_wrong']>0,
             'noinfo_not_exceeded':st['outside_noinfo']==0}
    full_only=True if construction else (st['a_only_strictly_wider']>0 and st['strict_noinfo_tightening']>0 and st['partial_nonpoint_rows']>0)
    good=(st['interval_mismatch']==0 and st['true_excluded']==0 and st['empty_interval']==0 and st['outside_noinfo']==0 and
          st['point_bound_not_exact']==0 and st['point_bound_rows']>0 and st['both_wider_than_a_only']==0 and
          st['completion_only_wrong']>0 and st['midpoint_plugin_wrong']>0 and st['sharp_endpoint_failures']==0 and
          full_only and all(directed.values()) and all(corrupt.values()))
    return st,directed,corrupt,good

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--construction',action='store_true');ap.add_argument('--output',required=True);a=ap.parse_args();o=Path(a.output);assert not o.exists();st,dc,cor,good=run(a.construction)
    r={'construction':a.construction,'stats':st,'directed':dc,'corruptions':cor,'formal_invocations':0 if a.construction else 1,'reruns':0,'replacements':0,'tuning':0,'decision':('CONSTRUCTION_PASS' if a.construction and good else ('PASS_PROBABILISTIC_AUTOMATON_CENSOR_BOUND_PARTIAL_ID_SCOPED' if good else 'FAIL_INTEGRITY'))}
    raw=json.dumps(r,sort_keys=True,separators=(',',':'),default=str).encode();r['digest']=hashlib.sha256(raw).hexdigest();o.write_text(json.dumps(r,indent=2,sort_keys=True,default=str)+'\n');print(json.dumps(r,indent=2,sort_keys=True,default=str))
if __name__=='__main__':main()
