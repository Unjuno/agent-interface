import hashlib, json
from pathlib import Path
root=Path(__file__).resolve().parent
main=json.loads((root/'RUN-MAIN.json').read_text()); cand=json.loads((root/'RUN-PR7330.json').read_text())
expected={'main_caller':'8517d130d7336b27e6ddfc0ee06629d2b1183070cf845c3ef4ada8adc3cd79ca','candidate_caller':'e9be73955d849a8d627450752a4b6b97a410cdd08e9424746d954e23015a654d','compiled':'d22160919ad7fc00d8a1c6e1da3240a316b024738362d714fafa68b772005014'}
assert main['source_sha256']=={'caller':expected['main_caller'],'compiled':expected['compiled']}
assert cand['source_sha256']=={'caller':expected['candidate_caller'],'compiled':expected['compiled']}
for label,x in [('main',main),('candidate',cand)]:
 p=x['cases']['positive']['result']; pc=x['cases']['positive']['compiled'][0]
 assert (p['outcome'],p['task_effect'],p['delivery'])==('TASK_SUCCEEDED','succeeded','confirmed')
 assert pc['outcome']=='TASK_SUCCEEDED' and pc['completed_transitions']==2
 assert p['accounting']['attempted_calls']==2 and p['accounting']['completed_calls']==2
 assert p['accounting']['usage_totals']=={'input_tokens':200,'cached_input_tokens':50,'cache_write_input_tokens':0,'output_tokens':20,'reasoning_output_tokens':6}
 assert p['accounting']['visible_images_submitted']==2 and p['accounting']['model_wait_ns']==20_000_000
 assert [a['stage'] for a in p['attempt_ledger']]==['coarse_model','anchor_model']
 stop=x['cases']['no_match']['result']
 assert (stop['outcome'],stop['reason'],stop['selected_target'])==('SAFE_STOP','no_match',None)
 assert stop['accounting']['attempted_calls']==1 and stop['accounting']['completed_calls']==1
 assert not x['cases']['no_match']['compiled'] and not x['cases']['no_match']['outer_effect_calls']
 failed=x['cases']['model_failure']['result']
 assert (failed['outcome'],failed['reason'])==('CALLER_FAILED','failed_upstream')
 assert failed['accounting']['attempted_calls']==1 and failed['accounting']['completed_calls']==0
 assert failed['accounting']['usage_totals']=={'input_tokens':None,'cached_input_tokens':None,'cache_write_input_tokens':None,'output_tokens':None,'reasoning_output_tokens':None}
 assert failed['accounting']['visible_images_submitted']==1 and failed['accounting']['model_wait_ns']==12_000_000
 assert failed['attempt_ledger'][0]['status']=='failed' and failed['attempt_ledger'][0]['call_id']=='a02-failed'
 assert failed['selected_target'] is None and not x['cases']['model_failure']['compiled']
assert main['cases']['positive']['result']['execution_progress']==cand['cases']['positive']['result']['execution_progress']
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
report={'status':'PASS_SCOPED_COLD_COMPOSITION','scope':'synthetic cold acquisition through caller v3 into compiled graph; no GUI, physical input, provider, schema endpoint or efficiency claim',
 'assertions':{'cold_positive_accounts_both_model_stages_and_executes_two_transitions':True,'no_match_stops_without_selected_target_or_execution':True,'failed_model_attempt_retains_missing_usage_image_and_wait_metadata':True,'current_main_and_candidate_agree_on_cold_cases':True},
 'source_sha256':{'main':main['source_sha256'],'candidate':cand['source_sha256']},
 'sha256':{p.name:sha(p) for p in (root/'run.py',root/'RUN-MAIN.json',root/'RUN-PR7330.json')}}
(root/'AUDIT.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');print(json.dumps(report,sort_keys=True,indent=2))
