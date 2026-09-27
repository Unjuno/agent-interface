import copy, json, pathlib, sys
P=pathlib.Path(__file__).with_name('ledger.json')
REQ_GATES=('same_model','same_effort','same_current_and_packed_image','same_history_set','same_prompt_schema_instructions','same_session_cache_state','same_task_oracle','presentation_differs_only')

def evaluate(data):
    errors=[]
    fam=data.get('families',[]); pairs=data.get('candidate_pairs',[])
    if data.get('task')!='TEMPORAL-SHEET-RETAINED-IDENTIFIABILITY-20260918-001': errors.append('task')
    if data.get('formal_invocations')!=1 or data.get('reruns')!=0 or data.get('replacements')!=0 or data.get('tuning')!=0: errors.append('invocation_contract')
    if len(fam)<3: errors.append('family_count')
    ids={x.get('id') for x in fam}
    if len(ids)!=len(fam): errors.append('duplicate_family')
    for f in fam:
        if f.get('presentation')!='packed_temporal_sheet': errors.append(f"{f.get('id')}:presentation")
        for k in ('report','report_blob','model','effort','first_model_image_sha256','first_session_id'):
            if not f.get(k): errors.append(f"{f.get('id')}:missing_{k}")
    admissible=[]
    for p in pairs:
        if p.get('left') not in ids or p.get('right') not in ids: errors.append(p.get('id','?')+':family_ref')
        gates=p.get('gates',{})
        if set(gates)!=set(REQ_GATES): errors.append(p.get('id','?')+':gate_shape')
        computed=all(v=='PASS' for v in gates.values())
        if p.get('admissible')!=computed: errors.append(p.get('id','?')+':admissible_label')
        if computed: admissible.append(p.get('id'))
        if not computed and all(v=='PASS' for k,v in gates.items() if k!='presentation_differs_only') and gates.get('presentation_differs_only')=='PASS':
            errors.append(p.get('id','?')+':unexplained_rejection')
    bg=data.get('non_model_background',{})
    if 'representation timing only' not in bg.get('issue_752',''): errors.append('752_scope')
    if 'not frontier-model evidence' not in bg.get('issue_808',''): errors.append('808_scope')
    search=data.get('search_scope_findings',{})
    if search.get('packed_temporal_sheet_use')!='FOUND_MANY': errors.append('sheet_use_not_pinned')
    if search.get('matched_separate_frames_arm') not in ('NOT_FOUND_IN_SEARCH_SCOPE','FOUND'): errors.append('search_sep')
    if errors: decision='FAIL_INTEGRITY'
    elif admissible: decision='PASS_RETAINED_TEMPORAL_SHEET_BENEFIT_IDENTIFIABLE_SCOPED'
    else: decision='PASS_RETAINED_TEMPORAL_SHEET_BENEFIT_NOT_IDENTIFIABLE_SCOPED'
    return {'decision':decision,'pass':not errors,'errors':errors,'metrics':{'families':len(fam),'candidate_pairs':len(pairs),'admissible_pairs':len(admissible),'admissible_ids':admissible}}

def controls(data):
    tests={}
    q=copy.deepcopy(data); q['families']=q['families'][:2]; tests['family_count']=evaluate(q)['decision']=='FAIL_INTEGRITY'
    q=copy.deepcopy(data); q['candidate_pairs'][0]['admissible']=True; tests['false_admissible_label']=evaluate(q)['decision']=='FAIL_INTEGRITY'
    q=copy.deepcopy(data); del q['candidate_pairs'][0]['gates']['same_model']; tests['gate_shape']=evaluate(q)['decision']=='FAIL_INTEGRITY'
    q=copy.deepcopy(data); q['families'][0]['presentation']='separate_frames'; tests['presentation_source']=evaluate(q)['decision']=='FAIL_INTEGRITY'
    q=copy.deepcopy(data); q['non_model_background']['issue_808']='HOLD_NO_PREDICTION_GAIN'; tests['background_scope']=evaluate(q)['decision']=='FAIL_INTEGRITY'
    return tests

data=json.loads(P.read_text())
out=evaluate(data); out['corruption_controls']=controls(data); out['controls_pass']=all(out['corruption_controls'].values()); out['pass']=out['pass'] and out['controls_pass']
if not out['controls_pass']: out['decision']='FAIL_INTEGRITY'
path=pathlib.Path(__file__).with_name('AUDIT.json'); path.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2,sort_keys=True))
sys.exit(0 if out['pass'] else 3)
