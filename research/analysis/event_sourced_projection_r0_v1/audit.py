import argparse,itertools,json,hashlib
from pathlib import Path
E=('SET0','SET1','INC','DOUBLE','TOGGLE','ADVANCE_GEN');I=(0,False,0)
def step(s,e):
 x,f,g=s
 if e=='SET0':x=0
 elif e=='SET1':x=1
 elif e=='INC':x=(x+1)%8
 elif e=='DOUBLE':x=(x*2)%8
 elif e=='TOGGLE':f=not f
 elif e=='ADVANCE_GEN':g+=1
 return x,f,g
def fold(q):
 s=I
 for e in q:s=step(s,e)
 return s
def pd(q):
 h=b'\0'*32
 for n,e in enumerate(q):h=hashlib.sha256(h+json.dumps([n,e],separators=(',',':')).encode()).digest()
 return h.hex()
def rcpt(n,d,s):return hashlib.sha256(json.dumps({'index':n,'prefix_digest':d,'state':list(s)},sort_keys=True,separators=(',',':')).encode()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--result',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();r=json.loads(Path(a.result).read_text())
 seqs=sum(len(E)**n for n in range(7));checks=sum((n+1)*(len(E)**n) for n in range(7));proj=0;cpbad=0;dup=0;missing=0;oob=0;order={};orderbad=False;indexalias=False
 for n in range(7):
  states=set()
  for q in itertools.product(E,repeat=n):
   f=fold(q);states.add(f)
   s=I
   for e in q:s=step(s,e)
   proj+=s!=f
   for cut in range(n+1):
    pre=q[:cut];s=fold(pre);d=pd(pre);receipt=rcpt(cut,d,s);cur=s
    if receipt!=rcpt(cut,d,s):cpbad+=1
    for e in q[cut:]:cur=step(cur,e)
    cpbad+=cur!=f
   oob+=(((f[0]+1)%8,f[1],f[2])!=f)
   if n:
    dup+=step(f,q[-1])!=f
    for j in range(n):missing+=fold(q[:j]+q[j+1:])!=f
   sig=tuple(sorted(q));old=order.get(sig)
   if old is None:order[sig]=f
   elif old!=f:orderbad=True
  if len(states)>1:indexalias=True
 neg={'INDEX_ONLY':int(indexalias),'OUT_OF_BAND':oob,'DUPLICATE_APPLY':dup,'ORDERLESS':int(orderbad),'MISSING_EVENT':missing}
 errs=[]
 for k,v in [('sequences',seqs),('checkpoint_checks',checks),('projection_mismatches',proj),('checkpoint_mismatches',cpbad)]:
  if r[k]!=v:errs.append(k)
 if r['negative_divergence_counts']!=neg:errs.append('negative_counts')
 if not all(r['sequence_controls'].values()) or not all(r['checkpoint_controls'].values()):errs.append('controls')
 if r['decision']!='PASS_EVENT_SOURCED_PROJECTION_CHECKPOINT_SCOPED':errs.append('decision')
 if r['formal_invocations']!=1 or r['reruns']!=0:errs.append('invocation')
 out={'pass':not errs,'errors':errs,'sequences':seqs,'checkpoint_checks':checks,'negative_divergence_counts':neg,'result_digest':r['digest']}
 out['audit_digest']=hashlib.sha256(json.dumps(out,sort_keys=True,separators=(',',':')).encode()).hexdigest();Path(a.output).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
