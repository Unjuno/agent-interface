#!/usr/bin/env python3
import argparse, json, pathlib, sys
HERE=pathlib.Path(__file__).resolve().parent
VOCAB={"ADDED","REMOVED","MODIFIED","UNCHANGED","UNKNOWN"}

def load(path): return json.loads(pathlib.Path(path).read_text(encoding='utf-8'))

def state_delta(case):
    if case['base_id'] != case['current_base_id']:
        return {'status':'BASE_MISMATCH','changes':[{'path':'*','change':'UNKNOWN','critical':True}], 'authority':'none'}
    before=case.get('before',{}); after=case.get('after',{})
    kb=set(case.get('known_before',before.keys())); ka=set(case.get('known_after',after.keys()))
    rows=[]; critical=set(case.get('_critical_paths',[]))
    for p in sorted(set(before)|set(after)|kb|ka):
        if p not in kb or p not in ka:
            kind='UNKNOWN'; b=before.get(p) if p in kb else None; a=after.get(p) if p in ka else None
        else:
            b=before.get(p); a=after.get(p)
            if p not in before and p in after: kind='ADDED'
            elif p in before and p not in after: kind='REMOVED'
            elif b==a: kind='UNCHANGED'
            else: kind='MODIFIED'
        rows.append({'path':p,'change':kind,'before':b,'after':a,'critical':p in critical})
    return {'status':'OK','changes':rows,'authority':'none'}

def endpoint(case):
    d=state_delta(case)
    return {'representation':'ENDPOINT_STATE_DELTA','status':d['status'],'state_changes':d['changes'],'critical_events':[], 'authority':'none'}

def event_aware(case):
    d=state_delta(case); critical=set(case.get('_critical_paths',[])); events=[]
    for e in case.get('events',[]):
        if e['kind'] not in VOCAB: raise ValueError('bad_event_vocab')
        events.append({'path':e['path'],'change':e['kind'],'before':e.get('before'),'after':e.get('after'),'source':e['source'],'critical':e['path'] in critical})
    return {'representation':'EVENT_AWARE_SEMANTIC_DELTA','status':d['status'],'state_changes':d['changes'],'critical_events':events,'authority':'none'}

def score(case,out):
    changes={r['path']:r for r in out['state_changes']}
    row={'case':case['id'],'domain':case.get('domain'),'representation':out['representation'],'output':out}
    if 'expected_unknown' in case: row['unknown_ok']=all(changes.get(p,{}).get('change')=='UNKNOWN' for p in case['expected_unknown'])
    if 'expected_critical_event_count' in case:
        row['critical_count_ok']=(len(out['critical_events'])==case['expected_critical_event_count']) if out['representation']=='EVENT_AWARE_SEMANTIC_DELTA' else None
    if case.get('expect_endpoint_alias'):
        row['endpoint_alias_observed']=(changes['focus.owner']['change']=='UNCHANGED' and len(out['critical_events'])==0) if out['representation']=='ENDPOINT_STATE_DELTA' else None
        row['excursion_retained']=(len([e for e in out['critical_events'] if e['path']=='focus.owner'])==2) if out['representation']=='EVENT_AWARE_SEMANTIC_DELTA' else None
    return row

def run(fixture):
    rows=[]; critical=fixture['critical_paths']
    for raw in fixture['cases']:
        case=dict(raw); case['_critical_paths']=critical
        rows.append(score(case,endpoint(case))); rows.append(score(case,event_aware(case)))
    neg=[]
    for raw in fixture['negative_controls']:
        c=dict(raw); c['_critical_paths']=critical; d=event_aware(c); changes={r['path']:r for r in d['state_changes']}
        if c['id']=='base-mismatch': ok=d['status']=='BASE_MISMATCH' and changes['*']['change']=='UNKNOWN'
        elif c['id']=='missing-critical': ok=changes['task.effect']['change']=='UNKNOWN'
        else: ok=False
        neg.append({'control':c['id'],'pass':ok,'output':d})
    e=[r for r in rows if r['representation']=='EVENT_AWARE_SEMANTIC_DELTA']; p=[r for r in rows if r['representation']=='ENDPOINT_STATE_DELTA']
    wf_e=next(r for r in e if r['case']=='calc-workflow-excursion'); wf_p=next(r for r in p if r['case']=='calc-workflow-excursion')
    gates={
      'row_count_16':len(rows)==16,
      'calc_excursion_event_aware':wf_e.get('excursion_retained') is True and wf_e.get('critical_count_ok') is True,
      'calc_endpoint_alias_discriminator':wf_p.get('endpoint_alias_observed') is True,
      'all_event_critical_counts':all(r.get('critical_count_ok',True) is True for r in e),
      'unknown_semantics':all(r.get('unknown_ok',True) is True for r in rows),
      'base_and_missing_controls':all(x['pass'] for x in neg),
      'authority_none':all(r['output']['authority']=='none' for r in rows) and all(x['output']['authority']=='none' for x in neg),
      'openttd_second_domain_present':sum(r['domain']=='openttd' for r in e)==4
    }
    passed=all(gates.values())
    return {'task':fixture['task'],'source_blobs':fixture['source_blobs'],'formal_invocations':1,'formal_reruns':0,'rows':rows,'negative_controls':neg,'gates':gates,'passed':passed,'decision':'PASS_SEMANTIC_DELTA_CRITICAL_RETENTION_SCOPED' if passed else 'FAIL_OR_HOLD_SEMANTIC_DELTA_CRITICAL_RETENTION','scope':'retained-evidence representation replay; no new task/model/input claim'}

def self_test(fixture):
    c={'id':'toy','base_id':'a','current_base_id':'a','before':{'x':1},'after':{'x':2},'events':[],'_critical_paths':[]}
    assert state_delta(c)['changes'][0]['change']=='MODIFIED'; c['current_base_id']='b'; assert state_delta(c)['status']=='BASE_MISMATCH'
    c={'id':'toy2','base_id':'a','current_base_id':'a','before':{'x':1},'after':{},'known_before':['x'],'known_after':[],'events':[],'_critical_paths':[]}
    assert state_delta(c)['changes'][0]['change']=='UNKNOWN'; print(json.dumps({'self_test':'PASS'}))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--fixture',default=str(HERE/'fixture.json')); ap.add_argument('--output'); ap.add_argument('--self-test',action='store_true'); a=ap.parse_args(); f=load(a.fixture)
    if a.self_test: self_test(f); return
    text=json.dumps(run(f),indent=2,sort_keys=True)+'\n'
    if a.output: pathlib.Path(a.output).write_text(text,encoding='utf-8',newline='\n')
    else: sys.stdout.write(text)
if __name__=='__main__': main()
