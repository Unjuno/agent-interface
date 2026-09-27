from __future__ import annotations
import hashlib,itertools,json,random
from dataclasses import replace
from contract import *
SEED=99420260917001;N=200000

def oracle(e):
    xs=(e.times.call_start,e.times.pre_start,e.times.pre_end,e.times.press_request,e.times.sync_return,e.times.post_start,e.times.post_end,e.times.call_return)
    if any(type(x) is not int or x<0 for x in xs) or any(xs[i]>xs[i+1] for i in range(7)):raise ValueError
    if any(not isinstance(x,str) or not x.strip() for x in (e.press_id,e.owner_id,e.intent_token,e.key)):raise ValueError
    bs=(e.owner_owned_before,e.pre_key_down,e.press_attempted,e.sync_succeeded,e.post_key_down,e.owner_owned_after)
    if any(type(x) is not bool for x in bs):raise ValueError
    if e.sync_succeeded and not e.press_attempted:raise ValueError
    if e.owner_owned_before: return 'OWNER_ALREADY_HELD',None
    if e.pre_key_down:return 'PREEXISTING_PHYSICAL_DOWN',None
    if e.press_attempted and e.sync_succeeded and e.post_key_down and e.owner_owned_after:return 'CONFIRMED_PHYSICAL_DOWN',[e.times.pre_end,e.times.post_end]
    return 'PRESS_UNCONFIRMED',None

def out(e):
    try:r=build(e);return ('OK',r['status'],r['physical_down_interval'])
    except ValueError:return ('ERR',None,None)
def oo(e):
    try:s,i=oracle(e);return ('OK',s,i)
    except ValueError:return ('ERR',None,None)
def times(off=10,gap=2):return Times(*(off+i*gap for i in range(8)))

def controls():
    t=times();good=Evidence('p','o','i','F8',False,False,True,True,True,True,t)
    assert build(good)['physical_down_interval']==[t.pre_end,t.post_end]
    pre=replace(good,pre_key_down=True);assert build(pre)['status']=='PREEXISTING_PHYSICAL_DOWN' and build(pre)['physical_down_interval'] is None
    held=replace(good,owner_owned_before=True);assert build(held)['status']=='OWNER_ALREADY_HELD' and build(held)['physical_down_interval'] is None
    ab=[replace(good,press_attempted=False,sync_succeeded=False),replace(good,sync_succeeded=False),replace(good,post_key_down=False),replace(good,owner_owned_after=False),replace(good,pre_key_down=True),replace(good,owner_owned_before=True)]
    for x in ab:
        z=out(x);assert not(z[0]=='OK' and z[2] is not None),z
    bad=[replace(good,press_id=' '),replace(good,owner_id=''),replace(good,intent_token=''),replace(good,key=' '),replace(good,pre_key_down=1),replace(good,times=Times(10,9,12,13,14,15,16,17)),replace(good,times=Times(-1,0,1,2,3,4,5,6))]
    for x in bad:assert out(x)[0]=='ERR'
    return 3+len(ab)+len(bad)

def main():
    ex=mis=rej=conf=0
    for spacing in (0,1,3,11):
      t=Times(*(100+i*spacing for i in range(8)))
      for bits in itertools.product((False,True),repeat=6):
        e=Evidence('p','o','i','F8',*bits,t);a=out(e);b=oo(e);ex+=1;mis+=a!=b;rej+=a[0]=='ERR';conf+=a[0]=='OK' and a[1]=='CONFIRMED_PHYSICAL_DOWN'
    ctl=controls();rng=random.Random(SEED);rm=fi=cr=0;h=hashlib.sha256()
    for n in range(N):
        vals=[rng.randrange(0,10**9)]
        for _ in range(7):vals.append(vals[-1]+rng.randrange(0,1000))
        e=Evidence(f'p{n}',f'o{rng.randrange(50)}',f'i{rng.randrange(50)}',rng.choice(['F8','Left','Right','space']),*(bool(rng.getrandbits(1)) for _ in range(6)),Times(*vals))
        a=out(e);b=oo(e);rm+=a!=b
        if a[0]=='OK' and a[2] is not None:
            cr+=1;allowed=(not e.owner_owned_before and not e.pre_key_down and e.press_attempted and e.sync_succeeded and e.post_key_down and e.owner_owned_after)
            if not allowed or a[2]!=[e.times.pre_end,e.times.post_end]:fi+=1
        h.update(json.dumps([n,a,b],sort_keys=True,separators=(',',':')).encode())
    r={'decision':'PASS_PHYSICAL_PRESS_BRACKET_CONTRACT_SCOPED' if not mis and not rm and not fi else 'FAIL','seed':SEED,'exhaustive_cases':ex,'exhaustive_mismatches':mis,'exhaustive_rejected':rej,'exhaustive_confirmed':conf,'fixed_controls_passed':ctl,'random_cases':N,'random_mismatches':rm,'random_confirmed_intervals':cr,'false_physical_intervals':fi,'digest_sha256':h.hexdigest()}
    open('RESULT.json','w').write(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps(r,sort_keys=True))
if __name__=='__main__':main()
