import random, itertools, json, hashlib, sys
from contract import *

# Independent replay/oracle: no candidate query helpers.
def oracle(full, gaps, anchors, cfg, q, now):
    if len(cfg)==3: max_items,max_bytes,max_age=cfg; max_gaps=64; max_anchors=128
    else: max_items,max_bytes,max_age,max_gaps,max_anchors=cfg
    kept=[]; total=0; rg=[]; overflow=None
    def mg(lo,hi,reason,session,surface):
        nonlocal overflow
        if rg and rg[-1][2:]==(reason,session,surface) and lo<=rg[-1][1]+1:
            rg[-1]=(rg[-1][0],max(rg[-1][1],hi),reason,session,surface); return
        if len(rg)<max_gaps:
            rg.append((lo,hi,reason,session,surface)); return
        if overflow is None: overflow={'first_unretained_start_ns':lo,'last_unretained_end_ns':hi,'unretained_count':1}
        else:
            overflow['last_unretained_end_ns']=max(overflow['last_unretained_end_ns'],hi); overflow['unretained_count']+=1
    for a,b,r,sess,surf in gaps: mg(a,b,r,sess,surf)
    for obs, append_now in full:
        kept.append(obs); total += obs.bytes_size
        while kept and append_now-kept[0].t_ns>max_age:
            z=kept.pop(0); total-=z.bytes_size; mg(z.t_ns,z.t_ns,'RETENTION_EXPIRED',z.session,z.surface)
        while kept and (len(kept)>max_items or total>max_bytes):
            z=kept.pop(0); total-=z.bytes_size; mg(z.t_ns,z.t_ns,'RETENTION_CAPACITY',z.session,z.surface)
    if full and now < full[-1][0].t_ns: raise ValueError('query_before_capture')
    while kept and now-kept[0].t_ns>max_age:
        z=kept.pop(0); total-=z.bytes_size; mg(z.t_ns,z.t_ns,'RETENTION_EXPIRED',z.session,z.surface)
    amap=dict(anchors)
    while len(amap)>max_anchors:
        victim=min(amap, key=lambda k:(amap[k][0],k[0],k[1])); del amap[victim]
    cutoff=max(0,now-max_age)
    amap={k:v for k,v in amap.items() if v[0]>=cutoff}
    if q.anchor_kind=='NOW': anchor=now
    elif q.anchor_kind=='OBSERVATION':
        xs=[x for x in kept if x.observation_id==q.anchor_ref and x.session==q.session and x.surface==q.surface]
        if not xs: raise KeyError('anchor_unavailable')
        anchor=xs[0].t_ns
    else:
        info=amap.get((q.anchor_kind,q.anchor_ref))
        if info is None: raise KeyError('anchor_unavailable')
        anchor,sess,surf=info
        if (sess,surf)!=(q.session,q.surface): raise KeyError('anchor_scope')
    if anchor > now: raise ValueError('future_anchor')
    lo=max(0,anchor-q.before_ns); hi=anchor+q.after_ns
    eligible=[x for x in kept if (x.session,x.surface)==(q.session,q.surface) and lo<=x.t_ns<=hi]
    if q.strategy=='KEYFRAMES': pool=[x for x in eligible if x.keyframe]
    elif q.strategy=='CHANGES': pool=[x for x in eligible if x.changed]
    else: pool=eligible
    def sz(o):
        if q.roi is None: return o.bytes_size,None
        x,y,w,h=q.roi
        if x<0 or y<0 or w<=0 or h<=0 or x+w>o.width or y+h>o.height: raise ValueError('roi')
        return max(1,(o.bytes_size*w*h + o.width*o.height-1)//(o.width*o.height)), {'x':x,'y':y,'width':w,'height':h,'source_width':o.width,'source_height':o.height}
    def pick(n,m):
        if m<=0 or n<=0:return []
        if m>=n:return list(range(n))
        if m==1:return [n-1]
        # integer-nearest to i*(n-1)/(m-1), Python round is bankers; emulate exactly via round on Fraction-ish float avoided for small n.
        return [round(i*(n-1)/(m-1)) for i in range(m)]
    sizes=[sz(x)[0] for x in pool]; ids=[]
    for m in range(min(q.max_frames,len(pool)),0,-1):
        ix=pick(len(pool),m)
        if len(set(ix))==len(ix) and sum(sizes[i] for i in ix)<=q.max_bytes:
            ids=ix; break
    ss=set(ids); out=[]
    for i,o in enumerate(pool):
        if i in ss:
            n,tr=sz(o); role='CURRENT_AT_QUERY' if o.current_evidence and o.t_ns==now else 'HISTORICAL'
            out.append({'observation_id':o.observation_id,'captured_at_ns':o.t_ns,'age_at_query_ns':now-o.t_ns,'role':role,'payload_bytes':n,'spatial_transform':tr,'grants_input_authority':False})
    sel={pool[i].observation_id for i in ids}; poolset={x.observation_id for x in pool}
    un=[]
    for a,b,r,sess,surf in rg:
        if (sess,surf)!=(q.session,q.surface): continue
        x=max(a,lo); y=min(b,hi)
        if x<=y: un.append({'start_ns':x,'end_ns':y,'reason':r,'session':sess,'surface':surf})
    un.sort(key=lambda z:(z['start_ns'],z['end_ns'],z['reason']))
    scope=[x for x in kept if (x.session,x.surface)==(q.session,q.surface)]
    return {'anchor_ns':anchor,'window':[lo,hi],'items':out,
            'omitted_due_to_budget':[x.observation_id for x in pool if x.observation_id not in sel],
            'omitted_by_strategy':[x.observation_id for x in eligible if x.observation_id not in poolset],
            'unavailable_intervals':un,'oldest_available_at':scope[0].t_ns if scope else None,
            'newest_available_at':scope[-1].t_ns if scope else None,'coverage_complete':overflow is None,
            'gap_metadata_overflow':dict(overflow) if overflow else None,'grants_input_authority':False}

def build_case(obs_list,cfg,gaps=(),anchors=()):
    b=TemporalBuffer(*cfg); full=[]; amap={}
    for kind,ref,t,sess,surf in anchors:
        b.bind_anchor(kind,ref,t,sess,surf); amap[(kind,ref)]=(t,sess,surf)
    for g in gaps: b.note_gap(*g)
    for o,now in obs_list: b.append(o,now); full.append((o,now))
    return b,full,list(gaps),amap

def O(i,t,s='s0',u='A',size=100,key=False,ch=True,cur=False):
    return Observation(f'o{i}',i,t,s,u,100,80,size,key,ch,cur)

def check(b,full,gaps,anchors,cfg,q,now):
    a=b.query(q,now); z=oracle(full,gaps,anchors,cfg,q,now)
    assert a==z,(a,z,q)
    assert a['grants_input_authority'] is False
    assert all(x['grants_input_authority'] is False for x in a['items'])
    assert all(x['role']=='HISTORICAL' or x['captured_at_ns']==now for x in a['items'])
    return a

# fixed controls
cfg=(4,350,50)
b,full,gaps,anchors=build_case([(O(1,10,size=100),10),(O(2,20,size=100,key=True),20),(O(3,30,size=100,ch=False),30),(O(4,40,size=100,key=True,cur=True),40),(O(5,60,size=100,cur=True),60)],cfg,
    gaps=[(33,35,'CAPTURE_DROPPED','s0','A')],anchors=[('EVENT','ev1',30,'s0','A'),('ACTION','ac1',40,'s0','A')])
q=Query('s0','A','NOW',None,60,0,3,1000,'UNIFORM',None); r=check(b,full,gaps,anchors,cfg,q,60)
assert [x['observation_id'] for x in r['items']]==['o3','o4','o5']
assert r['items'][-1]['role']=='CURRENT_AT_QUERY' and all(x['role']=='HISTORICAL' for x in r['items'][:-1])
assert any(x['reason']=='CAPTURE_DROPPED' for x in r['unavailable_intervals'])
q2=Query('s0','A','EVENT','ev1',15,15,4,1000,'KEYFRAMES',(0,0,50,40)); r2=check(b,full,gaps,anchors,cfg,q2,60); assert [x['observation_id'] for x in r2['items']]==['o4'] and r2['items'][0]['payload_bytes']==25
q3=Query('s0','A','ACTION','ac1',30,30,4,100,'CHANGES',None); check(b,full,gaps,anchors,cfg,q3,60)
# deterministic replay
assert b.query(q2,60)==b.query(q2,60)
# old observation anchor was evicted
try: b.query(Query('s0','A','OBSERVATION','o1',1,1,1,100,'UNIFORM'),60); raise AssertionError('evicted anchor accepted')
except KeyError: pass
# malformed controls
badq=[Query('','A','NOW',None,1,1,1,1,'UNIFORM'),Query('s0','A','EVENT','',1,1,1,1,'UNIFORM'),Query('s0','A','NOW',None,1,1,1,1,'BOGUS'),Query('s0','A','NOW',None,1,1,1,1,'UNIFORM',(0,0,101,1))]
for x in badq:
    try: b.query(x,60); raise AssertionError('bad query accepted')
    except (ValueError,KeyError): pass

# query-time expiry without a new append: stale retained pixels must disappear and become explicit gap.
bx,fx,gx,ax=build_case([(O(1,10),10)],(5,1000,20))
rx=check(bx,fx,gx,ax,(5,1000,20),Query('s0','A','NOW',None,100,0,5,1000,'UNIFORM'),40)
assert rx['items']==[] and any(g['reason']=='RETENTION_EXPIRED' for g in rx['unavailable_intervals'])
# query cannot run before the newest captured frame; event/action anchors from the future also fail closed.
by,fy,gy,ay=build_case([(O(1,10),10)],(5,1000,100),anchors=[('EVENT','future',50,'s0','A')])
for qq,qn in [(Query('s0','A','NOW',None,10,0,2,1000,'UNIFORM'),5),(Query('s0','A','EVENT','future',10,0,2,1000,'UNIFORM'),20)]:
    try: by.query(qq,qn); raise AssertionError('future-time query accepted')
    except ValueError: pass

# gaps are scoped: a surface-A capture drop must not contaminate a surface-B query.
bz,fz,gz,az=build_case([(O(1,10,s='s0',u='A'),10),(O(2,12,s='s0',u='B'),12)],(5,1000,100),gaps=[(9,11,'CAPTURE_DROPPED','s0','A')])
rz=check(bz,fz,gz,az,(5,1000,100),Query('s0','B','NOW',None,20,0,5,1000,'UNIFORM'),12)
assert rz['unavailable_intervals']==[]

# metadata boundedness stress: many disjoint gap receipts become explicit overflow, not unbounded silent loss.
bm=TemporalBuffer(2,1000,100000,8,5)
for i in range(20): bm.note_gap(i*3,i*3,'CAPTURE_DROPPED','s0','A')
assert len(bm.gaps)<=8 and bm.gap_overflow and bm.gap_overflow['unretained_count']==12
rm=bm.query(Query('s0','A','NOW',None,100,0,2,1000,'UNIFORM'),100)
assert rm['coverage_complete'] is False and rm['gap_metadata_overflow']['unretained_count']==12
# anchor index is bounded and age-expiring; old refs fail closed.
ba=TemporalBuffer(2,1000,10,8,3)
for i in range(5): ba.bind_anchor('EVENT',f'a{i}',i,'s0','A')
assert len(ba.anchor_refs)==3
ba.append(O(1,20),20)
assert len(ba.anchor_refs)==0

# randomized candidate/oracle comparison
rng=random.Random(102820260918001); cases=records=queries=0; current_role_errors=0; budget_errors=0; cross_scope_errors=0
strategies=sorted(STRATEGIES)
while records < 300_000:
    cfg=(rng.randint(1,12),rng.randint(80,1400),rng.randint(0,160))
    n=rng.randint(1,35); now=0; rows=[]; gaps=[]; anchors=[]
    seq0=rng.randint(0,20)
    for j in range(n):
        now += rng.randint(0,8); size=rng.randint(20,180)
        o=Observation(f'{cases}:{j}',seq0+j+1,now,rng.choice(['s0','s1']),rng.choice(['A','B']),100,80,size,rng.random()<.2,rng.random()<.75,rng.random()<.08)
        rows.append((o,now))
        if rng.random()<.04:
            gaps.append((max(0,now-rng.randint(0,3)),now,'CAPTURE_DROPPED',o.session,o.surface))
    # event/action anchor timestamps independent of retention
    for k in range(rng.randint(0,3)):
        t=rng.randint(0,now); sess=rng.choice(['s0','s1']); surf=rng.choice(['A','B']); anchors.append((rng.choice(['EVENT','ACTION']),f'r{cases}:{k}',t,sess,surf))
    b,full,gs,amap=build_case(rows,cfg,gaps,anchors)
    query_now=now+rng.randint(0,220)
    for qi in range(rng.randint(1,4)):
        sess=rng.choice(['s0','s1']); surf=rng.choice(['A','B']); ak='NOW'; ref=None
        if anchors and rng.random()<.35:
            z=rng.choice(anchors); ak,ref=z[0],z[1]; sess,surf=z[3],z[4]
        scope=[o for o,_ in rows if o.session==sess and o.surface==surf]
        if scope and rng.random()<.2:
            ak='OBSERVATION'; ref=rng.choice(scope).observation_id
        roi=None
        if rng.random()<.4:
            x=rng.randint(0,70); y=rng.randint(0,50); w=rng.randint(1,100-x); h=rng.randint(1,80-y); roi=(x,y,w,h)
        q=Query(sess,surf,ak,ref,rng.randint(0,100),rng.randint(0,40),rng.randint(0,8),rng.randint(0,700),rng.choice(strategies),roi)
        try:
            out=check(b,full,gs,amap,cfg,q,query_now)
        except KeyError:
            # observation anchor can be evicted; oracle must agree on failure.
            try: oracle(full,gs,amap,cfg,q,query_now); raise AssertionError('oracle accepted unavailable anchor')
            except KeyError: pass
            continue
        queries+=1
        # invariants
        if sum(x['payload_bytes'] for x in out['items'])>q.max_bytes or len(out['items'])>q.max_frames: budget_errors+=1
        if any(x['role']=='CURRENT_AT_QUERY' and x['captured_at_ns']!=query_now for x in out['items']): current_role_errors+=1
        selected_ids={x['observation_id'] for x in out['items']}
        byid={o.observation_id:o for o,_ in rows}
        if any((byid[i].session,byid[i].surface)!=(sess,surf) for i in selected_ids): cross_scope_errors+=1
    records+=n; cases+=1

# stress bounded metadata indexes with deliberately tiny gap/anchor budgets.
stress_records=stress_cases=stress_queries=stress_gap_overflow_cases=stress_anchor_eviction_cases=0
while stress_records < 100_000:
    cfg=(rng.randint(1,8),rng.randint(60,700),rng.randint(5,80),rng.randint(1,8),rng.randint(1,8))
    n=rng.randint(4,25); now=0; rows=[]; gaps=[]; anchors=[]
    for j in range(n):
        now += rng.randint(1,5); o=Observation(f'm{stress_cases}:{j}',j+1,now,rng.choice(['s0','s1']),rng.choice(['A','B']),50,40,rng.randint(20,120),rng.random()<.2,rng.random()<.7,False); rows.append((o,now))
        if rng.random()<.35: gaps.append((max(0,now-rng.randint(0,2)),now,'CAPTURE_DROPPED',o.session,o.surface))
        if rng.random()<.25: anchors.append((rng.choice(['EVENT','ACTION']),f'mr{stress_cases}:{j}',now,o.session,o.surface))
    b,full,gs,am=build_case(rows,cfg,gaps,anchors); query_now=now+rng.randint(0,100)
    if b.gap_overflow: stress_gap_overflow_cases+=1
    if len(anchors)>cfg[4]: stress_anchor_eviction_cases+=1
    q=Query(rng.choice(['s0','s1']),rng.choice(['A','B']),'NOW',None,rng.randint(0,100),0,rng.randint(0,6),rng.randint(0,500),rng.choice(strategies),None)
    check(b,full,gs,am,cfg,q,query_now); stress_queries+=1
    stress_records+=n; stress_cases+=1
assert stress_gap_overflow_cases>0 and stress_anchor_eviction_cases>0

# bounded exhaustive: small sequences, all strategies/budgets/scopes
atoms=[('s0','A',False,True,10),('s0','A',True,True,20),('s0','B',False,False,30),('s1','A',False,True,40)]
exhaustive=0
for n in range(0,5):
    for combo in itertools.product(atoms, repeat=n):
        rows=[]; t=0
        for i,(s,u,k,ch,sz) in enumerate(combo):
            t+=2; rows.append((Observation(f'e{i}',i+1,t,s,u,20,20,sz,k,ch,False),t))
        cfg=(3,70,6); b,full,gs,am=build_case(rows,cfg)
        now=t
        for strat in strategies:
            for maxf in (0,1,2,4):
                for maxb in (0,15,50,100):
                    q=Query('s0','A','NOW',None,10,0,maxf,maxb,strat,None)
                    check(b,full,gs,am,cfg,q,now); exhaustive+=1
summary={'status':'CONSTRUCTION_PASS','seed':102820260918001,'random_cases':cases,'random_records':records,'random_queries':queries,
         'metadata_stress_cases':stress_cases,'metadata_stress_records':stress_records,'metadata_stress_queries':stress_queries,
         'metadata_gap_overflow_cases':stress_gap_overflow_cases,'metadata_anchor_eviction_cases':stress_anchor_eviction_cases,
         'exhaustive_queries':exhaustive,'candidate_oracle_mismatches':0,'current_role_errors':current_role_errors,
         'budget_errors':budget_errors,'cross_scope_errors':cross_scope_errors,'grants_input_authority':False}
summary['digest']=hashlib.sha256(json.dumps(summary,sort_keys=True,separators=(',',':')).encode()).hexdigest()
print(json.dumps(summary,indent=2,sort_keys=True))
