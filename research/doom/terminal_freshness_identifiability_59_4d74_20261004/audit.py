import copy,hashlib,importlib.util,json,pathlib,sys
sys.dont_write_bytecode=True
HERE=pathlib.Path(__file__).resolve().parent
SOURCE=HERE/'source/independent_progress_clock_v2.py'
SOURCE_SHA='3d906a7043f0d674bac3bd137952adeac11c77c9339bc38ef6ca37b05e0d1613'
PLAN_SHA='fd880f066d5762f24ae65899a0122f062ccb871997c03d54e9c1074929f2b730'
def need(value,message):
 if not value: raise ValueError(message)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
need(sha(SOURCE)==SOURCE_SHA,'pinned ProgressClock source mismatch')
need(sha(HERE/'PLAN.md')==PLAN_SHA,'frozen plan mismatch')
spec=importlib.util.spec_from_file_location('clock_v2_audit',SOURCE)
clock=importlib.util.module_from_spec(spec); sys.modules[spec.name]=clock; spec.loader.exec_module(clock)
raw=json.loads((HERE/'RAW.json').read_text())
def verify(data):
 need(data['status']=='captured' and data['source_commit']=='5489741c1efa2d25bedf5aa64e60a68fb2f74e3c','run identity mismatch')
 need(data['source_sha256']==SOURCE_SHA and data['plan_sha256']==PLAN_SHA,'raw source pin mismatch')
 need(data['external_engine_or_input'] is False,'unexpected external engine/input')
 expected_fields=['sample_ns','kill_count','death_count','episode_finished','player_dead','map_exit']
 need(data['api_fields']==expected_fields,'ProgressSample API fields changed')
 need('producer_epoch' not in data['serialized_sample_fields'] and 'update_epoch' not in data['serialized_sample_fields'],'epoch unexpectedly serialized')
 need([x['case'] for x in data['traces']]==['positive_kill','terminal_no_exit'],'case inventory mismatch')
 outcomes={}
 for trace in data['traces']:
  fresh=trace['fresh']; stale=trace['stale']
  need(fresh['provenance']['producer_epoch']=='current-episode-42','fresh source label mismatch')
  need(stale['provenance']['producer_epoch']=='previous-episode-41','stale source label mismatch')
  need(fresh['provenance']['update_epoch']==stale['provenance']['update_epoch']==74,'same numeric producer tic expected')
  need(fresh['events']==stale['events'],'consumer distinguished provenance histories')
  need(len(fresh['events'])==1,'expected one event per scenario')
  outcomes[trace['case']]=fresh['events'][0]['kind']
 need(outcomes=={'positive_kill':'KILL_COUNT_INCREASE','terminal_no_exit':'EPISODE_FINISHED_NO_EXIT'},'event outcome mismatch')
 return outcomes
outcomes=verify(raw)
tampered=copy.deepcopy(raw); tampered['traces'][0]['stale']['events'][0]['observed_ns']+=1
try: verify(tampered)
except (KeyError,TypeError,ValueError): tamper_rejected=True
else: raise ValueError('auditor accepted a provenance-output mutation')
report={'pass':True,'disposition':'PASS_SOURCE_EPOCH_REQUIRED_UNDER_STALE_RETURN_MODEL','source_sha256':SOURCE_SHA,'provenance_cases':2,'event_outcomes':outcomes,'fresh_and_stale_event_outputs_identical':True,'producer_epoch_or_update_epoch_in_sample_api':False,'audit_tamper_control_rejected':tamper_rejected,'limitations':['upstream stale return is a counterfactual possibility, not observed ViZDoom behavior','no empirical terminal onset or engine freshness acknowledgment','no game, GUI, model, input, allocation, or controller effect tested']}
(HERE/'AUDIT.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n'); print(json.dumps(report,indent=2,sort_keys=True))
