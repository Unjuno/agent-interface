from __future__ import annotations
import hashlib,itertools,json,random
from dataclasses import replace
from contract import *
SEED=99220260917001
N=200000

def oracle(e):
    vals=(e.times.call_start,e.times.pre_start,e.times.pre_end,e.times.release_request,e.times.sync_return,e.times.post_start,e.times.post_end,e.times.call_return)
    if any(type(x) is not int or x<0 for x in vals) or any(vals[i]>vals[i+1] for i in range(7)): raise ValueError
    if any(not isinstance(x,str) or not x.strip() for x in (e.release_id,e.owner_id,e.intent_token,e.key)): raise ValueError
    bs=(e.owner_owned,e.pre_key_down,e.release_attempted,e.sync_succeeded,e.post_key_down)
    if any(type(x) is not bool for x in bs): raise ValueError
    if e.sync_succeeded and not e.release_attempted: raise ValueError
    if e.release_attempted and not e.owner_owned: raise ValueError
    if not e.owner_owned:
        st='FOREIGN_OR_STALE_DOWN' if e.pre_key_down else 'NOOP_ALREADY_UP'; interval=None
    elif not e.pre_key_down:
        st='OWNER_PHYSICAL_MISMATCH'; interval=None
    elif e.release_attempted and e.sync_succeeded and not e.post_key_down:
        st='CONFIRMED_PHYSICAL_UP'; interval=[e.times.pre_end,e.times.post_end]
    else:
        st='RELEASE_UNCONFIRMED'; interval=None
    return st,interval

def outcome(e):
    try:
        r=build(e); return ('OK',r['status'],r['physical_up_interval'])
    except ValueError:return ('ERR',None,None)

def oracle_out(e):
    try:
        st,iv=oracle(e);return ('OK',st,iv)
    except ValueError:return ('ERR',None,None)

def base_times(offset=0,gap=1):
    xs=[offset+i*gap for i in range(8)];return Times(*xs)

def fixed_controls():
    t=base_times(10,2)
    good=Evidence('r','o','i','F8',True,True,True,True,False,t)
    assert build(good)['physical_up_interval']==[t.pre_end,t.post_end]
    noop=replace(good,owner_owned=False,pre_key_down=False,release_attempted=False,sync_succeeded=False)
    assert build(noop)['status']=='NOOP_ALREADY_UP' and build(noop)['physical_up_interval'] is None
    post_missing=replace(good,post_key_down=True)
    assert build(post_missing)['status']=='RELEASE_UNCONFIRMED' and build(post_missing)['physical_up_interval'] is None
    ablations=[replace(good,owner_owned=False),replace(good,pre_key_down=False),replace(good,release_attempted=False,sync_succeeded=False),replace(good,sync_succeeded=False),replace(good,post_key_down=True)]
    for x in ablations:
        o=outcome(x); assert not (o[0]=='OK' and o[2] is not None),o
    bads=[replace(good,release_id=' '),replace(good,owner_id=''),replace(good,intent_token=' '),replace(good,key=''),replace(good,owner_owned=1),replace(good,times=Times(10,9,12,13,14,15,16,17)),replace(good,times=Times(-1,0,1,2,3,4,5,6))]
    for x in bads: assert outcome(x)[0]=='ERR',x
    return 3+len(ablations)+len(bads)

def main():
    exhaustive=0; mismatch=0; confirmed=0; rejected=0
    for spacing in (0,1,3,11):
      t=base_times(100,spacing)
      for bits in itertools.product((False,True),repeat=5):
        e=Evidence('r','o','i','F8',*bits,t)
        a=outcome(e); b=oracle_out(e); exhaustive+=1
        mismatch += a!=b; rejected += a[0]=='ERR'; confirmed += a[0]=='OK' and a[1]=='CONFIRMED_PHYSICAL_UP'
    controls=fixed_controls()
    rng=random.Random(SEED); dig=hashlib.sha256(); random_mismatch=0; false_interval=0; confirmed_random=0
    for n in range(N):
        x=rng.randrange(0,10**9); gaps=[rng.randrange(0,1000) for _ in range(7)]
        vals=[x]
        for g in gaps: vals.append(vals[-1]+g)
        t=Times(*vals)
        bits=tuple(bool(rng.getrandbits(1)) for _ in range(5))
        e=Evidence(f'r{n}',f'o{rng.randrange(50)}',f'i{rng.randrange(50)}',rng.choice(['F8','Left','Right','space']),*bits,t)
        a=outcome(e);b=oracle_out(e);random_mismatch+=a!=b
        if a[0]=='OK' and a[2] is not None:
            confirmed_random+=1
            allowed=e.owner_owned and e.pre_key_down and e.release_attempted and e.sync_succeeded and not e.post_key_down
            if not allowed or a[2]!=[e.times.pre_end,e.times.post_end]: false_interval+=1
        dig.update(json.dumps([n,a,b],separators=(',',':'),sort_keys=True).encode())
    res={'decision':'PASS_PHYSICAL_RELEASE_BRACKET_CONTRACT_SCOPED' if mismatch==0 and random_mismatch==0 and false_interval==0 else 'FAIL','seed':SEED,'exhaustive_cases':exhaustive,'exhaustive_mismatches':mismatch,'exhaustive_rejected':rejected,'exhaustive_confirmed':confirmed,'fixed_controls_passed':controls,'random_cases':N,'random_mismatches':random_mismatch,'random_confirmed_intervals':confirmed_random,'false_physical_intervals':false_interval,'digest_sha256':dig.hexdigest()}
    open('RESULT.json','w').write(json.dumps(res,indent=2,sort_keys=True)+'\n');print(json.dumps(res,sort_keys=True))
if __name__=='__main__':main()
