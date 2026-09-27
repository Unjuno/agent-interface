from __future__ import annotations
import hashlib,json,random,sys
from dual_edge_contract import *
R=json.load(open('FORMAL_RESULT.json'))
SEED_SMALL=98520260917001;SEED_MULTI=98520260917002;N_SMALL=30000;N_MULTI=50000;K=4

def i(a,b):
 s=max(a[0],b[0]);e=min(a[1],b[1]);return (s,e) if e>s else None
def m(xs):
 xs=sorted(xs)
 if not xs:return 0
 out=[list(xs[0])]
 for s,e in xs[1:]:
  if s<=out[-1][1]:out[-1][1]=max(out[-1][1],e)
  else:out.append([s,e])
 return sum(e-s for s,e in out)
def exhaustive_raw(dlo,dhi,rlo,rhi,w,auth):
 vals=[];avs=[]
 for d in range(dlo,dhi+1):
  for r in range(rlo,rhi+1):
   if d>r:continue
   x=i((d,r),w);vals.append(0 if not x else x[1]-x[0]);avs.append(0 if not x else m([y for a in auth if (y:=i(x,a))]))
 return min(vals),max(vals),min(avs),max(avs)
def choose(rng,dlo,dhi,rlo,rhi):
 fs=[]
 for d in range(dlo,dhi+1):
  lo=max(d,rlo)
  if lo<=rhi:fs.append((d,lo,rhi))
 d,lo,hi=rng.choice(fs);return d,rng.randrange(lo,hi+1)

def main():
 errors=[];h=hashlib.sha256();sm=0;ac=0
 rng=random.Random(SEED_SMALL)
 for case in range(N_SMALL):
  ws=rng.randrange(0,8);we=rng.randrange(ws+1,13);dlo=rng.randrange(0,10);dhi=rng.randrange(dlo,11);rlo=rng.randrange(0,11);rhi=rng.randrange(max(rlo,dlo),13);auth=[]
  for _ in range(rng.randrange(0,3)):
   s=rng.randrange(0,11);auth.append((s,rng.randrange(s+1,13)))
  exp=exhaustive_raw(dlo,dhi,rlo,rhi,(ws,we),auth)
  low=max(0,min(we,rlo)-max(ws,dhi));up=max(0,min(we,rhi)-max(ws,dlo))
  gl=(max(ws,dhi),min(we,rlo));pu=(max(ws,dlo),min(we,rhi));al=m([y for a in auth if gl[1]>gl[0] and (y:=i(gl,a))]);au=m([y for a in auth if pu[1]>pu[0] and (y:=i(pu,a))])
  sm+=int((low,up)==exp[:2]);ac+=int(al<=exp[2] and au>=exp[3]);h.update(json.dumps([case,ws,we,dlo,dhi,rlo,rhi,{'lower_ns':low,'upper_ns':up,'authority_lower_ns':al,'authority_upper_ns':au},exp],sort_keys=True).encode())
 rng=random.Random(SEED_MULTI);cf=0;inf=0;rc=0
 for case in range(N_MULTI):
  ws=rng.randrange(0,20);we=rng.randrange(ws+1,50);acts=[]
  for j in range(rng.randrange(1,6)):
   dlo=rng.randrange(0,40);dhi=rng.randrange(dlo,41);rlo=rng.randrange(0,41);rhi=rng.randrange(max(rlo,dlo),51);auth=[]
   for _ in range(rng.randrange(0,4)):
    s=rng.randrange(0,40);auth.append((s,rng.randrange(s+1,51)))
   acts.append((dlo,dhi,rlo,rhi,auth))
  lowers=[];uppers=[];als=[];aus=[]
  for dlo,dhi,rlo,rhi,auth in acts:
   gl=(max(ws,dhi),min(we,rlo));pu=(max(ws,dlo),min(we,rhi))
   if gl[1]>gl[0]:lowers.append(gl)
   if pu[1]>pu[0]:uppers.append(pu)
   for a in auth:
    if gl[1]>gl[0] and (y:=i(gl,a)):als.append(y)
    if pu[1]>pu[0] and (y:=i(pu,a)):aus.append(y)
  bounds=(m(lowers),m(uppers),m(als),m(aus));inf+=int(not(bounds[2]<=bounds[0]<=bounds[1] and bounds[3]<=bounds[1]))
  for k in range(K):
   phys=[];authp=[]
   for dlo,dhi,rlo,rhi,auth in acts:
    d,r=choose(rng,dlo,dhi,rlo,rhi);x=i((d,r),(ws,we))
    if x:
     phys.append(x)
     for a in auth:
      if y:=i(x,a):authp.append(y)
   p,au=m(phys),m(authp);rc+=1;cf+=int(not(bounds[0]<=p<=bounds[1] and bounds[2]<=au<=bounds[3]));h.update(json.dumps([case,k,p,au,*bounds],sort_keys=True).encode())
 checks={'small_physical_exact':sm==N_SMALL,'small_authority_conservative':ac==N_SMALL,'containment':cf==0,'invariant':inf==0,'realizations':rc==R.get('exact_realizations'),'digest':h.hexdigest()==R.get('case_digest_sha256'),'decision':R.get('decision')=='PASS_DUAL_EDGE_CENSORING_SCOPED','reruns':R.get('formal_reruns')==0}
 errors=[k for k,v in checks.items() if not v];out={'passed':not errors,'errors':errors,'checks':checks,'recomputed_digest':h.hexdigest()};open('AUDIT.json','w').write(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True));raise SystemExit(bool(errors))
if __name__=='__main__':main()
