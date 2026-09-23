from __future__ import annotations
import argparse, hashlib, json, random
from pathlib import Path

MASTER_SEED=149820260918002
TOTAL=220_000
BATCH_SIZE=11_000
BATCHES=20
MAX_FRAMES=4
FRAME_BYTES=4096
MAX_BYTES=MAX_FRAMES*FRAME_BYTES
FIXED=(0,-100,-400,-800)
CLASSES=('RECENT_DENSE','LONG_BASELINE','EVENT_CENTERED','REVERSAL_BRACKET')

def case_rng(index:int):
    b=hashlib.sha256(f'{MASTER_SEED}:{index}'.encode()).digest()
    return random.Random(int.from_bytes(b[:16],'big'))

def make_case(index:int):
    rng=case_rng(index); d=1000; scope='surfaceA'; rows=[]
    for j,t in enumerate(range(0,1001,25)):
        if rng.random()>=0.10: rows.append((f'{index}:A:{j}',scope,t,True))
    for k in range(3): rows.append((f'{index}:B:{k}','surfaceB',rng.randrange(0,1001,25),True))
    rows.append((f'{index}:future',scope,1025,True))
    kind=CLASSES[index%4]
    anchor=rng.randrange(250,826,25) if kind in ('EVENT_CENTERED','REVERSAL_BRACKET') else None
    return rows,kind,d,scope,anchor

def admissible(rows,d,scope): return [r for r in rows if r[1]==scope and r[2]<=d]
def pick(src,target,pred):
    xs=[r for r in src if pred(r)]
    return None if not xs else min(xs,key=lambda r:(abs(r[2]-target),-r[2],r[0]))
def unique(xs):
    d={r[0]:r for r in xs if r is not None}
    return sorted(d.values(),key=lambda r:(r[2],r[0]))[:MAX_FRAMES]
def fixed(rows,kind,d,scope,a):
    s=admissible(rows,d,scope); return unique([pick(s,d+o,lambda r:True) for o in FIXED])
def query(rows,kind,d,scope,a):
    s=admissible(rows,d,scope)
    if kind=='RECENT_DENSE': specs=[(d,lambda r:d-100<=r[2]<=d),(d-25,lambda r:d-100<=r[2]<=d),(d-50,lambda r:d-100<=r[2]<=d),(d-75,lambda r:d-100<=r[2]<=d)]
    elif kind=='LONG_BASELINE': specs=[(d,lambda r:True),(d-75,lambda r:True),(d-750,lambda r:True),(d-900,lambda r:True)]
    elif kind=='EVENT_CENTERED': specs=[(a-50,lambda r:r[2]<a),(a+50,lambda r:r[2]>a),(d,lambda r:True),(a,lambda r:True)]
    else: specs=[(a-75,lambda r:r[2]<=a-25),(a+75,lambda r:r[2]>=a+25),(d,lambda r:True),(d-100,lambda r:True)]
    return unique([pick(s,t,p) for t,p in specs])
def oracle(rows,kind,d,scope,a,arm):
    src=sorted([r for r in rows if r[1]==scope and r[2]<=d],key=lambda r:(r[2],r[0]))
    if arm=='fixed': specs=[(d+o,(-10**9,10**9)) for o in FIXED]
    elif kind=='RECENT_DENSE': specs=[(d,(d-100,d)),(d-25,(d-100,d)),(d-50,(d-100,d)),(d-75,(d-100,d))]
    elif kind=='LONG_BASELINE': specs=[(d,(-10**9,d)),(d-75,(-10**9,d)),(d-750,(-10**9,d)),(d-900,(-10**9,d))]
    elif kind=='EVENT_CENTERED': specs=[(a-50,(-10**9,a-1)),(a+50,(a+1,10**9)),(d,(-10**9,d)),(a,(-10**9,d))]
    else: specs=[(a-75,(-10**9,a-25)),(a+75,(a+25,10**9)),(d,(-10**9,d)),(d-100,(-10**9,d))]
    out=[]
    for target,(lo,hi) in specs:
        xs=[r for r in src if lo<=r[2]<=hi]
        if xs: out.append(sorted(xs,key=lambda r:(abs(r[2]-target),-r[2],r[0]))[0])
    return unique(out)
def covers(sel,kind,d,a):
    ts=[r[2] for r in sel]
    if kind=='RECENT_DENSE': return sum(d-100<=t<=d for t in ts)>=4
    if kind=='LONG_BASELINE': return any(t<=d-700 for t in ts) and any(t>=d-100 for t in ts)
    if kind=='EVENT_CENTERED': return any(a-100<=t<a for t in ts) and any(a<t<=a+100 for t in ts)
    return any(a-150<=t<=a-25 for t in ts) and any(a+25<=t<=a+150 for t in ts)
def validate(sel,rows,d,scope):
    ids={r[0] for r in rows}
    return [sum(r[0] not in ids for r in sel),sum(r[2]>d for r in sel),sum(r[1]!=scope for r in sel),int(len(sel)>MAX_FRAMES or len(sel)*FRAME_BYTES>MAX_BYTES),sum(not r[3] for r in sel)]
def directed():
    rows=[('a','surfaceA',900,True),('b','surfaceA',925,True),('c','surfaceA',950,True),('d','surfaceA',975,True),('e','surfaceA',1000,True),('x','surfaceB',1000,True),('f','surfaceA',1025,True)]
    for arm,fn in [('fixed',fixed),('query',query)]:
        s=fn(rows,'RECENT_DENSE',1000,'surfaceA',None); assert s==oracle(rows,'RECENT_DENSE',1000,'surfaceA',None,arm); assert validate(s,rows,1000,'surfaceA')==[0,0,0,0,0]
    sparse=[('a','surfaceA',900,True),('c','surfaceA',950,True),('e','surfaceA',1000,True)]
    assert not covers(query(sparse,'RECENT_DENSE',1000,'surfaceA',None),'RECENT_DENSE',1000,None)

def run(start,end):
    c={k:{'n':0,'fixed':0,'query':0} for k in CLASSES}; mm=0; leaks=[0,0,0,0,0]
    for i in range(start,end):
        rows,k,d,s,a=make_case(i); f=fixed(rows,k,d,s,a); q=query(rows,k,d,s,a)
        if f!=oracle(rows,k,d,s,a,'fixed') or q!=oracle(rows,k,d,s,a,'query'):mm+=1
        for z in (f,q):
            v=validate(z,rows,d,s); leaks=[x+y for x,y in zip(leaks,v)]
        c[k]['n']+=1;c[k]['fixed']+=int(covers(f,k,d,a));c[k]['query']+=int(covers(q,k,d,a))
    return {'master_seed':MASTER_SEED,'start':start,'end':end,'histories':end-start,'counts':c,'candidate_oracle_mismatches':mm,
      'leaks':dict(zip(('unknown_source','future','cross_scope','budget','authority'),leaks)),'grants_input_authority':False}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--batch',type=int);ap.add_argument('--construction',action='store_true');ap.add_argument('--output',required=True);a=ap.parse_args();directed()
    p=Path(a.output); assert not p.exists()
    if a.construction:start,end=-20000,0
    else:
        assert a.batch is not None and 0<=a.batch<BATCHES;start=a.batch*BATCH_SIZE;end=start+BATCH_SIZE
    r=run(start,end);r['batch']=None if a.construction else a.batch;r['construction']=a.construction
    r['digest']=hashlib.sha256(json.dumps(r,sort_keys=True,separators=(',',':')).encode()).hexdigest();p.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps(r,sort_keys=True))
if __name__=='__main__':main()
