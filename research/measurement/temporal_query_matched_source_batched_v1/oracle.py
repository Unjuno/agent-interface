from __future__ import annotations
import hashlib
MASTER=149820260918002
CLASSES=("RECENT_DENSE","LONG_BASELINE","EVENT_CENTERED","REVERSAL_BRACKET")
FIXED=(0,40,120,260)
def authored(index):
 d=hashlib.sha256((str(MASTER)+":"+str(index)).encode()).digest(); scope="scope-"+str(d[1]%4); cls=CLASSES[d[0]%4]
 ages=[0]+[a*20 for a in range(1,16) if d[a]>=32]
 c=None
 if cls=="EVENT_CENTERED": c=(80,120,160,200)[d[16]%4]
 if cls=="REVERSAL_BRACKET": c=(60,100,140,180)[d[16]%4]
 return scope,cls,c,ages
def choose(ages,targets):
 out=[]
 for t in targets:
  cand=[a for a in ages if a not in out]
  if not cand: break
  out.append(sorted(cand,key=lambda a:(abs(a-t),a))[0])
 return out[:4]
def selections(index):
 scope,cls,c,ages=authored(index)
 f=choose(ages,FIXED)
 if cls=="RECENT_DENSE": q=sorted(ages)[:4]
 elif cls=="LONG_BASELINE": q=choose(ages,(0,80,180,300))
 elif cls=="EVENT_CENTERED": q=choose(ages,(c-20,c,c+20,0))
 else: q=choose(ages,(c-20,c+20,c-40,c+40))
 return scope,cls,c,f,q
def cov(cls,c,ages):
 a=sorted(ages)
 if cls=="RECENT_DENSE": return sum(x<=60 for x in a)>=3
 if cls=="LONG_BASELINE": return 0 in a and any(x>=280 for x in a)
 if cls=="EVENT_CENTERED": return any(x<=c and c-x<=20 for x in a) and any(x>=c and x-c<=20 for x in a)
 return any(x<c and c-x<=40 for x in a) and any(x>c and x-c<=40 for x in a)
def one(index):
 scope,cls,c,f,q=selections(index)
 return {"index":index,"class":cls,"fixed_covered":cov(cls,c,f),"query_covered":cov(cls,c,q)}
