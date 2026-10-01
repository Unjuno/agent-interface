import random
from candidate import Actuation, Effect
SEED=100420260917002
COUNTS={'same_clock':50000,'cross_domain':35000,'cross_epoch':25000,'missing_clock':25000,'precedence':45000}

def _act(rng, i, domain='mono', epoch='ep1'):
    lo=rng.randrange(0,80); hi=lo+rng.randrange(0,8)
    return Actuation(f'a{i%5}',lo,hi,domain,epoch)

def cases():
    rng=random.Random(SEED); idx=0
    for _ in range(COUNTS['same_clock']):
        a=_act(rng,idx,'mono','ep1'); t=rng.randrange(0,100)
        e=Effect(f'e{idx}',a.actuation_id,t,True,bool(rng.getrandbits(1)),'mono','ep1')
        yield 'same_clock',e,[a]; idx+=1
    for _ in range(COUNTS['cross_domain']):
        a=_act(rng,idx,'monoA','ep1'); t=rng.randrange(0,100)
        e=Effect(f'e{idx}',a.actuation_id,t,True,bool(rng.getrandbits(1)),'monoB','ep1')
        yield 'cross_domain',e,[a]; idx+=1
    for _ in range(COUNTS['cross_epoch']):
        a=_act(rng,idx,'mono','bootA'); t=rng.randrange(0,100)
        e=Effect(f'e{idx}',a.actuation_id,t,True,bool(rng.getrandbits(1)),'mono','bootB')
        yield 'cross_epoch',e,[a]; idx+=1
    for _ in range(COUNTS['missing_clock']):
        mode=idx%4; ad='mono'; ae='ep1'; ed='mono'; ee='ep1'
        if mode==0: ed=None
        elif mode==1: ee=''
        elif mode==2: ad=None
        else: ae=''
        a=_act(rng,idx,ad,ae); t=rng.randrange(0,100)
        e=Effect(f'e{idx}',a.actuation_id,t,True,bool(rng.getrandbits(1)),ed,ee)
        yield 'missing_clock',e,[a]; idx+=1
    for _ in range(COUNTS['precedence']):
        a=_act(rng,idx,'mono','ep1'); mode=idx%6; t=rng.randrange(0,100)
        kw=dict(effect_id=f'e{idx}',actuation_id=a.actuation_id,t_ns=t,scored=True,useful=bool(rng.getrandbits(1)),clock_domain='mono',clock_epoch='ep1')
        if mode==0: kw['effect_id']=''
        elif mode==1: kw['t_ns']=-1
        elif mode==2: kw['scored']=False; kw['clock_domain']='other'
        elif mode==3: kw['actuation_id']=None; kw['clock_domain']='other'
        elif mode==4: kw['actuation_id']='unknown'; kw['clock_epoch']='other'
        else: kw['useful']=False
        yield 'precedence',Effect(**kw),[a]; idx+=1
