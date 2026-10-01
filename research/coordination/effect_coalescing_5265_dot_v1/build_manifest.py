"""Author the finite fixture; never imports any policy implementation."""
import copy, itertools, json
from pathlib import Path

BASE=dict(session='s',producer='A',retry_intent='retry-A',attempt='attempt-A',common_work_id='work-save-1',revision=1,generation=1,target='save',incarnation=1,operation='click',opportunity='save-once-1',params={'value':1},deadline=10,authorized=True,identity='exact')

def p(producer='A', **changes):
    return dict(BASE,producer=producer,retry_intent='retry-'+producer,attempt='attempt-'+producer,**changes)

def submit(proposal, goal='G1', now=1, deny=None, **kw):
    return dict(kind='proposal',now=now,proposal=proposal,oracle_goal=goal,oracle_deny=deny,**kw)

def transition(**update): return dict(kind='transition',update=update)

cases=[]
def add(name,events,permute=False,subset='shared_id_primary'):
    schedules=list(itertools.permutations(range(len(events)))) if permute else [tuple(range(len(events)))]
    for i, order in enumerate(schedules):
        cases.append(dict(id=f'{name}--{i}',family=name,subset=subset,events=[copy.deepcopy(events[j]) for j in order]))

add('same_state_two_independent',[submit(p()),submit(p('B'))],True)
add('same_state_three_independent',[submit(p()),submit(p('B')),submit(p('C'))],True)
add('same_producer_retry',[submit(p()),submit(dict(p(),attempt='retry-attempt'))],True)
add('changed_incarnation',[submit(p()),transition(incarnations={'save':2,'next':1,'other':1}),submit(p('B',incarnation=2,common_work_id='work-save-inc2'),'G2')])
add('different_intent_same_generation',[submit(p()),submit(p('B',revision=2,common_work_id='work-revision2'),'G2')],True)
add('different_target_same_coordinates',[submit(p()),submit(p('B',target='other',common_work_id='work-other'),'G2')],True)
add('different_parameters_distinct_work',[submit(p()),submit(p('B',params={'value':2},common_work_id='work-value2'),'G2')],True)
add('different_operation',[submit(p()),submit(p('B',operation='double-click',common_work_id='work-double'),'G2')],True)
add('different_opportunity_same_generation',[submit(p()),submit(p('B',opportunity='save-once-2',common_work_id='work-save-2'),'G2')],True)
add('next_after_verified_transition',[submit(p(target='next',opportunity='page1-next',common_work_id='next1')),transition(generation=2),submit(p('B',target='next',generation=2,opportunity='page2-next',common_work_id='next2'),'G2')])
add('late_verified_satisfied',[submit(p()),submit(p('B'),None,deny='SUPERSEDED',postcondition_satisfied=True)])
add('late_stale_after_transition',[submit(p()),transition(generation=2),submit(p('B'),None,deny='REJECT_STALE')])
add('retry_changed_parameters',[submit(p()),submit(dict(p(),attempt='retry2',params={'value':2}),None,deny='REJECT_RETRY_CONFLICT')])
for field in ('session','revision','generation','target','incarnation','operation','opportunity','params','producer','retry_intent'):
    q=p();q[field]=None
    add('missing_'+field,[submit(q,None,deny='YIELD_IDENTITY')])
add('ambiguous_identity',[submit(p(identity='ambiguous'),None,deny='YIELD_IDENTITY')])
add('unauthorized_equivalent_first',[submit(p(authorized=False),None,deny='REJECT_AUTHORITY'),submit(p('B'))])
add('unauthorized_equivalent_late',[submit(p()),submit(p('B',authorized=False),None,deny='REJECT_AUTHORITY')])
for tick in (9,10,11):
    add('deadline_'+str(tick),[submit(p(), 'G1' if tick<=10 else None,now=tick,deny=None if tick<=10 else 'REJECT_EXPIRED')])
add('expired_cached_equivalent',[submit(p()),submit(p('B'),None,now=11,deny='REJECT_EXPIRED')])
add('revoked_cached_equivalent',[submit(p()),transition(revoked=True),submit(p('B'),None,deny='REJECT_AUTHORITY'),dict(kind='release',oracle_goal=None,oracle_deny='RELEASED')])
add('same_attempt_different_session',[submit(p()),submit(p('B',session='s2'),'G2')],True)
add('stale_incarnation',[submit(p(incarnation=0),None,deny='REJECT_STALE')])
add('stale_intent',[submit(p(revision=0),None,deny='REJECT_STALE')])
add('common_id_absent_residual',[submit(p(common_work_id=None)),submit(p('B',common_work_id=None))],True,subset='identity_assignment_boundary')
# No amount of serialization identifies two different logical goals in one generation.
manifest=dict(schema='effect-coalescing-finite-v1',cases=cases,randomness='none',atomicity='one admission+effect+release transaction per proposal',bounds=dict(max_trace_events=max(len(c['events']) for c in cases),retained_records_per_table=16))
Path('CASE_MANIFEST.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n')
print(json.dumps(dict(cases=len(cases),families=len({c['family'] for c in cases}),primary=sum(c['subset']=='shared_id_primary' for c in cases),boundary=sum(c['subset']!='shared_id_primary' for c in cases))))
