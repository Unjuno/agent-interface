import argparse, copy, json, random
from candidate import anchored_bounded_skew, pairwise_skew_only, strict_anchor
from oracle import oracle_join

TASK='OBSERVATION-EPOCH-BOUNDED-SKEW-R1-20260918-001'
SEED=4220260918001
FIELDS=('focus','target_binding','image','ui_context')
CATS=('VALID_SKEW','CRITICAL_EXPIRED','IDENTITY_MISMATCH','MALFORMED','VALID_STRICT','GENERATION_MISMATCH')

def field(t,gen=7,valid=None):
    d={'session':'s1','surface':'surface-A','generation':gen,'sample_time':t}
    if valid is not None: d['valid_through']=valid
    return d

def base_row(anchor, strict=False):
    if strict:
        times={k:anchor for k in FIELDS}
    else:
        times={'focus':anchor-1,'target_binding':anchor,'image':anchor-2,'ui_context':anchor-1}
    return {'now':anchor,'fields':{
        'focus':field(times['focus'],valid=anchor+2),
        'target_binding':field(times['target_binding'],valid=anchor+2),
        'image':field(times['image']),
        'ui_context':field(times['ui_context']),
    }}

def make_row(i,rng):
    cat=CATS[i%len(CATS)]; anchor=10+rng.randrange(0,1000)
    if cat=='VALID_SKEW':
        row=base_row(anchor,False); truth=True
    elif cat=='CRITICAL_EXPIRED':
        row=base_row(anchor,False); row['fields']['focus']['valid_through']=anchor-1; truth=False
    elif cat=='IDENTITY_MISMATCH':
        row=base_row(anchor,False); row['fields']['image']['surface']='surface-B'; truth=False
    elif cat=='GENERATION_MISMATCH':
        row=base_row(anchor,False); row['fields']['target_binding']['generation']=8; truth=False
    elif cat=='VALID_STRICT':
        row=base_row(anchor,True); truth=True
    else:
        row=base_row(anchor,False); truth=False
        sub=(i//len(CATS))%4
        if sub==0: del row['fields']['ui_context']
        elif sub==1: row['fields']['image']['sample_time']='bad'
        elif sub==2: row['fields']['image']['sample_time']=anchor+1
        else: row['fields']['focus']['valid_through']='bad'
    return cat,row,truth

def directed():
    a=100
    stale=base_row(a,False); stale['fields']['focus']['valid_through']=a-1
    stagger=base_row(a,False)
    return {
      'focus_mutation': {'candidate':anchored_bounded_skew(stale),'naive':pairwise_skew_only(stale),'oracle':oracle_join(stale)},
      'valid_stagger': {'candidate':anchored_bounded_skew(stagger),'strict':strict_anchor(stagger),'oracle':oracle_join(stagger)}
    }

def execute(rows):
    rng=random.Random(SEED)
    m={
      'rows':rows,'seed':SEED,'candidate_oracle_mismatch':0,'candidate_stale_critical_joins':0,
      'candidate_cross_identity_generation_joins':0,'candidate_malformed_missing_future_joins':0,
      'valid_candidate_joins':0,'valid_candidate_joins_rejected_by_strict':0,
      'naive_stale_critical_joins':0,'critical_expiry_rows':0,'identity_generation_mismatch_rows':0,
      'malformed_missing_future_rows':0
    }
    category_counts={c:0 for c in CATS}
    for i in range(rows):
        cat,row,truth=make_row(i,rng); category_counts[cat]+=1
        c=anchored_bounded_skew(row); o=oracle_join(row); n=pairwise_skew_only(row); s=strict_anchor(row)
        if c!=o: m['candidate_oracle_mismatch']+=1
        if c: m['valid_candidate_joins']+=1
        if truth and c and not s: m['valid_candidate_joins_rejected_by_strict']+=1
        if cat=='CRITICAL_EXPIRED':
            m['critical_expiry_rows']+=1
            if c: m['candidate_stale_critical_joins']+=1
            if n: m['naive_stale_critical_joins']+=1
        if cat in ('IDENTITY_MISMATCH','GENERATION_MISMATCH'):
            m['identity_generation_mismatch_rows']+=1
            if c: m['candidate_cross_identity_generation_joins']+=1
        if cat=='MALFORMED':
            m['malformed_missing_future_rows']+=1
            if c: m['candidate_malformed_missing_future_joins']+=1
    d=directed()
    m['category_counts']=category_counts
    formal=rows==300000
    gates=[m['candidate_oracle_mismatch']==0,m['candidate_stale_critical_joins']==0,
           m['candidate_cross_identity_generation_joins']==0,m['candidate_malformed_missing_future_joins']==0,
           m['valid_candidate_joins']>0,m['naive_stale_critical_joins']>0,
           d['focus_mutation']=={'candidate':False,'naive':True,'oracle':False},
           d['valid_stagger']=={'candidate':True,'strict':False,'oracle':True}]
    if formal:
        gates += [m['critical_expiry_rows']>=50000,m['valid_candidate_joins_rejected_by_strict']>=50000,
                  m['identity_generation_mismatch_rows']>=50000,m['malformed_missing_future_rows']>=25000]
    if not all(gates):
        if m['candidate_stale_critical_joins']: dec='FAIL_CRITICAL_FIELD_SKEW_LEAK'
        elif m['candidate_oracle_mismatch'] or m['candidate_cross_identity_generation_joins'] or m['candidate_malformed_missing_future_joins']: dec='FAIL_INTEGRITY'
        else: dec='FAIL_BOUNDED_SKEW_OVERINVALIDATION'
    else:
        dec='PASS_OBSERVATION_EPOCH_BOUNDED_SKEW_R1_SCOPED' if formal else 'PASS_CONSTRUCTION_ELIGIBLE'
    return {'task':TASK,'phase':'formal' if formal else 'construction','formal_invocations':1 if formal else 0,
            'reruns':0,'replacements':0,'tuning':0,'decision':dec,'directed':d,'metrics':m}

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--rows',type=int,default=6000); ap.add_argument('--out',required=True); a=ap.parse_args()
    r=execute(a.rows)
    with open(a.out,'w') as f: json.dump(r,f,indent=2,sort_keys=True)
    print(json.dumps(r,indent=2,sort_keys=True))
