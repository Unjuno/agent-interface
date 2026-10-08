import copy, hashlib, json, pathlib, sys
D=pathlib.Path(__file__).parent
P=json.loads((D/'PREREGISTRATION.json').read_text())
EXPECTED_BLOBS={
'chromium_protocol':'e8e5ee9e3abb66cb7673ac90ec9074820a16cac9',
'chromium_plan':'ff0de7c4a0d6cc57d145d460f019f72d6967ffec',
'mindustry_lifecycle':'85da96306ab544a6e2f9a340b0a2af09c4701c3c',
'mindustry_reset_contract':'ae4d6143370117c2c3655e61ed62a570060d55b2',
'mindustry_fixture_protocol':'6b6b4c759ea097fadca9768d4938ac5ecf201a94'}
def validate(p):
    e=[]
    if p.get('arm_order')!=['plain','ephemeral','persistent']: e.append('arm_order')
    if p.get('tasks')!=['A1','A2','A3','B1','B2','B3']: e.append('tasks')
    if p.get('layouts')!=['A','A','A','B','B','B']: e.append('layouts')
    if p.get('routes')!={'plain':['cold']*6,'ephemeral':['cold']*6,'persistent':['cold','reuse','reuse','repair','reuse','reuse']}: e.append('route_schedule')
    if p.get('task_model_calls')!={'plain':[1]*6,'ephemeral':[1]*6,'persistent':[1,0,0,1,0,0]}: e.append('model_call_schedule')
    if p.get('preflight')!={'calls_per_arm':1,'images_per_call':0,'count_input_tokens':True,'count_planner_generation':True}: e.append('preflight_accounting')
    tc=p.get('task_contract',{})
    if not tc.get('score_before_reset') or tc.get('failed_score_allows_reset') or tc.get('failed_score_allows_next_task'): e.append('score_reset_barrier')
    if tc.get('geometry_mutations')!=[{'after':'A3.reset_witness','before':'B1.task_ready','from':'A','to':'B'}]: e.append('geometry_boundary')
    if set(tc.get('controller_visible_fields',[]))!={'task_id','task','layout','benchmark_epoch'}: e.append('controller_projection')
    if not {'engine_tiles','copper_oracle','score','checkpoint_private','reset_private'}<=set(tc.get('forbidden_controller_fields',[])): e.append('oracle_private_fields')
    if p.get('persistent_repair')!={'task':'B1','old_reference_must_refuse':True,'old_reference_consequential_admissions':0,'repair_calls':1,'requires_fresh_current_evidence':True,'reuse_after_repair':['B2','B3']}: e.append('persistent_repair')
    want_dr={'all_arms_correct':True,'persistent_old_target_admissions':0,'persistent_repair_succeeds':True,'persistent_final_input_tokens_lt_both_controls':True,'persistent_final_planner_generations_lt_both_controls':True,'token_break_even_task_lte':4,'wall_time_faster_than_both':'descriptive_only'}
    if p.get('decision_rule')!=want_dr: e.append('decision_rule_drift')
    lg=p.get('live_start_gate',{})
    if lg.get('required_fresh_successor_of')!=908 or lg.get('required_disposition')!='PASS_MINDUSTRY_MATERIALIZED_LIVE_SMOKE_SCOPED': e.append('live_smoke_gate')
    if lg.get('jar')!={'name':'Mindustry.jar','bytes':87022576,'sha256':'7f210295dfffb4c17b582b27bab41f4dde83f557f00f0877572fdac943f40539'}: e.append('jar_identity')
    if lg.get('save')!={'name':'canonical.msav','sha256':'8fff67b0c130ee59a3838c92754b73225a506902bd4838dcc3f1fb5be286cbed'}: e.append('save_identity')
    if lg.get('consumed_hold_not_reusable') is not True or lg.get('live_allocation_authorized_by_this_prereg') is not False: e.append('allocation_authority')
    deps=p.get('dependencies',{})
    if set(deps)!=set(EXPECTED_BLOBS): e.append('dependency_set')
    else:
        for k,v in EXPECTED_BLOBS.items():
            if deps[k].get('git_blob')!=v: e.append('dependency:'+k)
    return e
errors=validate(P)
controls={}
mutations={
 'persistent_call_schedule': lambda q:q['task_model_calls'].__setitem__('persistent',[1,0,0,0,0,0]),
 'reset_before_score': lambda q:q['task_contract'].__setitem__('score_before_reset',False),
 'oracle_leak': lambda q:q['task_contract']['controller_visible_fields'].append('score'),
 'relaxed_token_criterion': lambda q:q['decision_rule'].__setitem__('persistent_final_input_tokens_lt_both_controls',False),
 'removed_live_smoke_gate': lambda q:q['live_start_gate'].__setitem__('required_disposition','NONE')}
for name,fn in mutations.items():
    q=copy.deepcopy(P); fn(q); controls[name]=len(validate(q))>0
out={'schema':'mindustry_three_arm_economics_prereg_audit_v1','passed':not errors and all(controls.values()),'errors':errors,'corruption_controls':controls,'prereg_sha256':hashlib.sha256((D/'PREREGISTRATION.json').read_bytes()).hexdigest(),'formal_live_invocations':0,'design_audit_invocations':1}
(D/'AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,sort_keys=True))
sys.exit(0 if out['passed'] else 1)
