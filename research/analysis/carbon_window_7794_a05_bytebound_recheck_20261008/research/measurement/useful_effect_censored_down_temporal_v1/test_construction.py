from __future__ import annotations
import hashlib,json,random
from itertools import product
from candidate import *

SEED=98420260917001

# Oracle deliberately uses endpoint enumeration for temporal status, not thresholds.
def oracle_role(event:Event, acts):
    # Preserve #974 gates before the changed temporal question.
    if event.actuation_id is not None and not valid_id(event.actuation_id):
        return 'invalid_identity'
    if event.t < 0:
        return 'invalid_temporal'
    if not event.independently_scored:
        return 'unscored'
    by={a.actuation_id:a for a in acts}
    a=by.get(event.actuation_id)
    if a is None:
        return 'useful_unbound' if event.useful else None
    exact_downs=list(range(a.down_lo,a.down_hi+1))
    after=[event.t >= d for d in exact_downs]  # #974 equality convention
    if not any(after): return 'invalid_temporal'
    if not all(after): return 'temporal_ambiguous'
    return 'useful_bound' if event.useful else 'nonuseful_bound'

def parent_exact_role(event, act):
    if event.actuation_id is not None and not valid_id(event.actuation_id): return 'invalid_identity'
    if event.t < 0: return 'invalid_temporal'
    if not event.independently_scored: return 'unscored'
    if event.actuation_id != act.actuation_id:
        return 'useful_unbound' if event.useful else None
    if event.t < act.down_lo: return 'invalid_temporal'
    return 'useful_bound' if event.useful else 'nonuseful_bound'

def one_candidate_role(e, acts):
    out=analyze(Interval(0,32),acts,[EffectRecord('e',e)])['effects']
    hits=[k for k,v in out.items() if v]
    return hits[0] if hits else None

def independent_occupancy(wait, acts):
    # Separate direct point-set construction from candidate occupancy function.
    w=set(range(wait.lo,wait.hi)); gl=set(); pu=set(); al=set(); au=set()
    for a in acts:
        auth=set().union(*(set(range(x.lo,x.hi)) for x in a.authority)) if a.authority else set()
        g={x for x in w if a.down_hi <= x < a.up_lo}
        p={x for x in w if a.down_lo <= x < a.up_hi}
        gl |= g; pu |= p; al |= g & auth; au |= p & auth
    return len(gl),len(pu),len(al),len(au)

# Fixed boundary and precedence controls.
a=Actuation('a',5,8,12,15,(Interval(0,20),))
controls=[
    (Event(4,'a',True,True),'invalid_temporal'),
    (Event(5,'a',True,True),'temporal_ambiguous'),
    (Event(7,'a',True,False),'temporal_ambiguous'),
    (Event(8,'a',True,True),'useful_bound'),
    (Event(20,'a',True,False),'nonuseful_bound'),
    (Event(6,' ',True,True),'invalid_identity'),
    (Event(-1,' ',True,True),'invalid_identity'), # identity precedes negative time
    (Event(-1,'a',False,True),'invalid_temporal'), # time precedes scoring
    (Event(6,'a',False,True),'unscored'), # scoring precedes temporal ambiguity
    (Event(6,'unknown',True,True),'useful_unbound'),
    (Event(6,'unknown',True,False),None),
    (Event(6,None,True,True),'useful_unbound'),
]
for e,want in controls:
    got=one_candidate_role(e,[a]); assert got==want,(e,got,want)

# malformed dataset controls
for bad in ['', ' ', None, 0]:
    try: Actuation(bad,1,1,2,2); raise AssertionError(('bad actuation accepted',bad))
    except ValueError: pass
try:
    analyze(Interval(0,10),[Actuation('x',1,1,2,2),Actuation('x',3,3,4,4)],[])
    raise AssertionError('duplicate actuation accepted')
except ValueError: pass
for bad in ['', ' ']:
    try:
        analyze(Interval(0,10),[Actuation('x',1,1,2,2)],[EffectRecord(bad,Event(2,'x',True,True))])
        raise AssertionError('bad effect id accepted')
    except ValueError: pass
try:
    analyze(Interval(0,10),[Actuation('x',1,1,2,2)],[EffectRecord('e',Event(2,'x',True,True)),EffectRecord('e',Event(3,'x',True,True))])
    raise AssertionError('duplicate effect accepted')
except ValueError: pass

# Exhaustive small-domain temporal oracle.
exhaustive=0
ambiguous=0
for lo in range(0,8):
  for hi in range(lo,9):
    act=Actuation('a',lo,hi,10,12)
    for t in range(-2,12):
      for scored,useful,lineage in product((False,True),(False,True),('a','other',None,' ')):
        e=Event(t,lineage,scored,useful)
        got=one_candidate_role(e,[act]); want=oracle_role(e,[act])
        assert got==want,(lo,hi,e,got,want)
        exhaustive+=1
        ambiguous += got=='temporal_ambiguous'
        if lo==hi:
            assert got==parent_exact_role(e,act),(lo,e,got,parent_exact_role(e,act))
            assert got!='temporal_ambiguous'

# Random multi-record corpus, compare bucket counts to per-record independent oracle.
rng=random.Random(SEED)
random_cases=200000
random_records=0
ambig_to_bound=0
digest=hashlib.sha256()
for case in range(random_cases):
    acts=[]
    for i in range(rng.randrange(0,4)):
        dlo=rng.randrange(0,20); dhi=rng.randrange(dlo,min(24,dlo+5))
        ulo=rng.randrange(dhi,min(27,dhi+5)); uhi=rng.randrange(ulo,min(30,ulo+5))
        auth=[]
        for _ in range(rng.randrange(0,4)):
            x=rng.randrange(0,30); y=rng.randrange(x,31); auth.append(Interval(x,y))
        acts.append(Actuation(f'a{i}',dlo,dhi,ulo,uhi,tuple(auth)))
    records=[]; expected={k:0 for k in BUCKETS}
    for j in range(rng.randrange(0,7)):
        modes=[None,'unknown',' ',0]+[a.actuation_id for a in acts]
        lin=rng.choice(modes)
        e=Event(rng.randrange(-3,33),lin,bool(rng.getrandbits(1)),bool(rng.getrandbits(1)))
        r=EffectRecord(f'e{j}',e); records.append(r)
        role=oracle_role(e,acts)
        if role: expected[role]+=1
        # Independent per-record diagnostic: an oracle-ambiguous row must never
        # be emitted by the candidate as a bound useful/nonuseful effect.
        candidate_role=one_candidate_role(e,acts)
        if role=='temporal_ambiguous' and candidate_role in ('useful_bound','nonuseful_bound'):
            ambig_to_bound+=1
    got=analyze(Interval(0,30),acts,records)
    assert got['effects']==expected,(case,got['effects'],expected)
    occ=independent_occupancy(Interval(0,30),acts)
    assert got['occupancy']==occ,(case,got['occupancy'],occ)
    # Remove all effects: occupancy must be identical.
    assert analyze(Interval(0,30),acts,[])['occupancy']==occ
    random_records+=len(records)
    digest.update(json.dumps([case,got['occupancy'],got['effects']],sort_keys=True).encode())

print(json.dumps({
    'decision':'CONSTRUCTION_PASS',
    'seed':SEED,
    'fixed_controls':len(controls),
    'exhaustive_rows':exhaustive,
    'exhaustive_ambiguous_rows':ambiguous,
    'random_cases':random_cases,
    'random_records':random_records,
    'ambiguous_to_bound_promotions':ambig_to_bound,
    'digest_sha256':digest.hexdigest(),
},sort_keys=True))
