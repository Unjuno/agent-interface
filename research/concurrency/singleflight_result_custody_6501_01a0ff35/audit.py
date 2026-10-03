"""Independent parsed-data ownership reducer; no candidate/runtime imports."""
import copy
import hashlib
import json
from pathlib import Path


class AuditError(ValueError):pass


def encoded(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def sha(value):return hashlib.sha256(encoded(value)).hexdigest()


def demand(ok,code):
    if not ok:raise AuditError(code)


def exact(actual,expected,code):demand(encoded(actual)==encoded(expected),code)


def changed(original,schedule):
    result=copy.deepcopy(original)
    if schedule=='caller_top':result['generation']=8
    elif schedule in ('caller_nested','owner_nested'):result['answer']['visible']=True
    elif schedule=='caller_list':result['answer']['coordinates'].append(99)
    elif schedule!='none':raise AuditError('unknown_schedule')
    return result


def inspect(raw,freeze_bytes,fixture_bytes):
    freeze=json.loads(freeze_bytes);fixtures=json.loads(fixture_bytes)
    exact(raw['schema'],'result-custody-raw-v1','schema')
    exact(raw['allocation'],freeze['allocation'],'allocation')
    exact(raw['freeze_sha256'],hashlib.sha256(freeze_bytes).hexdigest(),'freeze_pin')
    exact(raw['fixture_sha256'],hashlib.sha256(fixture_bytes).hexdigest(),'fixture_pin')
    exact(raw['source_sha256'],freeze['source_sha256'],'source_pin')
    exact(raw['runtime'],freeze['runtime'],'runtime_pin')
    exact(raw['backend_calls'],0,'backend');exact(raw['input_emissions'],0,'input')
    original=fixtures['payload'];original_sha=sha(original)
    policies=fixtures['policies'];schedules=fixtures['schedules']
    expected_ids={p+'.'+s for p in policies for s in schedules}
    demand(type(raw['rows']) is list and len(raw['rows'])==len(expected_ids)==30,'case_coverage')
    seen=set();failures={p:[] for p in policies};naive_failures=[];producer_total=0
    for row in raw['rows']:
        p,s=row['policy'],row['schedule'];key=p+'.'+s
        demand(key in expected_ids and key not in seen and row['id']==key,'case_coverage');seen.add(key)
        calls=2 if p=='independent' else 1
        exact(row['read_calls'],calls,'read_calls');producer_total+=calls
        exact(row['original_snapshot_sha256'],original_sha,'original_pin')
        a=changed(original,s) if s.startswith('caller_') or s=='owner_nested' and p in ('independent','shared','shallow_delivery') else copy.deepcopy(original)
        b_changes=(p=='shared' and s!='none' or
                   p=='shallow_delivery' and s in ('caller_nested','caller_list','owner_nested') or
                   p=='deep_delivery' and s=='owner_nested')
        b=changed(original,s) if b_changes else copy.deepcopy(original)
        owner_changes=(s=='owner_nested' or p in ('independent','shared') and s.startswith('caller_') or
                       p=='shallow_delivery' and s in ('caller_nested','caller_list'))
        owner=changed(original,s) if owner_changes else copy.deepcopy(original)
        exact(row['a_final'],a,'a_value');exact(row['b_final'],b,'b_value')
        exact(row['first_owner_final'],owner,'owner_value')
        integrity=sha(b)==original_sha
        naive=b['generation']==original['generation'] and b['target']==original['target'] and b['answer']['visible'] is True
        exact(row['b_snapshot_sha256'],sha(b),'b_pin')
        exact(row['b_snapshot_matches_original'],integrity,'integrity')
        exact(row['naive_scope_only_admission'],naive,'naive_admission')
        exact(row['digest_admission'],naive and integrity,'digest_admission')
        exact(row['identity'],{'same_view_root':p=='shared',
             'same_answer':p in ('shared','shallow_delivery'),
             'same_coordinates':p in ('shared','shallow_delivery'),
             'same_carrier':p!='independent','a_is_first_owner':p in ('independent','shared'),
             'b_is_first_owner':p=='shared'},'identity')
        exact(row['producer_tasks_terminal'],True,'cleanup');exact(row['waiter_tasks_terminal'],True,'cleanup')
        events=row['events'];demand(type(events) is list,'event_coverage')
        kinds={kind:[] for kind in ('read_enter','read_snapshot','read_return','waiter_join',
                                  'producer_release','delivery','post_completion_edit','cleanup')}
        for position,event in enumerate(events):
            exact(event['ordinal'],position,'event_ordinal')
            demand(event['kind'] in kinds,'event_coverage');kinds[event['kind']].append(event)
        for kind in ('read_enter','read_snapshot','read_return'):demand(len(kinds[kind])==calls,'event_coverage')
        for kind in ('waiter_join','delivery'):demand(len(kinds[kind])==2,'event_coverage')
        for kind in ('producer_release','post_completion_edit','cleanup'):demand(len(kinds[kind])==1,'event_coverage')
        release=kinds['producer_release'][0]['ordinal'];edit=kinds['post_completion_edit'][0]['ordinal']
        joins={event['waiter']:event['ordinal'] for event in kinds['waiter_join']}
        deliveries={event['waiter']:event for event in kinds['delivery']}
        exact(sorted(joins),['A','B'],'event_waiters');exact(sorted(deliveries),['A','B'],'event_waiters')
        demand(max(joins.values())<release,'event_order')
        demand(deliveries['A']['ordinal']<edit<deliveries['B']['ordinal'],'event_order')
        for name,value in (('A',original),('B',b)):
            exact(deliveries[name]['snapshot'],value,'delivery_value')
            exact(deliveries[name]['sha256'],sha(value),'delivery_pin')
        for call in range(calls):
            chain=[]
            for kind in ('read_enter','read_snapshot','read_return'):
                entries=[event for event in kinds[kind] if type(event['call']) is int and event['call']==call]
                demand(len(entries)==1,'event_calls');chain.append(entries[0]['ordinal'])
                if kind=='read_snapshot':
                    exact(entries[0]['snapshot'],original,'read_value');exact(entries[0]['sha256'],original_sha,'read_pin')
                if kind=='read_return':exact(entries[0]['carrier_kind'],'bytes' if p=='json_completion' else 'dict','carrier_kind')
            demand(chain[0]<release<chain[1]<chain[2]<edit,'event_order')
        exact(kinds['post_completion_edit'][0]['schedule'],s,'edit_schedule')
        exact(kinds['post_completion_edit'][0]['a_snapshot'],a,'edit_value')
        exact(kinds['post_completion_edit'][0]['first_owner_snapshot'],owner,'edit_owner')
        exact(kinds['post_completion_edit'][0]['producer_done'],True,'edit_done')
        exact(kinds['cleanup'][0]['producer_tasks_terminal'],True,'cleanup')
        exact(kinds['cleanup'][0]['waiter_tasks_terminal'],True,'cleanup')
        demand(kinds['cleanup'][0]['ordinal']==len(events)-1,'event_order')
        if not integrity:failures[p].append(s)
        if naive:naive_failures.append(key)
    demand(seen==expected_ids,'case_coverage')
    demand(failures['deep_completion']==failures['json_completion']==[],'snapshot_policy_failure')
    return {'verdict':'PASS_RESULT_CUSTODY_CHARACTERIZATION_SCOPED','rows':30,'deliveries':60,
            'producer_calls':producer_total,'b_snapshot_failures_by_policy':failures,
            'naive_scope_only_false_admissions':naive_failures,'digest_false_admissions':0,
            'all_terminal_cleanup_verified':True}


def corruption_controls(raw,freeze_bytes,fixtures_bytes):
    tests=[]
    def change(name,code,fn):
        modified=copy.deepcopy(raw);fn(modified);tests.append((name,code,modified))
    change('read_count_float','read_calls',lambda r:r['rows'][0].__setitem__('read_calls',2.0))
    def falsify_value(r):
        row=r['rows'][-5];row['b_final']['answer']['visible']=True
        row['b_snapshot_sha256']=sha(row['b_final']);row['b_snapshot_matches_original']=False
        for event in row['events']:
            if event['kind']=='delivery' and event['waiter']=='B':
                event['snapshot']=copy.deepcopy(row['b_final']);event['sha256']=sha(row['b_final'])
    change('changed_value_rehashed','b_value',falsify_value)
    def omit_event(r):
        row=r['rows'][0];row['events']=[e for e in row['events'] if e['kind']!='post_completion_edit']
        for n,e in enumerate(row['events']):e['ordinal']=n
    change('missing_edit_event','event_coverage',omit_event)
    change('false_freeze_pin','freeze_pin',lambda r:r.__setitem__('freeze_sha256','0'*64))
    change('false_alias','identity',lambda r:r['rows'][0]['identity'].__setitem__('same_answer',True))
    change('false_admission','naive_admission',lambda r:r['rows'][0].__setitem__('naive_scope_only_admission',True))
    change('nonterminal_waiter','cleanup',lambda r:r['rows'][0].__setitem__('waiter_tasks_terminal',False))
    change('missing_case','case_coverage',lambda r:r['rows'].pop())
    results=[]
    for name,code,modified in tests:
        demand(encoded(modified)!=encoded(raw),'ineffective_control')
        try:inspect(modified,freeze_bytes,fixtures_bytes)
        except AuditError as error:
            exact(str(error),code,'wrong_control_reason')
            results.append({'name':name,'rejected':True,'reason':str(error),'modified_sha256':sha(modified)})
        else:raise AuditError('accepted_corruption:'+name)
    return results


def main():
    root=Path(__file__).resolve().parent
    frozen=(root/'FREEZE.json').read_bytes();fixtures=(root/'fixtures.json').read_bytes()
    freeze=json.loads(frozen)
    for name,pin in freeze['source_sha256'].items():
        demand(hashlib.sha256((root/name).read_bytes()).hexdigest()==pin,'frozen_file:'+name)
    raw=json.loads((root/'evidence/raw.json').read_bytes())
    result=inspect(raw,frozen,fixtures)
    result['corruption_controls']=corruption_controls(raw,frozen,fixtures)
    result['raw_sha256']=hashlib.sha256((root/'evidence/raw.json').read_bytes()).hexdigest()
    with (root/'evidence/audit.json').open('xb') as file:file.write(encoded(result)+b'\n')
    print(json.dumps(result,indent=2,sort_keys=True))


if __name__=='__main__':main()
