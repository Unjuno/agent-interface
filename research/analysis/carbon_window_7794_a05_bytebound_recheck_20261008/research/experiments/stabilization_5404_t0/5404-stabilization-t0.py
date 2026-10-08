import json, random

def run(seed, guarded, n=3):
 r=random.Random(seed); state=[r.randrange(0,8) for _ in range(n)]; steps=0; unsafe=0
 while len(set(state))>1 and steps<30:
  if not guarded and r.random()<.25: unsafe+=1
  target=max(state); i=min(range(n),key=lambda j:state[j]); state[i]=target; steps+=1
 return {'initial':state,'steps':steps,'unsafe_before_stable':unsafe,'stable':len(set(state))==1}
def main():
 out={}
 for g in (False,True):
  v=[run(s,g) for s in range(1000)]; out['guarded' if g else 'unguarded']={'mean_steps':sum(x['steps'] for x in v)/len(v),'unsafe_rate':sum(x['unsafe_before_stable']>0 for x in v)/len(v),'nonconverged':sum(not x['stable'] for x in v)}
 print(json.dumps({'experiment':'5404-stabilization-t0','trials':1000,'replicas':3,'results':out,'scope':'toy epoch repair; no packet loss, effect oracle, authority, or liveness proof'},sort_keys=True,indent=2))
if __name__=='__main__': main()
