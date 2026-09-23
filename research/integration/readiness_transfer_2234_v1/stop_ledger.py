import hashlib,json
required=['two_held_out_application_routes','same_model_policy','independent_readiness_score','independent_input_score','independent_task_effect_score','model_calls_tokens_latency']
missing=['two_held_out_application_routes','same_model_policy','independent_task_effect_score','model_calls_tokens_latency']
record={'decision':'STOP_EVIDENCE_ACQUISITION_GAP','required':required,'missing':missing,'classifier_control_reused':False,'synthetic_pass_substituted':False,'runtime_mutation':0,'model':0,'gui':0,'input':0}
assert set(missing)<=set(required) and record['synthetic_pass_substituted'] is False
record['digest']=hashlib.sha256(json.dumps(record,sort_keys=True).encode()).hexdigest()
print(json.dumps(record,sort_keys=True))
