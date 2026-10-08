from __future__ import annotations
import hashlib,json,random,sys
from pathlib import Path
from parent_996 import Edge,compose as parent_compose
from candidate import ClockedEdge,compose_clock_bound
from oracle import oracle
TASK='PHYSICAL-EDGE-CLOCK-DOMAIN-GATE-A2-20260918-002'
SEED=100220260917001
N=250_000
PARENT_BLOB='a1344409ea6383c6394e991ac0b59fa7689978ef'
DS=['CONFIRMED_PHYSICAL_DOWN','OWNER_ALREADY_HELD','PREEXISTING_PHYSICAL_DOWN','PRESS_UNCONFIRMED']
US=['CONFIRMED_PHYSICAL_UP','NOOP_ALREADY_UP','FOREIGN_OR_STALE_DOWN','OWNER_PHYSICAL_MISMATCH','RELEASE_UNCONFIRMED']

def git_blob(path):
 b=Path(path).read_bytes();return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def mk(status_d='CONFIRMED_PHYSICAL_DOWN',status_u='CONFIRMED_PHYSICAL_UP',div=(10,12),uiv=(20,22),domain='perf',epoch='bootA'):
 d=dict(edge='down',status=status_d,actuation_id='a',owner_id='o',intent_token='i',key='F8',interval=div if status_d=='CONFIRMED_PHYSICAL_DOWN' else None,clock_domain=domain,clock_epoch=epoch)
 u=dict(edge='up',status=status_u,actuation_id='a',owner_id='o',intent_token='i',key='F8',interval=uiv if status_u=='CONFIRMED_PHYSICAL_UP' else None,clock_domain=domain,clock_epoch=epoch)
 return d,u
def to_obj(r):
 e=Edge(r['edge'],r['status'],r['actuation_id'],r['owner_id'],r['intent_token'],r['key'],r['interval'])
 return ClockedEdge(e,r.get('clock_domain'),r.get('clock_epoch'))
def norm(r): return (r['status'],r['actuation'],r['grants_input_authority'])
def call(d,u):return norm(compose_clock_bound(to_obj(d),to_obj(u)))
def parent(d,u):return norm(parent_compose(to_obj(d).edge,to_obj(u).edge))

def controls():
 tests=[]
 d,u=mk(); tests.append(('same_valid',d,u,'COMPOSED_PHYSICAL_ACTUATION'))
 d,u=mk();u['clock_domain']='mono';tests.append(('domain_mismatch',d,u,'CLOCK_DOMAIN_MISMATCH'))
 d,u=mk();u['clock_epoch']='bootB';tests.append(('epoch_mismatch',d,u,'CLOCK_DOMAIN_MISMATCH'))
 for field in ('clock_domain','clock_epoch'):
  d,u=mk();d[field]=None;tests.append((f'missing_down_{field}',d,u,'CLOCK_PROVENANCE_MISSING'))
  d,u=mk();u[field]=' ';tests.append((f'blank_up_{field}',d,u,'CLOCK_PROVENANCE_MISSING'))
 d,u=mk();u['owner_id']='x';tests.append(('lineage',d,u,'LINEAGE_MISMATCH'))
 d,u=mk(status_d='PRESS_UNCONFIRMED');tests.append(('incomplete',d,u,'INCOMPLETE_EDGE_EVIDENCE'))
 d,u=mk(div=(10,21),uiv=(20,22));tests.append(('overlap',d,u,'EDGE_ORDER_AMBIGUOUS'))
 d,u=mk(div=(12,10),uiv=(20,22));tests.append(('reversed_down',d,u,'EXC:ValueError'))
 d,u=mk(div=(10,12),uiv=(22,20));tests.append(('reversed_up',d,u,'EXC:ValueError'))
 out={}
 for name,d,u,exp in tests:
  try:g=call(d,u)[0]
  except Exception as e:g='EXC:'+type(e).__name__
  out[name]=g==exp
 return out

def main(out):
 out=Path(out)
 if out.exists():raise SystemExit('result exists')
 if git_blob(Path(__file__).with_name('parent_996.py'))!=PARENT_BLOB:raise SystemExit('FAIL_SOURCE_IDENTITY')
 ctr=controls()
 rng=random.Random(SEED); mism=parent_reg=cross_comp=authority=malformed_escape=0; composed=0;same_valid=0;cross_rows=0
 status_counts={}
 for i in range(N):
  sd=rng.choice(DS);su=rng.choice(US)
  a=rng.randrange(0,200);b=a+rng.randrange(0,8);c=b+rng.randrange(-3,10);e=max(c,c+rng.randrange(0,8))
  # negative c can only occur from b<3; clamp interval endpoints separately to create malformed controls sometimes.
  div=(a,b);uiv=(c,e)
  domd=rng.choice(['perf','mono','clockX',None,'']);domu=rng.choice(['perf','mono','clockX',None,''])
  epd=rng.choice(['bootA','bootB','e7',None,'']);epu=rng.choice(['bootA','bootB','e7',None,''])
  d,u=mk(sd,su,div,uiv,domd,epd);u['clock_domain']=domu;u['clock_epoch']=epu
  mode=rng.randrange(20)
  if mode==0:u['intent_token']='other'
  elif mode==1:d['actuation_id']=' '
  try:
   got=call(d,u)
  except ValueError:
   try: oracle(d,u)
   except ValueError: continue
   malformed_escape+=1;continue
  try:exp=oracle(d,u)
  except ValueError:
   malformed_escape+=1;continue
  if got!=exp:mism+=1
  status_counts[got[0]]=status_counts.get(got[0],0)+1
  if got[2] is not False:authority+=1
  clocks_ok=all(type(x) is str and bool(x.strip()) for x in (d.get('clock_domain'),d.get('clock_epoch'),u.get('clock_domain'),u.get('clock_epoch'))) and (d['clock_domain'],d['clock_epoch'])==(u['clock_domain'],u['clock_epoch'])
  if sd=='CONFIRMED_PHYSICAL_DOWN' and su=='CONFIRMED_PHYSICAL_UP' and clocks_ok and all(d[k]==u[k] for k in ('actuation_id','owner_id','intent_token','key')):
   same_valid+=1
   try:p=parent(d,u)
   except ValueError:continue
   if got!=p:parent_reg+=1
  elif sd=='CONFIRMED_PHYSICAL_DOWN' and su=='CONFIRMED_PHYSICAL_UP' and not clocks_ok:
   cross_rows+=1
   if got[0]=='COMPOSED_PHYSICAL_ACTUATION':cross_comp+=1
  if got[0]=='COMPOSED_PHYSICAL_ACTUATION':composed+=1
 decision='PASS_PHYSICAL_EDGE_CLOCK_DOMAIN_GATE_A2_SCOPED'
 if cross_comp:decision='FAIL_CROSS_CLOCK_COMPOSITION'
 elif parent_reg:decision='FAIL_PARENT_DEGENERATION'
 elif mism or authority or malformed_escape or not all(ctr.values()):decision='FAIL_INTEGRITY'
 result={'task':TASK,'decision':decision,'seed':SEED,'pairs':N,'candidate_oracle_mismatch':mism,'same_clock_parent_cases':same_valid,'same_clock_parent_mismatch':parent_reg,'cross_or_missing_clock_cases':cross_rows,'cross_clock_compositions':cross_comp,'composed':composed,'authority_promotions':authority,'malformed_oracle_divergence':malformed_escape,'fixed_controls':ctr,'status_counts':status_counts,'parent_git_blob':PARENT_BLOB,'primary_invocations':1,'reruns':0,'replacements':0,'tuning':0,'source_sha256':{x:hashlib.sha256(Path(__file__).with_name(x).read_bytes()).hexdigest() for x in ('parent_996.py','candidate.py','oracle.py','runner.py')}}
 out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,sort_keys=True))
if __name__=='__main__':main(sys.argv[1])
