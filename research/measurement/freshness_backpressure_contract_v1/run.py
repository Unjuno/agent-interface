import itertools, random, json, hashlib
from contract import *

def R(i,t,s='s',g='t',st='x',k='FRAME'):
    return Record(f'e{i}',i,t,s,g,st,k)

def eq(rows,now=100,age=30):
    a=reduce_candidate(rows,now,age); b=reduce_reference(rows,now,age)
    assert a==b,(a,b,rows)
    return a

assert eq([R(1,80),R(2,90),R(3,95)])['delivered_ids']==['e3']
x=eq([R(1,80),R(2,81,k='LEASE_EXPIRED'),R(3,90),R(4,91,k='SAFETY_VIOLATION'),R(5,95)])
assert x['delivered_ids']==['e2','e4','e5']
x=eq([R(1,80,s='a'),R(2,90,s='b'),R(3,95,s='a')]); assert x['delivered_ids']==['e2','e3']
x=eq([R(1,1),R(2,2,k='AUTHORITY_REVOKED')]); assert x['delivered_ids']==['e2'] and x['stale_ids']==['e1']
for bad in [[R(1,80),Record('e1',2,90,'s','t','x','FRAME')],[R(2,80),R(1,90)],[R(1,80),Record('e2',1,90,'s','t','x','FRAME')],[Record('e1',1,80,'','t','x','FRAME')]]:
    try: reduce_candidate(bad,100,30); raise AssertionError('bad accepted')
    except ValueError: pass

rng=random.Random(100820260917001)
kinds=sorted(ALL_KINDS); sessions=['s0','s1','s2']; targets=['t0','t1']; streams=['frame','status','motor']
records_total=cases=critical_total=delivered_total=coalesced_total=stale_total=0
while records_total < 300_000:
    n=rng.randint(0,35); now=rng.randint(100,10000); max_age=rng.randint(0,300); rows=[]; seq0=rng.randint(0,20)
    for j in range(n):
        rows.append(Record(f'{cases}:{j}',seq0+j+1,max(0,now-rng.randint(0,600)),rng.choice(sessions),rng.choice(targets),rng.choice(streams),rng.choice(kinds)))
    out=eq(rows,now,max_age); rec={r.event_id:r for r in rows}; crit=[r.event_id for r in rows if r.kind in CRITICAL]
    assert out['critical_ids']==crit
    assert [e for e in out['delivered_ids'] if rec[e].kind in CRITICAL]==crit
    key_counts={}
    for e in out['delivered_ids']:
        r=rec[e]
        if r.kind not in CRITICAL:
            assert now-r.t_ns <= max_age
            key=(r.session,r.target,r.stream); key_counts[key]=key_counts.get(key,0)+1
    assert all(v<=1 for v in key_counts.values())
    records_total+=n; cases+=1; critical_total+=len(crit); delivered_total+=out['delivered_count']; coalesced_total+=out['coalesced_count']; stale_total+=out['stale_count']

atoms=[(k,s,st,t) for k in ['FRAME','STATUS','LEASE_EXPIRED','FOCUS_CHANGED'] for s in ['s0','s1'] for st in ['a','b'] for t in [0,5,10]]
exhaustive=0
for n in range(4):
    for combo in itertools.product(atoms[:12], repeat=n):
        eq([Record(f'x{i}',i+1,t,s,'t0',st,k) for i,(k,s,st,t) in enumerate(combo)],10,5); exhaustive+=1
summary={'status':'CONSTRUCTION_PASS','seed':100820260917001,'random_records':records_total,'random_cases':cases,'critical_total':critical_total,'delivered_total':delivered_total,'coalesced_total':coalesced_total,'stale_total':stale_total,'exhaustive_cases':exhaustive}
summary['digest']=hashlib.sha256(json.dumps(summary,sort_keys=True,separators=(',',':')).encode()).hexdigest()
print(json.dumps(summary,sort_keys=True,indent=2))
