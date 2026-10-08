import pathlib,json,hashlib
from saved_oracle import score_saved
R=pathlib.Path('/data');O=pathlib.Path('/out');I=R/'inputs';errors=[]
def read(p):return json.loads((I/p).read_text())
for f in json.loads((R/'INPUTS.json').read_text())['files']:
 if hashlib.sha256((I/f['path']).read_bytes()).hexdigest()!=f['sha256']:errors.append('input custody '+f['path'])
def usage(j):
 u=j['usage']
 if u['inputTokens']+u['outputTokens']!=u['totalTokens'] or u['cachedInputTokens']>u['inputTokens'] or u['reasoningOutputTokens']>u['outputTokens']:errors.append('usage subset')
 return u
e=read('A01/EXECUTION.json');stages=e['sessions'][0]['model_stages'];models=[read('A01/model'+str(n)+'.public.json') for n in range(2)]
us=[usage(j) for j in models]
if [s['usage'] for s in stages]!=us:errors.append('A01 stage usage join')
a_effects=[score_saved((I/f'A01/task{n}.fods').read_bytes(),a,b) for n,(a,b) in enumerate([(13,17),(19,23)])]
if [x['pass_effect'] for x in a_effects]!=[True,False]:errors.append('original first failure not reproduced')
a=dict(model_contexts=len(models),registered_calls=sum(j['dynamic_calls'] for j in models),attempted_tasks=2,correct_tasks=sum(x['pass_effect'] for x in a_effects),wrong_tasks=1,censored_tasks=22,usage={k:sum(u[k] for u in us) for k in us[0]},full_session_wall_ns=e['sessions'][0]['ended_wall_ns']-e['sessions'][0]['started_wall_ns'],model_wall_ns=sum(s['wall_ns'] for s in stages),effects=a_effects,cleanup='UNKNOWN after external stop',disposition='FAIL_EFFECT_STOP; HOLD_COMPARISON')
g=read('G18/raw.json');m=read('G18/model.public.json');gu=usage(m);first=score_saved((I/'G18/first.fods').read_bytes(),13,41)
if not first['pass_effect'] or len(g['native_attempts'])!=1 or g['compiled_result']['outcome']!='SAFE_YIELD' or g['compiled_result']['completed_transitions']!=1:errors.append('G18 partial prefix')
g18=dict(model_contexts=1,model_turns=m['turn_start_requests'],registered_calls=m['dynamic_calls'],native_programs=len(g['native_attempts']),saved_prefix_tasks=1,censored_native_tasks=1,usage=gu,model_context_wall_ns=m['ended_wall_ns']-m['started_wall_ns'],graph_wall_ns=g['compiled_result']['elapsed_ns'],effect=first,outcome=g['compiled_result']['outcome'],reason=g['compiled_result']['reason'],report_repair='separate retained semantic audit, not recomputed by numerical reader',disposition='PARTIAL_EFFECT; HOLD_TASK_AND_EFFICIENCY')
c=read('G22/raw.json');p=read('G22/PLAN.json');ce=read('G22/EXECUTION.json');cs=[score_saved((I/f'G22/task{n+1}.fods').read_bytes(),t['a'],t['b']) for n,t in enumerate(p['tasks'])]
if len(c['tasks'])!=6 or not all(x['pass_effect'] for x in cs):errors.append('G22 effects')
if any(any(o['op'].startswith('pointer') for o in t['program']['ops']) for t in c['tasks']):errors.append('G22 pointer')
c22=dict(native_tasks=len(cs),correct_tasks=sum(x['pass_effect'] for x in cs),model_calls=ce['rows'][0]['model_calls'],model_tokens=0,method_construction_tokens=None,producer_host_wall_ns=ce['rows'][0]['ended_wall_ns']-ce['rows'][0]['started_wall_ns'],relocation=c['relocation'],disposition='PASS_KNOWN_STANDARD_REFERENCE; NO_MATCHED_RATIO')
out=dict(allocation=json.loads((R/'PLAN.json').read_text())['allocation'],errors=errors,A01=a,G18=g18,G22=c22,integrated_decision='HOLD_CORRECTNESS_AND_MATCHED_TOTAL_COST',benefit_ratio=None,break_even=None,total_resource_or_money=None,reason='Original planned direct/compiled comparison stopped before compiled arm. G18 partial report repair did not complete second native task. G22 stronger standard method has different source/task/model assistance and uncharged construction; cross-allocation ratios are invalid.',scope='No native/model replay or original regrade; exact retained numerical/effect accounting only. Full ROADMAP remains active.')
with (O/'DECISION.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(errors=errors,A01=a['usage'],G18=gu,G22_correct=c22['correct_tasks'],decision=out['integrated_decision'])));raise SystemExit(bool(errors))


