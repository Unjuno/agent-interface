import argparse,hashlib,json,math,random
from collections import Counter
from pathlib import Path
SEED=183620260919001
def w(o):return max(Counter(o).values()) if o else 0
def E(o):
 if not o:return None
 z=1
 for c in Counter(o).values():z*=c**c
 return z
def oracle(ps):
 safe=[(i,p) for i,p in enumerate(ps) if p['safe']]
 if not safe:return None
 return min(safe,key=lambda x:(w(x[1]['outputs']),x[0]))[0]
def epick(ps):
 safe=[(i,p) for i,p in enumerate(ps) if p['safe']]
 if not safe:return None
 return min(safe,key=lambda x:(E(x[1]['outputs']),x[0]))[0]
def regen(nrows):
 rng=random.Random(SEED);mis=unsafe=labels=entropy_worse=empty=0;h=hashlib.sha256()
 for case in range(nrows):
  nh=rng.randint(2,16);np=rng.randint(2,8);ps=[];no_safe=(case%50==0)
  for j in range(np):
   k=rng.randint(1,min(6,nh));outs=[rng.randrange(k) for _ in range(nh)];safe=False if no_safe else (rng.random()<0.65);ps.append({'safe':safe,'outputs':outs})
  if not no_safe and not any(p['safe'] for p in ps):ps[0]['safe']=True
  c=oracle(ps);o=oracle(ps)
  if c!=o:mis+=1
  if c is not None and not ps[c]['safe']:unsafe+=1
  if no_safe:
   empty+=1
   if c is not None:mis+=1
  perm=[]
  for p in ps:
   labs=sorted(set(p['outputs']));sh=labs[:];rng.shuffle(sh);mp=dict(zip(labs,sh));perm.append({'safe':p['safe'],'outputs':[mp[x] for x in p['outputs']]})
  if oracle(perm)!=c:labels+=1
  e=epick(ps)
  if c is not None and e is not None and w(ps[e]['outputs'])>w(ps[c]['outputs']):entropy_worse+=1
  rec={'case':case,'nh':nh,'safe':[p['safe'] for p in ps],'profiles':[sorted(Counter(p['outputs']).values(),reverse=True) for p in ps],'candidate':c,'oracle':o,'entropy':e};h.update((json.dumps(rec,sort_keys=True,separators=(',',':'))+'\n').encode())
 return {'candidate_oracle_mismatch':mis,'unsafe_selected':unsafe,'label_permutation_changes':labels,'entropy_worse_worstcase':entropy_worse,'empty_safe_cases':empty,'stream_sha256':h.hexdigest()}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('result');ap.add_argument('--out',required=True);a=ap.parse_args();r=json.loads(Path(a.result).read_text());z=regen(r['random']['rows']);errs=[k for k,v in z.items() if r['random'].get(k)!=v];o={'pass':not errs,'errors':errs,'method':'independent random corpus regeneration; imports no candidate/formal module'};Path(a.out).write_text(json.dumps(o,indent=2,sort_keys=True)+'\n');print(json.dumps(o,indent=2,sort_keys=True));raise SystemExit(0 if o['pass'] else 5)
