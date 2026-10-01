import argparse, hashlib, json, pathlib, sys

SCORER_SOURCE = """def score(case, app_profile):
    if case.get('saved') is None or case.get('selected_id') is None:
        return 'UNKNOWN'
    if not case['saved']:
        return 'FAIL'
    if case.get('collateral'):
        return 'FAIL'
    return 'PASS' if case['selected_id'] == case['target'] else 'FAIL'
"""
SCORER_SHA = hashlib.sha256(SCORER_SOURCE.encode()).hexdigest()
SCORER_V2_SOURCE = """def score_v2(case, app_profile):
    selected = case.get('selected_object', case.get('selected_id'))
    if case.get('saved') is None or selected is None:
        return 'UNKNOWN'
    if not case['saved'] or case.get('collateral'):
        return 'FAIL'
    return 'PASS' if selected == case['target'] else 'FAIL'
"""
SCORER_V2_SHA = hashlib.sha256(SCORER_V2_SOURCE.encode()).hexdigest()

def scorer(case, app_profile):
    if case.get('saved') is None or case.get('selected_id') is None:
        return 'UNKNOWN'
    if not case['saved'] or case.get('collateral'):
        return 'FAIL'
    return 'PASS' if case['selected_id'] == case['target'] else 'FAIL'

def scorer_v2(case, app_profile):
    selected = case.get('selected_object', case.get('selected_id'))
    if case.get('saved') is None or selected is None:
        return 'UNKNOWN'
    if not case['saved'] or case.get('collateral'):
        return 'FAIL'
    return 'PASS' if selected == case['target'] else 'FAIL'

def semantic_reference(case, profile):
    if case.get('saved') is None or case.get('selected_id') is None:
        return 'UNKNOWN'
    if not case['saved'] or case.get('collateral'):
        return 'FAIL'
    mapping = profile.get('selected_id_to_effective_target', profile.get('selected_object_to_effective_target', {}))
    effective = mapping.get(case['selected_id'])
    if effective is None:
        return 'UNKNOWN'
    return 'PASS' if effective == case['target'] else 'FAIL'

def sha(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def file_sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--deck',required=True); ap.add_argument('--freeze',required=True); ap.add_argument('--out',required=True); a=ap.parse_args()
    deck=json.loads(pathlib.Path(a.deck).read_text(encoding='utf-8-sig')); freeze=json.loads(pathlib.Path(a.freeze).read_text())
    if file_sha(__file__) != freeze['candidate_source_sha256']:
        raise SystemExit('FROZEN_CANDIDATE_HASH_MISMATCH')
    cases=deck['cases']; refs=deck['frozen_reference_labels']; profiles=deck['app_profiles']; results=[]
    for name, profile_name, score_name, source_hash in [
        ('nominal','app-v1','v1',SCORER_SHA),
        ('semantic_drift_unchanged_scorer','app-v2-semantic-drift','v1',SCORER_SHA),
        ('equivalent_version_change','app-v2-equivalent-schema','v2',SCORER_V2_SHA),
        ('out_of_coverage','app-v1','v1',SCORER_SHA)]:
        profile=profiles[profile_name]; score_fn=scorer if score_name=='v1' else scorer_v2
        rows=[]
        for c in cases:
            observed=dict(c)
            if score_name=='v2':
                observed['selected_object']=observed.pop('selected_id',None)
            pred=score_fn(observed,profile)
            ref=semantic_reference(c,profile)
            rows.append({'case_id':c['id'],'prediction':pred,'independent_reference':ref,'frozen_label':refs[c['id']]})
        event=deck['candidate_events'][0 if name!='out_of_coverage' else 1]
        event_observed=dict(event)
        if score_name=='v2':
            event_observed['selected_object']=event_observed.pop('selected_id',None)
        epred=score_fn(event_observed,profile)
        covered=event['kind'] in deck['coverage']
        pre_ok=all(x['prediction']==x['frozen_label'] for x in [{'prediction':scorer(c,profiles['app-v1']),'frozen_label':refs[c['id']]} for c in cases])
        # A bracket is valid only while the current-semantic independent
        # reference agrees with both the scorer and the frozen reference label.
        post_ok=all(x['prediction']==x['independent_reference']==x['frozen_label'] for x in rows)
        if not covered: disposition='UNKNOWN_COVERAGE'
        elif not pre_ok or not post_ok: disposition='HOLD_ORACLE_DRIFT'
        else: disposition='ELIGIBLE_FOR_FURTHER_TASK_AUDIT'
        results.append({'scenario':name,'app_profile':profile_name,'scorer_version':score_name,'scorer_sha256':source_hash,
          'scorer_hash_unchanged_from_v1':source_hash==SCORER_SHA,'precheck':{'deck_id':deck['deck_id'],'rows':[{'case_id':c['id'],'prediction':scorer(c,profiles['app-v1']),'independent_reference':semantic_reference(c,profiles['app-v1']),'frozen_label':refs[c['id']]} for c in cases]},
          'postcheck':{'deck_id':deck['deck_id'],'rows':rows},'candidate_event':{'id':event['id'],'kind':event['kind'],'prediction':epred},
          'coverage_declared':covered,'disposition':disposition})
    raw={'schema':'oracle-check-t0-raw-v1','freeze_id':freeze['freeze_id'],'deck_sha256':sha(deck),'reference_lock_sha256':sha(refs),
      'candidate_source_sha256':file_sha(__file__),
      'run_order':['precheck','candidate_event','postcheck'],'results':results}
    pathlib.Path(a.out).write_text(json.dumps(raw,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({'status':'CANDIDATE_COMPLETE','freeze_id':freeze['freeze_id'],'deck_sha256':raw['deck_sha256'],'rows':len(results),'scorer_v1_sha256':SCORER_SHA,'scorer_v2_sha256':SCORER_V2_SHA,'out':a.out},sort_keys=True))
if __name__=='__main__': main()
