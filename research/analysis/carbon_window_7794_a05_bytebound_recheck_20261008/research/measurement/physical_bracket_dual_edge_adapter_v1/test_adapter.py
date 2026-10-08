from __future__ import annotations
import hashlib,itertools,json,random
from dataclasses import replace
from adapter import *
SEED=99620260917001;N=250000

def oracle(d,u):
    def val(e,which):
        if e.edge!=which: raise ValueError
        allowed=DOWN_STATUSES if which=='down' else UP_STATUSES
        if e.status not in allowed: raise ValueError
        if any(not isinstance(x,str) or not x.strip() for x in (e.actuation_id,e.owner_id,e.intent_token,e.key)): raise ValueError
        conf=e.status==('CONFIRMED_PHYSICAL_DOWN' if which=='down' else 'CONFIRMED_PHYSICAL_UP')
        if conf:
            if not isinstance(e.interval,tuple) or len(e.interval)!=2:raise ValueError
            a,b=e.interval
            if type(a)is not int or type(b)is not int or a<0 or b<a:raise ValueError
        elif e.interval is not None:raise ValueError
    val(d,'down');val(u,'up')
    if (d.actuation_id,d.owner_id,d.intent_token,d.key)!=(u.actuation_id,u.owner_id,u.intent_token,u.key):return ('LINEAGE_MISMATCH',None)
    if d.status!='CONFIRMED_PHYSICAL_DOWN' or u.status!='CONFIRMED_PHYSICAL_UP':return ('INCOMPLETE_EDGE_EVIDENCE',None)
    if d.interval[1]>u.interval[0]:return ('EDGE_ORDER_AMBIGUOUS',None)
    return ('COMPOSED_PHYSICAL_ACTUATION',(d.interval[0],d.interval[1],u.interval[0],u.interval[1]))

def norm(d,u):
    try:
        r=compose(d,u);a=r['actuation'];return ('OK',r['status'],None if a is None else (a['down_lo'],a['down_hi'],a['up_lo'],a['up_hi']))
    except ValueError:return ('ERR',None,None)
def onorm(d,u):
    try:s,a=oracle(d,u);return ('OK',s,a)
    except ValueError:return ('ERR',None,None)
def edge(which,status,iv,aid='a',owner='o',intent='i',key='F8'):
    return Edge(which,status,aid,owner,intent,key,iv)

def fixed():
    d=edge('down','CONFIRMED_PHYSICAL_DOWN',(10,12));u=edge('up','CONFIRMED_PHYSICAL_UP',(20,22))
    assert compose(d,u)['status']=='COMPOSED_PHYSICAL_ACTUATION'
    assert compose(d,replace(u,interval=(12,15)))['status']=='COMPOSED_PHYSICAL_ACTUATION'
    assert compose(d,replace(u,interval=(11,15)))['status']=='EDGE_ORDER_AMBIGUOUS'
    for x in [replace(d,status='PRESS_UNCONFIRMED',interval=None),replace(u,status='NOOP_ALREADY_UP',interval=None)]:
        r=compose(x,u) if x.edge=='down' else compose(d,x);assert r['actuation'] is None
    for field in ('actuation_id','owner_id','intent_token','key'):
        bad=replace(u,**{field:getattr(u,field)+'x'});r=compose(d,bad);assert r['status']=='LINEAGE_MISMATCH' and r['actuation'] is None
    bads=[replace(d,status='UNKNOWN'),replace(d,interval=None),replace(u,status='NOOP_ALREADY_UP',interval=(20,22)),replace(d,interval=(-1,2)),replace(u,interval=(23,22)),replace(d,actuation_id=' ')]
    for b in bads:
        try: compose(b,u) if b.edge=='down' else compose(d,b);raise AssertionError('bad accepted')
        except ValueError:pass
    return 3+2+4+len(bads)

def main():
    controls=fixed();ex=mis=0
    interval_shapes=[((1,2),(4,5)),((1,2),(2,5)),((1,4),(3,6)),((0,0),(0,0))]
    for ds,us,match,(di,ui) in itertools.product(sorted(DOWN_STATUSES),sorted(UP_STATUSES),(False,True),interval_shapes):
        d=edge('down',ds,di if ds=='CONFIRMED_PHYSICAL_DOWN' else None)
        u=edge('up',us,ui if us=='CONFIRMED_PHYSICAL_UP' else None,aid='a' if match else 'b')
        a=norm(d,u);b=onorm(d,u);ex+=1;mis+=a!=b
    rng=random.Random(SEED);rm=fa=0;composed=overlap=incomplete=mismatch=0;h=hashlib.sha256()
    dss=sorted(DOWN_STATUSES);uss=sorted(UP_STATUSES)
    for n in range(N):
        ds=rng.choice(dss);us=rng.choice(uss)
        x=rng.randrange(0,10**9);dlo=x+rng.randrange(0,100);dhi=dlo+rng.randrange(0,100);ulo=x+rng.randrange(0,250);uhi=ulo+rng.randrange(0,100)
        aid=f'a{rng.randrange(100)}';owner=f'o{rng.randrange(30)}';intent=f'i{rng.randrange(30)}';key=rng.choice(['F8','Left','Right','space'])
        d=edge('down',ds,(dlo,dhi) if ds=='CONFIRMED_PHYSICAL_DOWN' else None,aid,owner,intent,key)
        u=edge('up',us,(ulo,uhi) if us=='CONFIRMED_PHYSICAL_UP' else None,aid,owner,intent,key)
        if rng.random()<.15:
            f=rng.choice(['actuation_id','owner_id','intent_token','key']);u=replace(u,**{f:getattr(u,f)+'x'})
        a=norm(d,u);b=onorm(d,u);rm+=a!=b
        if a[0]=='OK':
            st=a[1];composed+=st=='COMPOSED_PHYSICAL_ACTUATION';overlap+=st=='EDGE_ORDER_AMBIGUOUS';incomplete+=st=='INCOMPLETE_EDGE_EVIDENCE';mismatch+=st=='LINEAGE_MISMATCH'
            if st=='COMPOSED_PHYSICAL_ACTUATION':
                allowed=(ds=='CONFIRMED_PHYSICAL_DOWN' and us=='CONFIRMED_PHYSICAL_UP' and (d.actuation_id,d.owner_id,d.intent_token,d.key)==(u.actuation_id,u.owner_id,u.intent_token,u.key) and dhi<=ulo)
                if not allowed or a[2]!=(dlo,dhi,ulo,uhi):fa+=1
        h.update(json.dumps([n,a,b],sort_keys=True,separators=(',',':')).encode())
    r={'decision':'PASS_PHYSICAL_BRACKET_DUAL_EDGE_ADAPTER_SCOPED' if mis==0 and rm==0 and fa==0 else 'FAIL','seed':SEED,'fixed_controls_passed':controls,'exhaustive_cases':ex,'exhaustive_mismatches':mis,'random_cases':N,'random_mismatches':rm,'false_actuations':fa,'random_composed':composed,'random_overlap':overlap,'random_incomplete':incomplete,'random_lineage_mismatch':mismatch,'digest_sha256':h.hexdigest()}
    open('RESULT.json','w').write(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps(r,sort_keys=True))
if __name__=='__main__':main()
