import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent
main=json.loads((root/'RUN-MAIN.json').read_text());cand=json.loads((root/'RUN-PR7330.json').read_text())
expected={'main_caller':'8517d130d7336b27e6ddfc0ee06629d2b1183070cf845c3ef4ada8adc3cd79ca','candidate_caller':'983d22edfd1232a42765804688e990249887723f849220fae6407f58a04dca8c','compiled':'d22160919ad7fc00d8a1c6e1da3240a316b024738362d714fafa68b772005014'}
assert main['source_sha256']=={'caller':expected['main_caller'],'compiled':expected['compiled']}
assert cand['source_sha256']=={'caller':expected['candidate_caller'],'compiled':expected['compiled']}
for x in (main,cand):
 local=x['cases']['local_repair']['result'];lc=x['cases']['local_repair']
 assert (local['outcome'],local['repair_path'])==('TASK_SUCCEEDED','local')
 assert local['accounting']['attempted_calls']==0 and lc['model_results']==[]
 assert lc['compiled'][0]['outcome']=='TASK_SUCCEEDED' and lc['compiled'][0]['completed_transitions']==2
 model=x['cases']['model_repair']['result'];mc=x['cases']['model_repair']
 assert (model['outcome'],model['repair_path'])==('TASK_SUCCEEDED','model_reacquisition')
 assert model['accounting']['attempted_calls']==1 and model['accounting']['completed_calls']==1
 assert model['accounting']['usage_totals']=={'input_tokens':70,'cached_input_tokens':20,'cache_write_input_tokens':0,'output_tokens':9,'reasoning_output_tokens':2}
 assert mc['compiled'][0]['outcome']=='TASK_SUCCEEDED' and mc['compiled'][0]['completed_transitions']==2
 assert model['repair_trace']==[{'stage':'reuse_revalidate','status':'missing'},{'stage':'model_reacquisition','status':'target_reference'},{'stage':'post_model_revalidate','status':'current_patch_match'}]
 abort=x['cases']['changed_after_model']['result'];ac=x['cases']['changed_after_model']
 assert (abort['outcome'],abort['reason'])==('SAFE_STOP','association_changed')
 assert abort['accounting']['attempted_calls']==1 and ac['compiled']==[]
 assert 'execute' not in ac['adapter_calls'] and 'verify_effect' not in ac['adapter_calls']
assert main['cases']['local_repair']['result']['outcome']==cand['cases']['local_repair']['result']['outcome']
assert main['cases']['model_repair']['result']['outcome']==cand['cases']['model_repair']['result']['outcome']
assert main['cases']['changed_after_model']['result']['reason']==cand['cases']['changed_after_model']['result']['reason']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
report={'status':'PASS_SCOPED_INVALIDATION_REPAIR_COMPOSITION','scope':'synthetic cached-target invalidation, local/model repair and post-model change through compiled runtime; no GUI, physical input, provider or efficiency claim',
 'assertions':{'local_repair_then_compiled_execution':True,'model_repair_accounted_then_revalidated_then_compiled_execution':True,'changed_post_model_evidence_stops_before_execute':True,'main_and_candidate_agree_on_gate_outcomes':True},
 'source_sha256':{'main':main['source_sha256'],'candidate':cand['source_sha256']},
 'sha256':{p.name:sha(p) for p in (root/'run.py',root/'RUN-MAIN.json',root/'RUN-PR7330.json')}}
(root/'AUDIT.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');print(json.dumps(report,sort_keys=True,indent=2))
