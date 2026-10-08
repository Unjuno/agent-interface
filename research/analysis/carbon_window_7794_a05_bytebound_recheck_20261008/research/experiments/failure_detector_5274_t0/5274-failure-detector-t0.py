import json, random

def run(seed, fp, fn, n=1000):
 r=random.Random(seed); unsafe=abstain=miss=0
 for _ in range(n):
  failed=r.random()<.25; suspicion=(failed and r.random()>=fn) or ((not failed) and r.random()<fp)
  if suspicion: abstain+=1; miss+=int(failed and not suspicion)
  else: unsafe+=int(failed)
 return unsafe,abstain,miss
def main():
 out=[]
 for fp,fn in ((0,.0),(.01,.1),(.05,.3),(.1,.5)):
  v=[run(s,fp,fn) for s in range(500)]; out.append({'false_positive':fp,'false_negative':fn,'unsafe_commit':sum(x[0] for x in v)/500,'abstain':sum(x[1] for x in v)/500,'miss':sum(x[2] for x in v)/500})
 print(json.dumps({'experiment':'5274-failure-detector-t0','trials':500,'events':1000,'rows':out,'scope':'toy crash/suspicion detector; no consensus or semantic effect model'},sort_keys=True,indent=2))
if __name__=='__main__': main()
