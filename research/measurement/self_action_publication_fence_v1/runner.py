from __future__ import annotations
import argparse, hashlib, json, random
from pathlib import Path
from candidate import PublicationFence
from oracle import reduce_history

TASK='SELF-ACTION-PUBLICATION-FRESHNESS-FENCE-20260918-001'
SEED=149020260918001
FORMAL_N=240_000
SCOPES=('s0','s1','s2','s3')
COUNTS=[
    ('LAG_RELEVANT',50_000),
    ('POST_NEGATIVE',40_000),
    ('POST_POSITIVE',40_000),
    ('IRRELEVANT',25_000),
    ('STALE_COVER',30_000),
    ('ORD_FALSE',15_000),
    ('WRONG_SCOPE',10_000),
    ('FUTURE_COVER',10_000),
    ('DUP_ACTION',10_000),
    ('DUP_EVIDENCE_CONFLICT',10_000),
]

def spec_for(i:int, category:str)->dict:
    scope=SCOPES[i%4]
    e0=f'e{i:06d}-0'; e1=f'e{i:06d}-1'; a1=f'a{i:06d}-1'
    ops=[]
    if category=='LAG_RELEVANT':
        ops=[{'kind':'OBSERVE','evidence_id':e0,'visual_guard':True,'covered_action_seq':0},
             {'kind':'SELF_ACTION','action_id':a1,'relevant':True},
             {'kind':'TRY_EFFECT','evidence_id':e0,'ordinary_authority':True}]
    elif category=='POST_NEGATIVE':
        ops=[{'kind':'OBSERVE','evidence_id':e0,'visual_guard':True,'covered_action_seq':0},
             {'kind':'SELF_ACTION','action_id':a1,'relevant':True},
             {'kind':'OBSERVE','evidence_id':e1,'visual_guard':False,'covered_action_seq':1},
             {'kind':'TRY_EFFECT','evidence_id':e1,'ordinary_authority':True}]
    elif category=='POST_POSITIVE':
        ops=[{'kind':'OBSERVE','evidence_id':e0,'visual_guard':True,'covered_action_seq':0},
             {'kind':'SELF_ACTION','action_id':a1,'relevant':True},
             {'kind':'OBSERVE','evidence_id':e1,'visual_guard':True,'covered_action_seq':1},
             {'kind':'TRY_EFFECT','evidence_id':e1,'ordinary_authority':True}]
    elif category=='IRRELEVANT':
        ops=[{'kind':'OBSERVE','evidence_id':e0,'visual_guard':True,'covered_action_seq':0},
             {'kind':'SELF_ACTION','action_id':a1,'relevant':False},
             {'kind':'TRY_EFFECT','evidence_id':e0,'ordinary_authority':True}]
    elif category=='STALE_COVER':
        ops=[{'kind':'OBSERVE','evidence_id':e0,'visual_guard':True,'covered_action_seq':0},
             {'kind':'SELF_ACTION','action_id':a1,'relevant':True},
             {'kind':'OBSERVE','evidence_id':e1,'visual_guard':True,'covered_action_seq':0},
             {'kind':'TRY_EFFECT','evidence_id':e1,'ordinary_authority':True}]
    elif category=='ORD_FALSE':
        ops=[{'kind':'OBSERVE','evidence_id':e0,'visual_guard':True,'covered_action_seq':0},
             {'kind':'TRY_EFFECT','evidence_id':e0,'ordinary_authority':False}]
    elif category=='WRONG_SCOPE':
        ops=[{'kind':'OBSERVE','evidence_id':e0,'visual_guard':True,'covered_action_seq':0},
             {'kind':'TRY_EFFECT','evidence_id':e0,'ordinary_authority':True,'presented_scope':'other'}]
    elif category=='FUTURE_COVER':
        ops=[{'kind':'SELF_ACTION','action_id':a1,'relevant':True},
             {'kind':'OBSERVE','evidence_id':e1,'visual_guard':True,'covered_action_seq':2},
             {'kind':'TRY_EFFECT','evidence_id':e1,'ordinary_authority':True}]
    elif category=='DUP_ACTION':
        ops=[{'kind':'OBSERVE','evidence_id':e0,'visual_guard':True,'covered_action_seq':0},
             {'kind':'SELF_ACTION','action_id':a1,'relevant':True},
             {'kind':'SELF_ACTION','action_id':a1,'relevant':True},
             {'kind':'OBSERVE','evidence_id':e1,'visual_guard':True,'covered_action_seq':1},
             {'kind':'TRY_EFFECT','evidence_id':e1,'ordinary_authority':True}]
    elif category=='DUP_EVIDENCE_CONFLICT':
        ops=[{'kind':'OBSERVE','evidence_id':e0,'visual_guard':True,'covered_action_seq':0},
             {'kind':'OBSERVE','evidence_id':e0,'visual_guard':False,'covered_action_seq':0},
             {'kind':'TRY_EFFECT','evidence_id':e0,'ordinary_authority':True}]
    else: raise ValueError(category)
    return {'trace_id':f't{i:06d}','scope':scope,'category':category,'ops':ops}

def canonical_row(row:dict)->dict:
    if row.get('ok') is False:
        err=row.get('error','')
        if 'future' in err: cls='FUTURE_COVER'
        elif 'conflicting' in err and 'evidence' in err: cls='DUPLICATE_EVIDENCE_CONFLICT'
        elif 'conflicting' in err and 'action' in err: cls='DUPLICATE_ACTION_CONFLICT'
        elif 'bad' in err: cls='MALFORMED'
        else: cls='OTHER_ERROR'
        return {'kind':row.get('kind'),'ok':False,'error_class':cls}
    return row

def run_candidate(spec:dict)->dict:
    c=PublicationFence(spec['scope']); rows=[]; events=[]; step_mismatch=False
    for op in spec['ops']:
        try:
            if op['kind']=='SELF_ACTION': res=c.self_action(op['action_id'],op['relevant'])
            elif op['kind']=='OBSERVE': res=c.observe(op['evidence_id'],op['visual_guard'],op['covered_action_seq'])
            elif op['kind']=='TRY_EFFECT': res=c.try_effect(op['evidence_id'],op['ordinary_authority'],op.get('presented_scope'))
            else: raise ValueError('bad_kind')
            rows.append({'kind':op['kind'],'ok':True,'result':res})
        except ValueError as exc:
            rows.append({'kind':op['kind'],'ok':False,'error':str(exc)})
        events.append(op)
        oracle=reduce_history(spec['scope'], events)
        if c.snapshot()!=oracle['state'] or [canonical_row(x) for x in rows]!=[canonical_row(x) for x in oracle['rows']]:
            step_mismatch=True
    return {'rows':rows,'state':c.snapshot(),'step_mismatch':step_mismatch}

def visual_only(spec:dict)->dict:
    action_seq=0; evidences={}; effects=0; stale_effects=0; seen_actions=set()
    for op in spec['ops']:
        if op['kind']=='SELF_ACTION':
            if op['action_id'] not in seen_actions:
                action_seq += 1; seen_actions.add(op['action_id'])
        elif op['kind']=='OBSERVE':
            if op['covered_action_seq']<=action_seq and op['evidence_id'] not in evidences:
                evidences[op['evidence_id']]={'guard':op['visual_guard'],'cover':op['covered_action_seq']}
        elif op['kind']=='TRY_EFFECT':
            ev=evidences.get(op['evidence_id']); scope_ok=op.get('presented_scope',spec['scope'])==spec['scope']
            admitted=bool(ev and ev['guard'] and op['ordinary_authority'] and scope_ok)
            if admitted:
                effects += 1
                if spec['category'] in ('LAG_RELEVANT','STALE_COVER'): stale_effects += 1
    return {'effects':effects,'stale_effects':stale_effects}

def always_history(spec:dict)->dict:
    action_ids={}; evidences={}; effects=0; false_refusals=0; relevant_seen=False; action_seq=0
    for op in spec['ops']:
        if op['kind']=='SELF_ACTION':
            aid=op['action_id']
            if aid not in action_ids:
                action_seq+=1; action_ids[aid]=op['relevant']; relevant_seen = relevant_seen or op['relevant']
        elif op['kind']=='OBSERVE':
            if op['covered_action_seq']<=action_seq and op['evidence_id'] not in evidences:
                evidences[op['evidence_id']]={'guard':op['visual_guard'],'cover':op['covered_action_seq']}
        elif op['kind']=='TRY_EFFECT':
            ev=evidences.get(op['evidence_id']); scope_ok=op.get('presented_scope',spec['scope'])==spec['scope']
            base=bool(ev and ev['guard'] and op['ordinary_authority'] and scope_ok)
            admitted=base and not relevant_seen
            effects += int(admitted)
            if spec['category']=='POST_POSITIVE' and base and not admitted: false_refusals += 1
    return {'effects':effects,'false_refusals':false_refusals}

def schedule()->list[str]:
    cats=[]
    for cat,n in COUNTS: cats.extend([cat]*n)
    assert len(cats)==FORMAL_N
    random.Random(SEED).shuffle(cats)
    return cats

def construction()->dict:
    rows=[]
    for i,(cat,_) in enumerate(COUNTS):
        spec=spec_for(i,cat); cand=run_candidate(spec); ora=reduce_history(spec['scope'],spec['ops'])
        rows.append({'category':cat,'candidate':cand,'oracle':ora,'match':not cand['step_mismatch'] and [canonical_row(x) for x in cand['rows']]==[canonical_row(x) for x in ora['rows']] and cand['state']==ora['state'],
                     'visual_only':visual_only(spec),'always_history':always_history(spec)})
    c=PublicationFence('s0'); malformed=[]
    for label,fn in [
        ('empty_action',lambda:c.self_action('',True)),
        ('empty_evidence',lambda:c.observe('',True,0)),
        ('bad_cover',lambda:c.observe('e',True,-1)),
        ('bad_authority',lambda:c.try_effect('e','yes')),
    ]:
        try: fn(); malformed.append({'label':label,'rejected':False})
        except ValueError: malformed.append({'label':label,'rejected':True})
    return {'task':TASK,'phase':'construction','formal_invocations':0,'reruns':0,'replacements':0,'tuning':0,'rows':rows,'malformed':malformed}

def formal(source_sha256:dict)->dict:
    metrics={
        'traces':0,'candidate_oracle_mismatch':0,'publication_gap_stale_effects':0,'stale_cover_effects':0,
        'fresh_negative_effects':0,'fresh_positive_effects':0,'irrelevant_false_rejections':0,
        'ordinary_false_effects':0,'wrong_scope_effects':0,'future_cover_accepted':0,
        'duplicate_action_double_advance':0,'duplicate_evidence_conflict_accepted':0,
        'visual_only_stale_effects':0,'always_history_fresh_positive_false_refusals':0,
    }
    digest=hashlib.sha256(); samples=[]
    for i,cat in enumerate(schedule()):
        spec=spec_for(i,cat); cand=run_candidate(spec); ora=reduce_history(spec['scope'],spec['ops'])
        metrics['traces']+=1
        mismatch=cand['step_mismatch'] or [canonical_row(x) for x in cand['rows']]!=[canonical_row(x) for x in ora['rows']] or cand['state']!=ora['state']
        metrics['candidate_oracle_mismatch'] += int(mismatch)
        effect_rows=[r['result'] for r in cand['rows'] if r['kind']=='TRY_EFFECT' and r['ok']]
        admitted=sum(int(r['admitted']) for r in effect_rows)
        vo=visual_only(spec); ah=always_history(spec)
        if cat=='LAG_RELEVANT': metrics['publication_gap_stale_effects'] += admitted
        elif cat=='STALE_COVER': metrics['stale_cover_effects'] += admitted
        elif cat=='POST_NEGATIVE': metrics['fresh_negative_effects'] += admitted
        elif cat=='POST_POSITIVE': metrics['fresh_positive_effects'] += admitted
        elif cat=='IRRELEVANT': metrics['irrelevant_false_rejections'] += int(admitted!=1)
        elif cat=='ORD_FALSE': metrics['ordinary_false_effects'] += admitted
        elif cat=='WRONG_SCOPE': metrics['wrong_scope_effects'] += admitted
        elif cat=='FUTURE_COVER':
            observe_errors=[r for r in cand['rows'] if r['kind']=='OBSERVE' and not r['ok']]
            metrics['future_cover_accepted'] += int(not observe_errors)
        elif cat=='DUP_ACTION': metrics['duplicate_action_double_advance'] += int(cand['state']['action_seq']!=1)
        elif cat=='DUP_EVIDENCE_CONFLICT':
            errs=[r for r in cand['rows'] if r['kind']=='OBSERVE' and not r['ok']]
            metrics['duplicate_evidence_conflict_accepted'] += int(not errs)
        metrics['visual_only_stale_effects'] += vo['stale_effects']
        metrics['always_history_fresh_positive_false_refusals'] += ah['false_refusals']
        canonical={'i':i,'cat':cat,'candidate':cand,'oracle':ora,'visual_only':vo,'always_history':ah}
        digest.update(json.dumps(canonical,sort_keys=True,separators=(',',':')).encode())
        if len(samples)<24: samples.append(canonical)
    return {'task':TASK,'phase':'formal','seed':SEED,'formal_invocations':1,'reruns':0,'replacements':0,'tuning':0,
            'source_sha256':source_sha256,'metrics':metrics,'ledger_sha256':digest.hexdigest(),'samples':samples}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--phase',choices=['construction','formal'],required=True); ap.add_argument('--out',required=True); ap.add_argument('--source-manifest')
    a=ap.parse_args()
    if a.phase=='construction': out=construction()
    else:
        if not a.source_manifest: raise SystemExit('--source-manifest required')
        out=formal(json.loads(Path(a.source_manifest).read_text())['sha256'])
    Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'phase':a.phase,'metrics':out.get('metrics'),'rows':len(out.get('rows',[]))},sort_keys=True))
if __name__=='__main__': main()
