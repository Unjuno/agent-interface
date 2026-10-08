import itertools,random
from contract import Record,CRITICAL,STATE_KINDS
SEED=100820260917002
RANDOM_BATCHES=25000
EXHAUSTIVE_ALPHABET=[
 ('s0','t0','r0','FRAME','fresh'),('s0','t0','r0','FRAME','stale'),
 ('s0','t0','r0','STATUS','fresh'),('s0','t0','r0','STATUS','stale'),
 ('s0','t0','r0','FOCUS_CHANGED','fresh'),('s0','t0','r0','FOCUS_CHANGED','stale'),
 ('s0','t0','r0','LEASE_EXPIRED','fresh'),('s0','t0','r0','LEASE_EXPIRED','stale'),
 ('s1','t1','r1','FRAME','fresh'),('s1','t1','r1','FRAME','stale'),
 ('s1','t1','r1','STATUS','fresh'),('s1','t1','r1','STATUS','stale'),
 ('s1','t1','r1','FOCUS_CHANGED','fresh'),('s1','t1','r1','FOCUS_CHANGED','stale'),
 ('s1','t1','r1','LEASE_EXPIRED','fresh'),('s1','t1','r1','LEASE_EXPIRED','stale')]
def random_batches():
 rng=random.Random(SEED); kinds=sorted(CRITICAL|STATE_KINDS)
 for b in range(RANDOM_BATCHES):
  now=100000+rng.randrange(0,10000); max_age=rng.randrange(0,250); n=rng.randrange(1,32); rows=[]
  for i in range(n):
   age=rng.randrange(0,500); t=max(0,now-age); scope=rng.randrange(0,8)
   rows.append(Record(f'b{b}e{i}',i,t,f's{scope%3}',f't{scope%4}',f'r{scope%2}',rng.choice(kinds)))
  yield rows,now,max_age

def exhaustive_batches():
 now=100; max_age=10; case=0
 for n in (1,2,3):
  for combo in itertools.product(EXHAUSTIVE_ALPHABET,repeat=n):
   rows=[]
   for i,(s,t,r,k,agec) in enumerate(combo):
    ts=95 if agec=='fresh' else 80
    rows.append(Record(f'x{case}e{i}',i,ts,s,t,r,k))
   yield rows,now,max_age;case+=1
